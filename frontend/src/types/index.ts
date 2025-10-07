export interface User {
  id: number;
  username: string;
  email?: string;
  status: 'ACTIVE' | 'DISABLED' | 'LIMITED' | 'EXPIRED';
  traffic_limit_bytes?: number;
  traffic_used_bytes: number;
  traffic_limit_strategy: 'NO_RESET' | 'DAY' | 'WEEK' | 'MONTH';
  expire_at?: string;
  sub_revoked_at?: string;
  online_at?: string;
  description?: string;
  telegram_id?: number;
  hwid_device_limit?: number;
  created_at: string;
  updated_at: string;
  proxies: Proxy[];
  hwid_devices: HwidDevice[];
}

export interface Proxy {
  id: number;
  user_id: number;
  type: 'VMESS' | 'VLESS' | 'TROJAN' | 'SHADOWSOCKS';
  vmess_uuid?: string;
  vless_uuid?: string;
  vless_flow?: string;
  trojan_password?: string;
  ss_password?: string;
  ss_method?: string;
  network?: string;
  security?: string;
  sni?: string;
  alpn?: string[];
  fingerprint?: string;
  created_at: string;
}

export interface HwidDevice {
  id: number;
  hwid: string;
  device_os?: string;
  ver_os?: string;
  device_model?: string;
  first_seen_at: string;
  last_seen_at: string;
}

export interface Node {
  id: number;
  name: string;
  address: string;
  api_port: number;
  api_protocol: 'grpc' | 'rest';
  usage_ratio: number;
  traffic_limit_bytes?: number;
  traffic_used_bytes: number;
  traffic_notify_percent: number;
  is_connected: boolean;
  is_enabled: boolean;
  xray_running: boolean;
  xray_version?: string;
  node_version?: string;
  core_type?: string;
  cpu_count?: number;
  cpu_model?: string;
  total_ram_mb?: number;
  country_code?: string;
  view_position: number;
  add_host_to_inbounds: boolean;
  last_status_message?: string;
  last_connected_at?: string;
  uptime_seconds?: number;
  created_at: string;
  updated_at: string;
  // SSL certificates (only returned when creating new node)
  ssl_client_certificate?: string;
  ssl_client_key?: string;
  ssl_ca_certificate?: string;
}

export interface Inbound {
  id: number;
  tag: string;
  type: string;
  listen: string;
  port: number;
  network: string;
  security?: string;
  tls_settings?: any;
  reality_settings?: any;
  stream_settings?: any;
  sniffing_enabled: boolean;
  sniffing_dest_override?: string[];
  domain_strategy?: string;
  fallbacks?: any[];
  excluded_nodes?: string[];
  remark?: string;
  is_enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface Admin {
  id: number;
  username: string;
  is_sudo: boolean;
  is_active: boolean;
  roles: string[];
  mfa_enabled: boolean;
  telegram_id?: number;
  last_login_at?: string;
  created_at: string;
  updated_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}
