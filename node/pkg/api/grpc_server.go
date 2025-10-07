package api

import (
	"context"
	"fmt"
	"log"
	"os/exec"

	"github.com/google/uuid"
	pb "xray-panel-node/proto"
	"xray-panel-node/pkg/xray"
	"xray-panel-node/pkg/stats"
	"xray-panel-node/pkg/types"
)

type GRPCServer struct {
	pb.UnimplementedNodeServiceServer
	xrayManager *xray.Manager
	statsCollector *stats.Collector
	sessionID string
}

func NewGRPCServer(xrayMgr *xray.Manager, statsCol *stats.Collector) *GRPCServer {
	return &GRPCServer{
		xrayManager: xrayMgr,
		statsCollector: statsCol,
		sessionID: uuid.New().String(),
	}
}

func (s *GRPCServer) Start(ctx context.Context, req *pb.Backend) (*pb.BaseInfoResponse, error) {
	backend := types.Backend{
		Type:      req.Type,
		Config:    req.Config,
		KeepAlive: req.KeepAlive,
	}

	for _, u := range req.Users {
		user := types.User{
			Email:    u.Email,
			Inbounds: u.Inbounds,
		}
		for _, p := range u.Proxies {
			user.Proxies = append(user.Proxies, types.Proxy{
				VmessID:   p.VmessId,
				VlessID:   p.VlessId,
				VlessFlow: p.VlessFlow,
				TrojanPwd: p.TrojanPwd,
				SSMethod:  p.SsMethod,
				SSPass:    p.SsPass,
			})
		}
		backend.Users = append(backend.Users, user)
	}

	// Check if Xray is already running - if so, restart it
	if s.xrayManager.IsRunning() {
		log.Printf("[Start] Xray already running, restarting with new config")
		if err := s.xrayManager.Restart(backend); err != nil {
			return nil, err
		}
	} else {
		if err := s.xrayManager.Start(backend); err != nil {
			return nil, err
		}
	}

	return s.GetBaseInfo(ctx, &pb.Empty{})
}

func (s *GRPCServer) Stop(ctx context.Context, req *pb.Empty) (*pb.BaseInfoResponse, error) {
	if err := s.xrayManager.Stop(); err != nil {
		return nil, err
	}
	return s.GetBaseInfo(ctx, req)
}

func (s *GRPCServer) GetBaseInfo(ctx context.Context, req *pb.Empty) (*pb.BaseInfoResponse, error) {
	log.Printf("[GetBaseInfo] Called from %v", ctx)
	
	version, _ := s.xrayManager.GetVersion()
	isRunning := s.xrayManager.IsRunning()
	
	log.Printf("[GetBaseInfo] IsRunning returned: %v", isRunning)
	
	return &pb.BaseInfoResponse{
		Version:      "1.0.0",
		CoreType:     "xray",
		Running:      isRunning,
		XrayVersion:  version,
		Uptime:       s.xrayManager.GetUptime(),
		SessionId:    s.sessionID,
	}, nil
}

func (s *GRPCServer) GetLogs(req *pb.Empty, stream pb.NodeService_GetLogsServer) error {
	// TODO: Implement log streaming
	return fmt.Errorf("not implemented")
}

func (s *GRPCServer) SyncUser(ctx context.Context, req *pb.User) (*pb.SyncResponse, error) {
	user := types.User{
		Email:    req.Email,
		Inbounds: req.Inbounds,
	}

	for _, p := range req.Proxies {
		user.Proxies = append(user.Proxies, types.Proxy{
			VmessID:   p.VmessId,
			VlessID:   p.VlessId,
			VlessFlow: p.VlessFlow,
			TrojanPwd: p.TrojanPwd,
			SSMethod:  p.SsMethod,
			SSPass:    p.SsPass,
		})
	}

	if err := s.xrayManager.SyncUser(user); err != nil {
		return &pb.SyncResponse{
			Success: false,
			Message: err.Error(),
		}, nil
	}

	return &pb.SyncResponse{
		Success:     true,
		Message:     "User synced successfully",
		SyncedCount: 1,
	}, nil
}

func (s *GRPCServer) SyncUsers(ctx context.Context, req *pb.Users) (*pb.SyncResponse, error) {
	var users []types.User

	for _, u := range req.Users {
		user := types.User{
			Email:    u.Email,
			Inbounds: u.Inbounds,
		}
		for _, p := range u.Proxies {
			user.Proxies = append(user.Proxies, types.Proxy{
				VmessID:   p.VmessId,
				VlessID:   p.VlessId,
				VlessFlow: p.VlessFlow,
				TrojanPwd: p.TrojanPwd,
				SSMethod:  p.SsMethod,
				SSPass:    p.SsPass,
			})
		}
		users = append(users, user)
	}

	if err := s.xrayManager.SyncUsers(users); err != nil {
		return &pb.SyncResponse{
			Success: false,
			Message: err.Error(),
		}, nil
	}

	return &pb.SyncResponse{
		Success:     true,
		Message:     "Users synced successfully",
		SyncedCount: int32(len(users)),
	}, nil
}

func (s *GRPCServer) GetStats(ctx context.Context, req *pb.StatsRequest) (*pb.StatsResponse, error) {
	// req.Reset is a protobuf method, not a field. Use false for now or add a proper reset field
	stats := s.statsCollector.GetUserStats(req.Name, false)
	
	return &pb.StatsResponse{
		Name:      stats.Name,
		BytesUp:   stats.BytesUp,
		BytesDown: stats.BytesDown,
	}, nil
}

func (s *GRPCServer) GetSystemStats(ctx context.Context, req *pb.Empty) (*pb.SystemStatsResponse, error) {
	stats := s.statsCollector.GetSystemStats()
	
	return &pb.SystemStatsResponse{
		CpuCores:  int32(stats.CPUCores),
		CpuUsage:  stats.CPUUsage,
		MemTotal:  stats.MemTotal,
		MemUsed:   stats.MemUsed,
		MemUsage:  stats.MemUsage,
		NetRx:     stats.NetRx,
		NetTx:     stats.NetTx,
	}, nil
}

func (s *GRPCServer) GetOnlineUsers(ctx context.Context, req *pb.Empty) (*pb.OnlineUsersResponse, error) {
	// TODO: Implement online users tracking
	return &pb.OnlineUsersResponse{
		Users: []*pb.OnlineUser{},
	}, nil
}

func (s *GRPCServer) ExecuteCommand(ctx context.Context, req *pb.CommandRequest) (*pb.CommandResponse, error) {
	log.Printf("[ExecuteCommand] Executing: %s", req.Command)
	
	cmd := exec.Command("/bin/sh", "-c", req.Command)
	stdout, err := cmd.Output()
	
	response := &pb.CommandResponse{
		Stdout: string(stdout),
	}
	
	if err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok {
			response.ExitCode = int32(exitErr.ExitCode())
			response.Stderr = string(exitErr.Stderr)
		} else {
			response.ExitCode = 1
			response.Stderr = err.Error()
		}
	} else {
		response.ExitCode = 0
	}
	
	log.Printf("[ExecuteCommand] Exit code: %d", response.ExitCode)
	return response, nil
}
