package types

type Backend struct {
	Type      string `json:"type"`
	Config    string `json:"config"`
	Users     []User `json:"users"`
	KeepAlive bool   `json:"keep_alive"`
}

type User struct {
	Email    string   `json:"email"`
	Proxies  []Proxy  `json:"proxies"`
	Inbounds []string `json:"inbounds"`
}

type Proxy struct {
	VmessID    string `json:"vmess_id,omitempty"`
	VlessID    string `json:"vless_id,omitempty"`
	VlessFlow  string `json:"vless_flow,omitempty"`
	TrojanPwd  string `json:"trojan_pwd,omitempty"`
	SSMethod   string `json:"ss_method,omitempty"`
	SSPass     string `json:"ss_pass,omitempty"`
}

type BaseInfo struct {
	Version      string `json:"version"`
	CoreType     string `json:"core_type"`
	Running      bool   `json:"running"`
	XrayVersion  string `json:"xray_version,omitempty"`
	Uptime       int64  `json:"uptime"`
	SessionID    string `json:"session_id"`
}

type SystemStats struct {
	CPUCores  int     `json:"cpu_cores"`
	CPUUsage  float64 `json:"cpu_usage"`
	MemTotal  int64   `json:"mem_total"`
	MemUsed   int64   `json:"mem_used"`
	MemUsage  float64 `json:"mem_usage"`
	NetRx     int64   `json:"net_rx"`
	NetTx     int64   `json:"net_tx"`
}

type Stats struct {
	Name      string `json:"name"`
	BytesUp   int64  `json:"bytes_up"`
	BytesDown int64  `json:"bytes_down"`
}

type OnlineUser struct {
	Email       string   `json:"email"`
	IPs         []string `json:"ips"`
	OnlineSince int64    `json:"online_since"`
}
