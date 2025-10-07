# Opening Ports on Remote Nodes

## For Node Administrators

After installing a node with `install-node.sh`, all required ports should already be open.

If you need to manually open ports on a node, run this command:

```bash
# On the node server (via SSH)
cd /opt/xray-panel-node
bash <(curl -s https://raw.githubusercontent.com/Kavis1/xray-panel/main/deployment/node/open-xray-ports.sh)
```

Or manually:

```bash
# Required ports for Xray protocols
PORTS=(443 7443 8388 10080 50051)

# UFW (Ubuntu/Debian)
for port in "${PORTS[@]}"; do
    sudo ufw allow $port/tcp
done

# Or iptables (CentOS/RHEL)
for port in "${PORTS[@]}"; do
    sudo iptables -I INPUT -p tcp --dport $port -j ACCEPT
done
sudo service iptables save
```

## Verification

Check if ports are open:

```bash
ss -tlnp | grep -E ':(443|7443|8388|10080|50051)'
```

Test from panel server:

```bash
python3 /root/panel/backend/test_node_connection.py
```

## Port Usage

- **443** - VLESS Reality
- **7443** - Trojan TLS
- **8388** - Shadowsocks
- **10080** - VMess WebSocket
- **50051** - gRPC API (for panel communication)

## Automatic Port Opening

When you create a new inbound in the panel:
1. Port is automatically opened on the panel server (if local node)
2. Port opening command is sent to all remote nodes via gRPC
3. Firewall rules are updated automatically

## Troubleshooting

If ports are not accessible:

1. Check firewall status:
   ```bash
   ufw status
   # or
   iptables -L -n
   ```

2. Check if Xray is listening:
   ```bash
   ss -tlnp | grep xray
   ```

3. Check cloud provider firewall (AWS Security Groups, etc.)

4. Test connectivity:
   ```bash
   telnet <node-ip> 443
   ```
