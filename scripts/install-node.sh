#!/bin/bash

set -e

echo "========================================="
echo "  Xray Panel Node Installation Script"
echo "========================================="

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 
   exit 1
fi

# Install Xray-core
echo "Installing Xray-core..."
bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ install

# Install Go
echo "Installing Go..."
GO_VERSION="1.21.5"
wget "https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz"
rm -rf /usr/local/go
tar -C /usr/local -xzf "go${GO_VERSION}.linux-amd64.tar.gz"
rm "go${GO_VERSION}.linux-amd64.tar.gz"

export PATH=$PATH:/usr/local/go/bin

# Install node service
INSTALL_DIR="/opt/xray-panel-node"
echo "Installing node service to $INSTALL_DIR..."

mkdir -p $INSTALL_DIR
cd $INSTALL_DIR

# Copy node files (assuming they're in /tmp/node)
if [ -d "/tmp/node" ]; then
    cp -r /tmp/node/* .
fi

# Install protoc if not present
if ! command -v protoc &> /dev/null; then
    echo "Installing protoc..."
    PROTOC_VERSION="25.1"
    wget "https://github.com/protocolbuffers/protobuf/releases/download/v${PROTOC_VERSION}/protoc-${PROTOC_VERSION}-linux-x86_64.zip"
    unzip -o "protoc-${PROTOC_VERSION}-linux-x86_64.zip" -d /usr/local
    rm "protoc-${PROTOC_VERSION}-linux-x86_64.zip"
fi

# Install protoc-gen-go and protoc-gen-go-grpc
echo "Installing protoc plugins..."
go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest

export PATH=$PATH:/root/go/bin

# Compile proto files
echo "Compiling proto files..."
protoc --go_out=. --go_opt=paths=source_relative \
    --go-grpc_out=. --go-grpc_opt=paths=source_relative \
    proto/node.proto

# Build node service
echo "Building node service..."
go mod download
go build -o xray-panel-node cmd/main.go

# Create environment file
if [ ! -f .env ]; then
    cp .env.example .env
    
    # Generate random API key
    API_KEY=$(openssl rand -hex 32)
    sed -i "s/your-secure-api-key-here/$API_KEY/" .env
    
    echo "Environment file created at .env"
    echo "API Key: $API_KEY"
    echo "Please save this key - you'll need it to add this node to the panel"
fi

# Create systemd service
cat > /etc/systemd/system/xray-panel-node.service << EOF
[Unit]
Description=Xray Panel Node Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
EnvironmentFile=$INSTALL_DIR/.env
ExecStart=$INSTALL_DIR/node
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
systemctl daemon-reload

echo ""
echo "========================================="
echo "  Node Installation completed!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Review configuration: $INSTALL_DIR/.env"
echo "2. Start node service:"
echo "   systemctl enable --now xray-panel-node"
echo "3. Add this node to your panel using the API key above"
echo ""
