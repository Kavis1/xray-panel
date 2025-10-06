package stats

import (
	"runtime"
	"sync"

	"xray-panel-node/pkg/types"
)

type Collector struct {
	mu sync.RWMutex
	userStats map[string]*types.Stats
}

func NewCollector() *Collector {
	return &Collector{
		userStats: make(map[string]*types.Stats),
	}
}

func (c *Collector) GetUserStats(email string, reset bool) *types.Stats {
	c.mu.Lock()
	defer c.mu.Unlock()

	stats, exists := c.userStats[email]
	if !exists {
		return &types.Stats{
			Name: email,
			BytesUp: 0,
			BytesDown: 0,
		}
	}

	result := &types.Stats{
		Name: stats.Name,
		BytesUp: stats.BytesUp,
		BytesDown: stats.BytesDown,
	}

	if reset {
		stats.BytesUp = 0
		stats.BytesDown = 0
	}

	return result
}

func (c *Collector) GetSystemStats() *types.SystemStats {
	var m runtime.MemStats
	runtime.ReadMemStats(&m)

	return &types.SystemStats{
		CPUCores: runtime.NumCPU(),
		CPUUsage: 0.0, // TODO: Implement actual CPU usage
		MemTotal: int64(m.Sys),
		MemUsed:  int64(m.Alloc),
		MemUsage: float64(m.Alloc) / float64(m.Sys) * 100,
		NetRx:    0, // TODO: Implement network stats
		NetTx:    0,
	}
}

func (c *Collector) RecordTraffic(email string, bytesUp, bytesDown int64) {
	c.mu.Lock()
	defer c.mu.Unlock()

	if _, exists := c.userStats[email]; !exists {
		c.userStats[email] = &types.Stats{Name: email}
	}

	c.userStats[email].BytesUp += bytesUp
	c.userStats[email].BytesDown += bytesDown
}
