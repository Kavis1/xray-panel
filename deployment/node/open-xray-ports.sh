#!/bin/bash
# Open required ports for Xray on node
# This script should be run on each node server

set -e

echo "=================================="
echo "Opening Xray Ports on Node"
echo "=================================="

# Common Xray ports
PORTS=(443 7443 8388 10080)

echo ""
echo "Checking firewall..."

# Check if UFW is installed and active
if command -v ufw &> /dev/null; then
    echo "UFW detected, opening ports..."
    
    for port in "${PORTS[@]}"; do
        echo "  Opening port $port/tcp..."
        ufw allow $port/tcp >/dev/null 2>&1 || true
    done
    
    # Also open gRPC port
    echo "  Opening gRPC port 50051/tcp..."
    ufw allow 50051/tcp >/dev/null 2>&1 || true
    
    echo "✓ UFW rules configured"
    
elif command -v iptables &> /dev/null; then
    echo "iptables detected, opening ports..."
    
    for port in "${PORTS[@]}"; do
        echo "  Opening port $port/tcp..."
        iptables -I INPUT -p tcp --dport $port -j ACCEPT >/dev/null 2>&1 || true
    done
    
    # Also open gRPC port
    echo "  Opening gRPC port 50051/tcp..."
    iptables -I INPUT -p tcp --dport 50051 -j ACCEPT >/dev/null 2>&1 || true
    
    # Try to save iptables rules
    if command -v netfilter-persistent &> /dev/null; then
        netfilter-persistent save >/dev/null 2>&1 || true
    elif command -v iptables-save &> /dev/null; then
        iptables-save > /etc/iptables/rules.v4 2>/dev/null || true
    fi
    
    echo "✓ iptables rules configured"
else
    echo "⚠ No firewall detected (UFW/iptables)"
    echo "  Ports may already be open or you're using a different firewall"
fi

echo ""
echo "=================================="
echo "Port Opening Complete"
echo "=================================="
echo ""
echo "Opened ports:"
for port in "${PORTS[@]}"; do
    echo "  - $port/tcp"
done
echo "  - 50051/tcp (gRPC)"
echo ""
echo "Verify with: ss -tlnp | grep -E ':(443|7443|8388|10080|50051)'"
