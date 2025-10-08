package api

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/exec"
	"sync"
	"time"

	"xray-panel-node/pkg/xray"
)

type RestServer struct {
	xrayManager *xray.Manager
	sessionID   string
	mu          sync.RWMutex
}

type StartRequest struct {
	SessionID string `json:"session_id"`
	Config    string `json:"config"`
}

type RestartRequest struct {
	SessionID string `json:"session_id"`
	Config    string `json:"config"`
}

type Response struct {
	Started      bool   `json:"started,omitempty"`
	SessionID    string `json:"session_id,omitempty"`
	CoreVersion  string `json:"core_version,omitempty"`
	Message      string `json:"message,omitempty"`
	Detail       string `json:"detail,omitempty"`
}

func NewRestServer(xrayMgr *xray.Manager) *RestServer {
	return &RestServer{
		xrayManager: xrayMgr,
	}
}

func (s *RestServer) handleConnect(w http.ResponseWriter, r *http.Request) {
	s.mu.Lock()
	s.sessionID = generateSessionID()
	s.mu.Unlock()

	log.Printf("[REST] Client connected, session: %s", s.sessionID)

	json.NewEncoder(w).Encode(Response{
		SessionID: s.sessionID,
	})
}

func (s *RestServer) handleDisconnect(w http.ResponseWriter, r *http.Request) {
	s.mu.Lock()
	s.sessionID = ""
	s.mu.Unlock()

	log.Printf("[REST] Client disconnected")

	json.NewEncoder(w).Encode(Response{
		Message: "Disconnected",
	})
}

func (s *RestServer) handlePing(w http.ResponseWriter, r *http.Request) {
	json.NewEncoder(w).Encode(Response{
		Message: "pong",
	})
}

func (s *RestServer) handleRoot(w http.ResponseWriter, r *http.Request) {
	version, _ := s.xrayManager.GetVersion()
	started := s.xrayManager.IsRunning()

	json.NewEncoder(w).Encode(Response{
		Started:     started,
		CoreVersion: version,
	})
}

func (s *RestServer) handleStart(w http.ResponseWriter, r *http.Request) {
	var req StartRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	log.Printf("[REST] Start request received, config length: %d", len(req.Config))

	// Check if already running - if so, restart instead
	if s.xrayManager.IsRunning() {
		log.Printf("[REST] Xray already running, restarting instead")
		s.handleRestart(w, r)
		return
	}

	// Write config to file
	configFile := "/opt/xray-panel-node/xray_config.json"
	if err := os.WriteFile(configFile, []byte(req.Config), 0644); err != nil {
		log.Printf("[REST] Failed to write config: %v", err)
		http.Error(w, fmt.Sprintf("Failed to write config: %v", err), http.StatusInternalServerError)
		return
	}
	
	log.Printf("[REST] Config written to %s", configFile)
	
	// Sync to disk
	exec.Command("/usr/bin/sync").Run()
	time.Sleep(200 * time.Millisecond)

	// Start xray-node service via systemd
	cmd := exec.Command("/usr/bin/systemctl", "start", "xray-node")
	if err := cmd.Run(); err != nil {
		log.Printf("[REST] Failed to start xray-node: %v", err)
		http.Error(w, fmt.Sprintf("Failed to start xray: %v", err), http.StatusInternalServerError)
		return
	}

	log.Printf("[REST] xray-node service started")
	
	// Wait for xray to start
	time.Sleep(2 * time.Second)

	// Get version
	version, _ := s.xrayManager.GetVersion()

	json.NewEncoder(w).Encode(Response{
		Started:     true,
		CoreVersion: version,
		Message:     "Xray started successfully",
	})
}

func (s *RestServer) handleStop(w http.ResponseWriter, r *http.Request) {
	log.Printf("[REST] Stop request received")

	if err := s.xrayManager.Stop(); err != nil {
		log.Printf("[REST] Stop failed: %v", err)
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	log.Printf("[REST] Xray stopped successfully")

	json.NewEncoder(w).Encode(Response{
		Started: false,
		Message: "Xray stopped",
	})
}

func (s *RestServer) handleRestart(w http.ResponseWriter, r *http.Request) {
	var req RestartRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	log.Printf("[REST] Restart request received, config length: %d", len(req.Config))

	// Write config to file
	configFile := "/opt/xray-panel-node/xray_config.json"
	if err := os.WriteFile(configFile, []byte(req.Config), 0644); err != nil {
		log.Printf("[REST] Failed to write config: %v", err)
		http.Error(w, fmt.Sprintf("Failed to write config: %v", err), http.StatusInternalServerError)
		return
	}
	
	log.Printf("[REST] Config written to %s", configFile)
	
	// Sync to disk
	exec.Command("/usr/bin/sync").Run()
	time.Sleep(200 * time.Millisecond)

	// Restart xray-node service via systemd
	cmd := exec.Command("/usr/bin/systemctl", "restart", "xray-node")
	if err := cmd.Run(); err != nil {
		log.Printf("[REST] Failed to restart xray-node: %v", err)
		http.Error(w, fmt.Sprintf("Failed to restart xray: %v", err), http.StatusInternalServerError)
		return
	}

	log.Printf("[REST] xray-node service restarted")
	
	// Wait for xray to start
	time.Sleep(2 * time.Second)

	// Get version
	version, _ := s.xrayManager.GetVersion()

	json.NewEncoder(w).Encode(Response{
		Started:     true,
		CoreVersion: version,
		Message:     "Xray restarted successfully",
	})
}

func (s *RestServer) Start(port int) error {
	mux := http.NewServeMux()

	mux.HandleFunc("/", s.handleRoot)
	mux.HandleFunc("/connect", s.handleConnect)
	mux.HandleFunc("/disconnect", s.handleDisconnect)
	mux.HandleFunc("/ping", s.handlePing)
	mux.HandleFunc("/start", s.handleStart)
	mux.HandleFunc("/stop", s.handleStop)
	mux.HandleFunc("/restart", s.handleRestart)

	addr := fmt.Sprintf(":%d", port)
	log.Printf("[REST] Starting REST API server on %s", addr)

	return http.ListenAndServe(addr, mux)
}

func generateSessionID() string {
	// Simple session ID generation
	return fmt.Sprintf("session-%d", time.Now().Unix())
}
