# 🤖 SOL-SWARM Elite - AI Trading Swarm

**Elite AI-powered trading system for Solana memecoin research with $AGENT token-funded operations.**

⚠️ **RESEARCH/EDUCATIONAL USE ONLY** - 90%+ rug probability, NFA/DYOR

## 💰 $AGENT Token - The Flywheel

The $AGENT token powers the entire swarm ecosystem through a self-sustaining fee model:

```
$AGENT Trading Volume → Transaction Fees (2%)
                              ↓
        ┌─────────────────────────────────────────┐
        │  25% → Bot Trading Treasury             │
        │  25% → Infrastructure (AI/servers)      │
        │  25% → Development Fund                 │
        │  25% → Builder Income                   │
        └─────────────────────────────────────────┘
                              ↓
        More Capital → Better Agents → More Users → More Volume
                              ↓
                         FLYWHEEL 🔄
```

**The more $AGENT is traded, the more fees fund the bots, which generate better returns, attracting more users.**

## ✨ Features

### Multi-Agent Swarm (Up to 100 Agents)
- **Scout Agent**: Token discovery + rug pull detection
- **Sentiment Agent**: Multi-source sentiment analysis
- **Arbiter Agent**: AI-powered trading decisions
- **Sniper Agent**: Jito bundle execution
- **Sell Agent**: Position management & exits
- **Treasury Agent**: Fee distribution & capital allocation

### Trading Strategies
- 🚀 Momentum
- 🧠 GMGN AI
- 📈 Axiom Migration
- 🐋 Whale Copy
- ⚡ Nova Jito
- 🎯 Pump Graduate
- 💭 Sentiment
- ⚖️ Arbitrage
- 🎯 Sniper
- ⏱️ Scalper

### Tokenomics Dashboard
- Real-time fee distribution visualization
- Treasury status across all 4 buckets
- Flywheel metrics and projections
- Agent performance leaderboard
- Trade history and analytics

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/kozzlost/sol-swarm-elite
cd sol-swarm-elite

# Setup
cp .env.example .env
pip install -r requirements.txt

# Configure wallets in .env
# BOT_TRADING_WALLET=your_wallet
# INFRASTRUCTURE_WALLET=your_wallet
# DEVELOPMENT_WALLET=your_wallet
# BUILDER_WALLET=your_wallet

# Run
streamlit run main.py
```

Visit: `http://localhost:8501`

## 📁 Architecture

```
sol-swarm-elite/
├── src/
│   ├── agents/
│   │   ├── scout_agent.py      # Token discovery
│   │   ├── sentiment_agent.py  # Social analysis
│   │   ├── arbiter_agent.py    # Trade decisions
│   │   ├── sniper_agent.py     # Execution
│   │   ├── sell_agent.py       # Exit logic
│   │   ├── treasury_agent.py   # Capital management
│   │   └── agent_spawner.py    # Swarm management
│   ├── tokenomics/
│   │   ├── agent_token.py      # $AGENT token logic
│   │   └── fee_collector.py    # Fee routing
│   ├── services/               # API integrations
│   ├── strategies/             # Trading strategies
│   ├── command_center.py       # Main orchestration
│   └── constants.py
├── dashboard/
│   └── components/
│       └── tokenomics_panel.py # Fee visualization
├── main.py                     # Entry point
├── requirements.txt
└── .env.example
```

## ⚙️ Configuration

### Environment Variables

```env
# Trading
MAINNET_ENABLED=false
ACTIVE_STRATEGY=MOMENTUM

# $AGENT Token
AGENT_TOKEN_MINT=              # Set after token launch
AGENT_FEE_BPS=200              # 2% fee

# Fee Wallets (25% each)
BOT_TRADING_WALLET=            # Trading capital
INFRASTRUCTURE_WALLET=         # Server/API costs
DEVELOPMENT_WALLET=            # Dev fund
BUILDER_WALLET=                # Your income

# Agent Swarm
MAX_AGENTS=100
AUTO_SCALE_ENABLED=true

# Risk
STOP_LOSS_PCT=15
MAX_DRAWDOWN_PCT=15
```

## 🛡️ Risk Management

- 🛑 Max drawdown: 15% (auto pause)
- 📊 Position sizing: 0.01-0.05 SOL
- 💼 Max positions: 3 concurrent per agent
- ⏱️ Position timeout: 30 minutes
- 🔄 Automatic underperformer culling

## 🔗 API Integrations

**Free Tier Compatible:**
- DexScreener (token discovery)
- RugCheck (security)
- X/Twitter (sentiment)
- Solscan (whale tracking)

**Optional Premium:**
- Cielo (smart money)
- LunarCrush (galaxy scores)
- Birdeye (extended data)

## ⚠️ Mainnet Trading

**EXTREMELY DANGEROUS** - Only after extensive paper trading:

1. Set `MAINNET_ENABLED=true`
2. Configure wallet private key
3. Set fee distribution wallets
4. Start with minimal capital ($1-5)
5. Monitor closely

## 📊 Testing

```bash
pytest tests/ -v
mypy src --ignore-missing-imports
ruff check .
```

## 🐳 Docker

```bash
docker build -t sol-swarm .
docker run -p 8501:8501 -e MAINNET_ENABLED=false sol-swarm
```

## 📜 License

MIT License - See LICENSE

## ⚠️ Disclaimer

THIS SOFTWARE IS FOR EDUCATIONAL AND RESEARCH PURPOSES ONLY.

- ❌ NOT financial advice
- ❌ 90%+ of memecoins = COMPLETE LOSS
- ❌ NEVER use real funds without testing
- ❌ Developers NOT liable for losses

---

**Made with ❤️ for the Solana community**

**$AGENT Token: Powering 100 AI Agents**
