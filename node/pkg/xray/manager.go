package xray

import (
	"fmt"
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
		return true
	}
	
	// Check if Xray process is actually running
	// Try with full path first
	cmd := exec.Command("/usr/bin/pidof", "xray")
	if err := cmd.Run(); err == nil {
		// Xray process found
		return true
	}
	
	// Try with pgrep as alternative
	cmd = exec.Command("/usr/bin/pgrep", "xray")
	if err := cmd.Run(); err == nil {
		return true
	}
	
	// If not found by pidof/pgrep, check systemd services
	cmd = exec.Command("/usr/bin/systemctl", "is-active", "xray-node")
	if err := cmd.Run(); err == nil {
		return true
	}
	
	// Also check xray-panel service (for compatibility)
	cmd = exec.Command("/usr/bin/systemctl", "is-active", "xray-panel")
	if err := cmd.Run(); err == nil {
		return true
	}
	
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
