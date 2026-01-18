# 🚀 SOL-SWARM Elite - Production Deployment Guide

## Docker Deployment (Recommended)

### Option 1: Docker Compose (Easiest)

```bash
# Clone repo
git clone https://github.com/kozzlost/sol-swarm-elite
cd sol-swarm-elite

# Start the system
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Option 2: Docker Direct

```bash
# Build image
docker build -t sol-swarm:latest .

# Run container
docker run -d \
  --name sol-swarm \
  -p 8501:8501 \
  -e MAINNET_ENABLED=false \
  sol-swarm:latest

# View logs
docker logs -f sol-swarm
```

## Cloud Deployment

### Heroku

```bash
# Install Heroku CLI
# https://devcenter.heroku.com/articles/heroku-cli

# Create app
heroku create sol-swarm-elite
heroku container:push web
heroku container:release web
heroku open
```

### Railway.app (Recommended for Solana)

```bash
# Sign up: https://railway.app
# Connect GitHub repo
# Deploy with one click!
```

### DigitalOcean

```bash
# Create App Platform app from Dockerfile
# Set environment variables
# Deploy!
```

## VPS Deployment (AWS EC2, Linode, etc.)

```bash
# SSH into VPS
ssh root@your_vps_ip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Clone repo
git clone https://github.com/kozzlost/sol-swarm-elite
cd sol-swarm-elite

# Run with systemd
sudo tee /etc/systemd/system/sol-swarm.service > /dev/null <<EOF
[Unit]
Description=SOL-SWARM Elite Trading System
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/sol-swarm-elite
ExecStart=/usr/bin/docker-compose up
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl enable sol-swarm
sudo systemctl start sol-swarm

# View status
sudo systemctl status sol-swarm
```

## Environment Configuration

### Paper Trading (Default)

```env
MAINNET_ENABLED=false
DEVNET_RPC_URL=https://api.devnet.solana.com
PAPER_BALANCE=25.0
```

### Mainnet Trading (⚠️ DANGEROUS)

```env
MAINNET_ENABLED=true
MAINNET_RPC_URL=https://api.mainnet-beta.solana.com
# Or premium RPC:
HELIUS_RPC_URL=https://mainnet.helius-rpc.com/?api-key=YOUR_KEY

# Wallet (⚠️ NEVER commit this!)
SOLANA_PRIVATE_KEY=your_base58_private_key_here

# API Keys
X_BEARER_TOKEN=your_x_api_token
CIELO_API_KEY=your_cielo_key
```

## Monitoring

### Logs

```bash
# Docker
docker-compose logs -f

# Systemd
journalctl -u sol-swarm -f
```

### Health Check

```bash
# Check if app is running
curl http://localhost:8501/_stcore/health

# Response should be: {"status": "ok"}
```

## Scaling

### Load Balancing

```bash
# Run multiple instances
docker-compose up --scale sol-swarm=3

# Use nginx reverse proxy
# (See nginx.conf template)
```

## Security

### Firewall Rules

```bash
# Only allow SSH and port 8501
sudo ufw default deny incoming
sudo ufw allow 22/tcp
sudo ufw allow 8501/tcp
sudo ufw enable
```

### API Key Rotation

```bash
# Update .env
# Restart container
docker-compose restart
```

## Troubleshooting

### Port Already in Use

```bash
# Change port in docker-compose.yml
# ports:
#   - "8502:8501"

docker-compose down
docker-compose up -d
```

### Memory Issues

```bash
# Increase Docker memory limit
# Docker Desktop: Preferences > Resources > Memory: 4GB+
```

### API Rate Limits

```env
# Add backoff and retry logic
DEXSCREENER_RATE_LIMIT_DELAY=1.0
RUGCHECK_RETRY_ATTEMPTS=3
```

## Backup & Recovery

```bash
# Backup Docker volumes
docker-compose exec db pg_dump solswarm > backup.sql

# Restore
cat backup.sql | docker-compose exec -T db psql solswarm
```

## Support

- 📖 Docs: https://github.com/kozzlost/sol-swarm-elite
- 🐛 Issues: https://github.com/kozzlost/sol-swarm-elite/issues
- 💬 Discussions: https://github.com/kozzlost/sol-swarm-elite/discussions

