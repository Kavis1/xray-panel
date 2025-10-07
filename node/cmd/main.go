package main

import (
	"context"
	"fmt"
	"log"
	"net"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials"

	"xray-panel-node/config"
	"xray-panel-node/pkg/api"
	"xray-panel-node/pkg/stats"
	"xray-panel-node/pkg/xray"
	pb "xray-panel-node/proto"
)

func main() {
	cfg := config.Load()

	xrayMgr := xray.NewManager(cfg)
	statsCol := stats.NewCollector()

	// Start REST API server in background
	restServer := api.NewRestServer(xrayMgr)
	go func() {
		restPort := 8080 // REST API port
		log.Printf("Starting REST API server on port %d", restPort)
		if err := restServer.Start(restPort); err != nil {
			log.Printf("REST API server error: %v", err)
		}
	}()

	// Start gRPC server (main)
	if cfg.ServiceProtocol == "grpc" {
		if err := startGRPCServer(cfg, xrayMgr, statsCol); err != nil {
			log.Fatalf("Failed to start gRPC server: %v", err)
		}
	} else {
		log.Fatalf("Unknown protocol: %s", cfg.ServiceProtocol)
	}
}

func startGRPCServer(cfg *config.Config, xrayMgr *xray.Manager, statsCol *stats.Collector) error {
	lis, err := net.Listen("tcp", fmt.Sprintf("%s:%d", cfg.NodeHost, cfg.ServicePort))
	if err != nil {
		return fmt.Errorf("failed to listen: %w", err)
	}

	var opts []grpc.ServerOption

	// Add request logging interceptor
	unaryInterceptor := func(ctx context.Context, req interface{}, info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (interface{}, error) {
		log.Printf("[gRPC] >>> Incoming: %s", info.FullMethod)
		resp, err := handler(ctx, req)
		if err != nil {
			log.Printf("[gRPC] <<< Failed: %s - %v", info.FullMethod, err)
		} else {
			log.Printf("[gRPC] <<< Success: %s", info.FullMethod)
		}
		return resp, err
	}
	opts = append(opts, grpc.UnaryInterceptor(unaryInterceptor))

	if cfg.SSLEnabled {
		creds, err := credentials.NewServerTLSFromFile(cfg.SSLCertFile, cfg.SSLKeyFile)
		if err != nil {
			return fmt.Errorf("failed to load TLS credentials: %w", err)
		}
		opts = append(opts, grpc.Creds(creds))
		log.Printf("SSL/TLS enabled")
	} else {
		log.Printf("SSL/TLS disabled (running without encryption)")
	}

	grpcServer := grpc.NewServer(opts...)
	nodeService := api.NewGRPCServer(xrayMgr, statsCol)
	
	pb.RegisterNodeServiceServer(grpcServer, nodeService)

	protocol := "gRPC"
	if cfg.SSLEnabled {
		protocol = "gRPC+TLS"
	}
	log.Printf("Node service starting on %s:%d (%s)", cfg.NodeHost, cfg.ServicePort, protocol)
	log.Printf("Waiting for requests...")
	return grpcServer.Serve(lis)
}
