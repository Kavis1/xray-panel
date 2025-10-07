package api

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"sync"
	"time"

	"xray-panel-node/pkg/types"
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

	log.Printf("[REST] Start request received")

	// Check if already running
	if s.xrayManager.IsRunning() {
		w.WriteHeader(http.StatusConflict)
		json.NewEncoder(w).Encode(Response{
			Detail: "Xray is started already",
		})
		return
	}

	backend := types.Backend{
		Type:   "xray",
		Config: req.Config,
	}

	if err := s.xrayManager.Start(backend); err != nil {
		log.Printf("[REST] Start failed: %v", err)
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	log.Printf("[REST] Xray started successfully")

	json.NewEncoder(w).Encode(Response{
		Started: true,
		Message: "Xray started",
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

	log.Printf("[REST] Restart request received")

	backend := types.Backend{
		Type:   "xray",
		Config: req.Config,
	}

	if err := s.xrayManager.Restart(backend); err != nil {
		log.Printf("[REST] Restart failed: %v", err)
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	log.Printf("[REST] Xray restarted successfully")

	json.NewEncoder(w).Encode(Response{
		Started: true,
		Message: "Xray restarted",
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
