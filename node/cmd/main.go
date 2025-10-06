package main

import (
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

	if cfg.ServiceProtocol == "grpc" {
		if err := startGRPCServer(cfg, xrayMgr, statsCol); err != nil {
			log.Fatalf("Failed to start gRPC server: %v", err)
		}
	} else {
		log.Fatalf("REST server not implemented yet")
	}
}

func startGRPCServer(cfg *config.Config, xrayMgr *xray.Manager, statsCol *stats.Collector) error {
	lis, err := net.Listen("tcp", fmt.Sprintf("%s:%d", cfg.NodeHost, cfg.ServicePort))
	if err != nil {
		return fmt.Errorf("failed to listen: %w", err)
	}

	var opts []grpc.ServerOption

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
	return grpcServer.Serve(lis)
}
