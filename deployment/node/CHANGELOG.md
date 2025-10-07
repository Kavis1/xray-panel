# Changelog - Xray Panel Node

## v2.0.0 (2025-10-07) - MAJOR UPDATE

### 🔥 Major Features
- **SSL-based Automatic Port Management**: Complete automation through SSL client certificates
- **Auto Port Opening**: Create inbound in panel → port opens on all nodes automatically
- **Auto Port Closing**: Delete inbound in panel → port closes on all nodes automatically
- **Mutual TLS Authentication**: Secure communication between panel and nodes

### ✨ New Features
- SSL certificate generation during node installation
- Interactive SSL certificate input flow in install-node.sh
- Automatic firewall management (UFW/iptables)
- CA certificate validation for secure commands
- Unique SSL certificate per node

### 🔒 Security
- All commands authenticated via SSL client certificates
- Mutual TLS (mTLS) between panel and nodes
- Commands without valid certificate are rejected
- Certificate revocation on node deletion
- CA certificate: `/opt/xray-panel/ssl/ca-cert.pem`

### 📦 Installation Changes
- **BREAKING**: install-node.sh now requires SSL certificate input
- Interactive flow: script stops and waits for certificate from panel
- SSL certificates stored in `/opt/xray-panel-node/ssl/`
- New .env variables: SSL_CERT_FILE, SSL_KEY_FILE, SSL_CA_FILE

### 🛠 Technical Changes
- Added CertificateManager service for SSL generation
- Enhanced FirewallManager with close_port methods
- Updated gRPC client with SSL authentication
- Automatic port management in inbound endpoints
- Node certificates auto-generated on node creation

### 📝 Files Changed
- `install-node.sh`: Added SSL certificate request flow
- `backend/app/services/ssl/certificate_manager.py`: NEW
- `backend/app/api/v1/endpoints/inbounds.py`: Auto port management
- `backend/app/services/node/firewall.py`: Port closing methods
- `backend/app/services/node/grpc_client.py`: SSL authentication

### 🔄 Migration from v1.x
**For existing nodes:**
1. Nodes installed with v1.x will continue to work
2. To enable SSL automation, reinstall node with v2.0.0
3. Follow new SSL certificate flow during installation
4. Old nodes can be deleted and recreated to get SSL certificates

**No automatic migration** - SSL requires fresh installation for security

### 📚 Documentation
- `SSL_SETUP_GUIDE.md`: Complete SSL setup documentation
- `TEST_SSL_AUTOMATION.md`: Testing guide for automation
- `IMPLEMENTATION_COMPLETE.md`: Implementation summary

---

## v1.1.2 (2025-10-06)

### 🐛 Bug Fixes
- Fixed Reality public key generation
- Fixed VMess WebSocket stream settings
- Fixed case-sensitive proxy type comparison
- Fixed subscription link parameters

### ✨ Features
- Added subscription tokens for security
- Added TLS/SNI/ALPN/fingerprint parameters
- Added validation: active users must have inbounds
- Added CLI tools: xraypanel-cli.sh, xraynode-cli.sh

### 🔧 Improvements
- Auto-generation of subscription tokens
- Normalized proxy types to lowercase
- Enhanced subscription link generation
- Added Reality keypair generation script

---

## v1.1.1 (2025-10-05)

### 🐛 Bug Fixes
- Fixed remote node connectivity issues
- Fixed Xray "Stopped" status despite running
- Emergency recovery after accidental .env deletion

### 🔧 Improvements
- Improved node status detection
- Better error handling in node sync
- Enhanced logging for debugging

---

## v1.1.0 (2025-10-04)

### ✨ Features
- Added deployment scripts (install.sh, install-node.sh)
- Added UPDATE_MODE for safe updates
- Git history cleanup (changed author to Kavis1)

### 🔧 Improvements
- Celery Worker/Beat configuration
- Traffic collection fixes
- Database backup before updates

---

## v1.0.0 (2025-10-03)

### 🎉 Initial Release
- Xray Panel with multi-node support
- User management
- Inbound configuration
- Traffic statistics
- Basic node monitoring
- React frontend
- FastAPI backend

---

## Version Numbering

**Format:** MAJOR.MINOR.PATCH

- **MAJOR**: Breaking changes, requires reinstallation
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

**Current:** v2.0.0 (SSL Automation - Breaking Change)
