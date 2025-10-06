#!/bin/bash

set -e

echo "========================================="
echo "  Xray Panel Installation Script"
echo "========================================="

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 
   exit 1
fi

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo "Cannot detect OS"
    exit 1
fi

echo "Detected OS: $OS"

# Install dependencies
echo "Installing dependencies..."

if [[ "$OS" == "ubuntu" ]] || [[ "$OS" == "debian" ]]; then
    apt-get update
    apt-get install -y python3 python3-pip python3-venv postgresql redis-server nginx curl wget unzip
elif [[ "$OS" == "centos" ]] || [[ "$OS" == "rhel" ]]; then
    yum install -y python3 python3-pip postgresql-server redis nginx curl wget unzip
else
    echo "Unsupported OS: $OS"
    exit 1
fi

# Install Xray-core
echo "Installing Xray-core..."
bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ install

# Create panel user
echo "Creating panel user..."
if ! id -u panel > /dev/null 2>&1; then
    useradd -m -s /bin/bash panel
fi

# Install panel
INSTALL_DIR="/opt/xray-panel"
echo "Installing panel to $INSTALL_DIR..."

mkdir -p $INSTALL_DIR
cd $INSTALL_DIR

# Clone or copy panel files (assuming current directory)
if [ -d "/tmp/panel" ]; then
    cp -r /tmp/panel/* .
fi

# Setup Python virtual environment
echo "Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt

# Setup database
echo "Setting up database..."
sudo -u postgres psql -c "CREATE USER panel WITH PASSWORD 'panel';"
sudo -u postgres psql -c "CREATE DATABASE panel OWNER panel;"

# Copy environment file
if [ ! -f backend/.env ]; then
    cp backend/.env.example backend/.env
    
    # Generate random secret key
    SECRET_KEY=$(openssl rand -hex 32)
    sed -i "s/change-this-to-random-secret-key-min-32-chars/$SECRET_KEY/" backend/.env
    
    echo "Environment file created at backend/.env"
    echo "Please review and update the configuration"
fi

# Run migrations
cd backend
alembic upgrade head
cd ..

# Create systemd services
echo "Creating systemd services..."

cat > /etc/systemd/system/xray-panel.service << EOF
[Unit]
Description=Xray Panel API
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=panel
WorkingDirectory=$INSTALL_DIR/backend
Environment="PATH=$INSTALL_DIR/venv/bin"
ExecStart=$INSTALL_DIR/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/xray-panel-worker.service << EOF
[Unit]
Description=Xray Panel Worker
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=panel
WorkingDirectory=$INSTALL_DIR/backend
Environment="PATH=$INSTALL_DIR/venv/bin"
ExecStart=$INSTALL_DIR/venv/bin/celery -A app.workers.celery worker --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Set permissions
chown -R panel:panel $INSTALL_DIR

# Reload systemd
systemctl daemon-reload

echo ""
echo "========================================="
echo "  Installation completed!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Review configuration: $INSTALL_DIR/backend/.env"
echo "2. Create admin user:"
echo "   cd $INSTALL_DIR && source venv/bin/activate"
echo "   python -m app.cli admin create --username admin --password yourpassword --sudo"
echo "3. Start services:"
echo "   systemctl enable --now xray-panel"
echo "   systemctl enable --now xray-panel-worker"
echo "4. Configure Nginx reverse proxy"
echo ""
