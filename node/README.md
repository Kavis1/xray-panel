# Xray Panel - Node Service

Lightweight node service for Xray-core management, communicating with the Control Panel via gRPC or REST.

## Features

- gRPC and REST API support
- Xray-core process management
- User synchronization
- Traffic statistics collection
- System metrics monitoring
- TLS/mTLS support

## Installation

### Requirements

- Go 1.21+
- Xray-core installed on the system

### Build

```bash
go mod download
go build -o node cmd/main.go
```

### Configuration

Create `.env` file:
```bash
cp .env.example .env
# Edit .env with your configuration
```

### Run

```bash
./node
```

Or with environment variables:
```bash
SERVICE_PORT=50051 SERVICE_PROTOCOL=grpc ./node
```

## API Endpoints (gRPC)

- `Start(Backend)` - Start Xray backend
- `Stop()` - Stop Xray backend
- `GetBaseInfo()` - Get node information
- `GetLogs()` - Stream logs
- `SyncUser(User)` - Sync single user
- `SyncUsers(Users)` - Sync all users
- `GetStats(StatsRequest)` - Get traffic stats
- `GetSystemStats()` - Get system metrics
- `GetOnlineUsers()` - Get online users

## Protocol Buffers

Generate protobuf code:
```bash
protoc --go_out=. --go-grpc_out=. proto/node.proto
```

## Docker

Build:
```bash
docker build -t xray-panel-node .
```

Run:
```bash
docker run -d \
  -e SERVICE_PORT=50051 \
  -e API_KEY=your-key \
  -p 50051:50051 \
  xray-panel-node
```
