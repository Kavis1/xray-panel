package config

import (
	"os"
	"strconv"
)

type Config struct {
	ServicePort        int
	ServiceProtocol    string // grpc or rest
	NodeHost           string
	XrayExecutablePath string
	XrayAssetsPath     string
	SSLCertFile        string // опционально
	SSLKeyFile         string // опционально
	APIKey             string
	MaxLogPerRequest   int
	SSLEnabled         bool // автоматически определяется
}

func Load() *Config {
	certFile := getEnv("SSL_CERT_FILE", "")
	keyFile := getEnv("SSL_KEY_FILE", "")
	sslEnabled := certFile != "" && keyFile != ""
	
	return &Config{
		ServicePort:        getEnvAsInt("SERVICE_PORT", 50051),
		ServiceProtocol:    getEnv("SERVICE_PROTOCOL", "grpc"),
		NodeHost:           getEnv("NODE_HOST", "0.0.0.0"),
		XrayExecutablePath: getEnv("XRAY_EXECUTABLE_PATH", "/usr/local/bin/xray"),
		XrayAssetsPath:     getEnv("XRAY_ASSETS_PATH", "/usr/local/share/xray"),
		SSLCertFile:        certFile,
		SSLKeyFile:         keyFile,
		SSLEnabled:         sslEnabled,
		APIKey:             getEnv("API_KEY", ""),
		MaxLogPerRequest:   getEnvAsInt("MAX_LOG_PER_REQUEST", 100),
	}
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func getEnvAsInt(key string, defaultValue int) int {
	if value := os.Getenv(key); value != "" {
		if intVal, err := strconv.Atoi(value); err == nil {
			return intVal
		}
	}
	return defaultValue
}
