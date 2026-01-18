# 🤖 SOL-SWARM Elite - Solana Memecoin Research Lab

**Elite AI-powered trading system for Solana memecoin research, backtesting, and sniping.**

⚠️ **RESEARCH/EDUCATIONAL USE ONLY** - 90%+ rug probability, NFA/DYOR

## Features

✨ **Multi-Agent Swarm Intelligence**
- Scout Agent: Token discovery + rug pull detection
- Sentiment Agent: Multi-source sentiment analysis
- Arbiter Agent: AI-powered trading decisions
- Sniper Agent: Execution with Jito bundle simulation
- Sell Agent: Position management & exit logic

📊 **Advanced Dashboard**
- Real-time PnL tracking
- Monte Carlo probability analysis
- Win rate analytics
- Agent activity logs

🛡️ **Safety First**
- Paper trading default (zero real funds)
- Hardcoded risk warnings
- RugCheck honeypot detection
- Mint/freeze authority checking

🚀 **Production Ready**
- Docker deployment
- GitHub Actions CI/CD
- Async/await architecture
- LangGraph agent orchestration

## Quick Start

```bash
# Clone
git clone https://github.com/kozzlost/sol-swarm-elite
cd sol-swarm-elite

# Setup
cp .env.example .env
pip install -r requirements.txt

# Run
streamlit run main.py
```

Visit: `http://localhost:8501`

## Strategies

- 🚀 Momentum
- 🧠 GMGN AI
- 📈 Axiom Migration  
- 🐋 Whale Copy
- ⚡ Nova Jito
- 🎯 Pump Graduate

## Configuration

Edit `.env`:
```
MAINNET_ENABLED=false          # Paper trading by default
ACTIVE_STRATEGY=MOMENTUM
MIN_SENTIMENT_SCORE=2.0
MAX_HONEYPOT_SCORE=0.3
```

## Architecture

```
sol-swarm-elite/
├── src/
│   ├── agents/           # Scout, Sentiment, Arbiter, Sniper, Sell
│   ├── services/         # DexScreener, RugCheck, X API
│   ├── strategies/       # Trading strategy implementations
│   ├── types.py          # Data structures
│   └── constants.py      # Config & thresholds
├── dashboard/            # Streamlit UI
├── tests/                # Unit & integration tests
├── .github/workflows/    # CI/CD automation
├── main.py               # Entry point
├── Dockerfile            # Production deployment
└── requirements.txt      # Dependencies
```

## API Integrations

**Free Tier Compatible:**
- DexScreener (token discovery)
- RugCheck (security vetting)
- X API v2 (sentiment)
- Solscan (whale tracking)

Optional premium:
- Cielo (smart money)
- LunarCrush (galaxy scores)

## Mainnet Trading

⚠️ **EXTREMELY DANGEROUS** - Requires explicit setup:

1. Set `MAINNET_ENABLED=true` in `.env`
2. Add Phantom wallet private key (base58)
3. Confirm you understand 90%+ loss risk
4. Start with $1-5 ONLY
5. Test extensively first

```env
MAINNET_ENABLED=true
SOLANA_PRIVATE_KEY=your_base58_key_here
```

## Risk Management

- 🛑 Max drawdown: 15% (auto pause)
- 📊 Position sizing: 0.01-0.05 SOL
- 💼 Max positions: 3 concurrent
- ⏱️ Position timeout: 30 minutes

## Testing

```bash
# Unit tests
pytest tests/ -v

# Type checking
mypy src --ignore-missing-imports

# Lint
ruff check .
```

## Docker Deployment

```bash
# Build
docker build -t sol-swarm .

# Run
docker run -p 8501:8501 -e MAINNET_ENABLED=false sol-swarm

# Or with compose
docker-compose up
```

## Contributing

Please ensure:
- ✅ All agents function correctly
- ✅ Risk warnings in place
- ✅ Tests pass (pytest)
- ✅ Type checking passes (mypy)
- ✅ Code formatted (black)

## Disclaimer

THIS SOFTWARE IS FOR EDUCATIONAL AND RESEARCH PURPOSES ONLY.

- ❌ NOT financial advice
- ❌ 90%+ of memecoins result in COMPLETE LOSS
- ❌ NEVER use real funds without extensive testing
- ❌ Developers NOT responsible for losses
- ⚖️ Utah/US users: Consult tax professional

See LICENSE for full terms.

## License

MIT License - See LICENSE file

---

**Made with ❤️ for the Solana community**
