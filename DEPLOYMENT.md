# ☁️ Cloud Deployment Guide

Deploy SOL-SWARM Elite to run 24/7 on a cloud server.

---

## Option 1: Railway (Easiest - Free Tier)

### Setup

1. **Go to Railway**: https://railway.app

2. **New Project** → **Deploy from GitHub repo**

3. **Connect**: `github.com/kozzlost/sol-swarm-elite`

4. **Add Environment Variables** in Railway dashboard:
   ```
   MAINNET_ENABLED=false
   ACTIVE_STRATEGY=momentum
   BOT_TRADING_WALLET=4NTt9GgvgaGmLsrDpVxArBjQxFH8u3ZQaiZKqofRuz6V
   INFRASTRUCTURE_WALLET=5nxrsa6212fgSYRP5jfXTb65Nx3eizPw1MfpPFdXY3Fy
   DEVELOPMENT_WALLET=B5dnSnKiy5rVA7ngR2yZ3pDSQfhjMdErdYPsVeKYMFaR
   BUILDER_WALLET=C9dZoFDTWPTbDuZ3wBvf7Zt6NF7WaskD2CerandtJSYY
   ```

5. **Deploy** - Railway auto-detects the Dockerfile

6. **Get URL** - Your dashboard will be at `https://your-app.railway.app`

### Cost
- Free tier: 500 hours/month
- Hobby: $5/month unlimited

---

## Option 2: Render (Free Tier)

### Setup

1. **Go to Render**: https://render.com

2. **New** → **Web Service**

3. **Connect GitHub**: `kozzlost/sol-swarm-elite`

4. **Settings**:
   - Environment: Docker
   - Plan: Free

5. **Environment Variables**: Same as Railway above

6. **Create Web Service**

### Cost
- Free tier: Sleeps after 15 min inactivity
- Starter: $7/month always-on

---

## Option 3: DigitalOcean Droplet (Most Control)

### Setup

```bash
# 1. Create $6/mo droplet (Ubuntu 24.04)
# 2. SSH in and run:

# Install Docker
curl -fsSL https://get.docker.com | sh

# Clone repo
git clone https://github.com/kozzlost/sol-swarm-elite
cd sol-swarm-elite

# Create .env
cp .env.example .env
nano .env  # Add your config

# Run with Docker Compose
docker compose up -d

# View logs
docker compose logs -f
```

### Cost
- Basic droplet: $6/month
- Full control over resources

---

## Option 4: VPS (Hetzner - Cheapest)

### Setup

```bash
# 1. Create CX11 server (~$4/mo) at hetzner.com
# 2. SSH in:

apt update && apt install -y docker.io docker-compose git

git clone https://github.com/kozzlost/sol-swarm-elite
cd sol-swarm-elite

cp .env.example .env
nano .env

docker-compose up -d
```

### Cost
- CX11: ~$4/month
- European data centers

---

## Environment Variables for Cloud

**Required:**
```
MAINNET_ENABLED=false
ACTIVE_STRATEGY=momentum
BOT_TRADING_WALLET=4NTt9GgvgaGmLsrDpVxArBjQxFH8u3ZQaiZKqofRuz6V
INFRASTRUCTURE_WALLET=5nxrsa6212fgSYRP5jfXTb65Nx3eizPw1MfpPFdXY3Fy
DEVELOPMENT_WALLET=B5dnSnKiy5rVA7ngR2yZ3pDSQfhjMdErdYPsVeKYMFaR
BUILDER_WALLET=C9dZoFDTWPTbDuZ3wBvf7Zt6NF7WaskD2CerandtJSYY
```

**For Mainnet (when ready):**
```
MAINNET_ENABLED=true
SOLANA_PRIVATE_KEY=<your_base58_private_key>
HELIUS_API_KEY=<your_helius_key>
```

**Optional (better data):**
```
TWITTER_BEARER_TOKEN=<your_token>
BIRDEYE_API_KEY=<your_key>
```

---

## Security Checklist

- [ ] Never commit `.env` to Git
- [ ] Use environment variables in cloud dashboard
- [ ] Enable 2FA on cloud accounts
- [ ] Use separate wallet for trading (not your main)
- [ ] Start with paper trading
- [ ] Set strict position limits

---

## Monitoring

### Check if running:
```bash
curl https://your-app.railway.app/_stcore/health
```

### View logs (Docker):
```bash
docker compose logs -f sol-swarm-elite
```

### Restart:
```bash
docker compose restart
```

---

## Recommended Setup

**For testing**: Railway free tier
**For production**: DigitalOcean $6 droplet or Hetzner $4 VPS

The swarm is lightweight - even the cheapest VPS can handle 100 agents.
