package xray

import (
	"fmt"
	"log"
	"os"
	"os/exec"
	"sync"
	"time"

	"xray-panel-node/config"
	"xray-panel-node/pkg/types"
)

type Manager struct {
	cfg         *config.Config
	cmd         *exec.Cmd
	running     bool
	startTime   time.Time
	config      string
	users       []types.User
	mu          sync.RWMutex
}

func NewManager(cfg *config.Config) *Manager {
	return &Manager{
		cfg:     cfg,
		running: false,
	}
}

func (m *Manager) Start(backend types.Backend) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if m.running {
		return fmt.Errorf("xray is already running")
	}

	configFile := "/tmp/xray_config.json"
	if err := os.WriteFile(configFile, []byte(backend.Config), 0644); err != nil {
		return fmt.Errorf("failed to write config: %w", err)
	}

	m.cmd = exec.Command(m.cfg.XrayExecutablePath, "run", "-config", configFile)
	m.cmd.Env = append(os.Environ(), fmt.Sprintf("XRAY_LOCATION_ASSET=%s", m.cfg.XrayAssetsPath))

	if err := m.cmd.Start(); err != nil {
		return fmt.Errorf("failed to start xray: %w", err)
	}

	m.running = true
	m.startTime = time.Now()
	m.config = backend.Config
	m.users = backend.Users

	return nil
}

func (m *Manager) Stop() error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if !m.running || m.cmd == nil || m.cmd.Process == nil {
		return fmt.Errorf("xray is not running")
	}

	if err := m.cmd.Process.Kill(); err != nil {
		return fmt.Errorf("failed to stop xray: %w", err)
	}

	m.running = false
	return nil
}

func (m *Manager) IsRunning() bool {
	m.mu.RLock()
	defer m.mu.RUnlock()
	
	// First check internal flag
	if m.running {
		log.Printf("[IsRunning] Internal flag: running=true")
		return true
	}
	
	// Primary check: systemd service status (most reliable for systemd-managed services)
	cmd := exec.Command("/usr/bin/systemctl", "is-active", "--quiet", "xray-node")
	if err := cmd.Run(); err == nil {
		log.Printf("[IsRunning] systemctl xray-node: SUCCESS")
		return true
	} else {
		log.Printf("[IsRunning] systemctl xray-node failed: %v", err)
	}
	
	// Fallback: check xray-panel service (for compatibility)
	cmd = exec.Command("/usr/bin/systemctl", "is-active", "--quiet", "xray-panel")
	if err := cmd.Run(); err == nil {
		log.Printf("[IsRunning] systemctl xray-panel: SUCCESS")
		return true
	} else {
		log.Printf("[IsRunning] systemctl xray-panel failed: %v", err)
	}
	
	// Alternative: check if Xray process exists
	cmd = exec.Command("/usr/bin/pidof", "xray")
	if err := cmd.Run(); err == nil {
		log.Printf("[IsRunning] pidof xray: SUCCESS")
		return true
	} else {
		log.Printf("[IsRunning] pidof xray failed: %v", err)
	}
	
	// Last resort: pgrep
	cmd = exec.Command("/usr/bin/pgrep", "-x", "xray")
	if err := cmd.Run(); err == nil {
		log.Printf("[IsRunning] pgrep xray: SUCCESS")
		return true
	} else {
		log.Printf("[IsRunning] pgrep xray failed: %v", err)
	}
	
	log.Printf("[IsRunning] All checks failed, returning false")
	return false
}

func (m *Manager) GetUptime() int64 {
	m.mu.RLock()
	defer m.mu.RUnlock()
	
	if !m.running {
		return 0
	}
	
	return int64(time.Since(m.startTime).Seconds())
}

func (m *Manager) SyncUser(user types.User) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	// If inbounds is empty, remove user
	if len(user.Inbounds) == 0 {
		for i, u := range m.users {
			if u.Email == user.Email {
				m.users = append(m.users[:i], m.users[i+1:]...)
				return nil
			}
		}
		return nil
	}

	// Update or add user
	found := false
	for i, u := range m.users {
		if u.Email == user.Email {
			m.users[i] = user
			found = true
			break
		}
	}

	if !found {
		m.users = append(m.users, user)
	}

	// TODO: Apply changes to running Xray instance via API
	return nil
}

func (m *Manager) SyncUsers(users []types.User) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	m.users = users
	// TODO: Apply full replacement to running Xray instance
	return nil
}

func (m *Manager) GetVersion() (string, error) {
	cmd := exec.Command(m.cfg.XrayExecutablePath, "version")
	output, err := cmd.Output()
	if err != nil {
		return "", err
	}
	return string(output), nil
}
