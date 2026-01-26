# 🤖 SOL-SWARM Elite

**AI-powered trading system for Solana memecoin research with $AGENT token-funded operations.**

⚠️ **RESEARCH/EDUCATIONAL USE ONLY** - 90%+ rug probability, NFA/DYOR

---

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

---

## ✨ Features

### Multi-Agent Swarm (Up to 100 Agents)
- **Scout Agent**: Token discovery + rug pull detection via RugCheck
- **Sentiment Agent**: Multi-source sentiment analysis (Twitter/X)
- **Arbiter Agent**: AI-powered trading decisions
- **Sniper Agent**: Jupiter DEX execution with Jito MEV protection
- **Sell Agent**: Position management & risk-based exits
- **Treasury Agent**: Fee distribution & capital allocation
- **Agent Spawner**: Dynamic swarm scaling

### Trading Strategies
| Strategy | Description |
|----------|-------------|
| 🚀 Momentum | Follow price momentum signals |
| 🧠 GMGN AI | GMGN.ai signal following |
| 📈 Axiom Migration | Catch Axiom migrations |
| 🐋 Whale Copy | Copy whale wallet trades |
| ⚡ Nova Jito | Jito bundle sniping |
| 🎯 Pump Graduate | Pump.fun graduates |
| 💭 Sentiment | Social sentiment plays |
| ⚖️ Arbitrage | Cross-DEX arbitrage |
| 🎯 Sniper | New token sniping |
| ⏱️ Scalper | Quick in-out scalps |

### Safety Features
- 📝 Paper trading by default (MAINNET_ENABLED=false)
- 🛡️ RugCheck honeypot detection
- ⚠️ Hardcoded risk warnings
- 📉 Max 15% drawdown auto-pause
- 💰 Position sizing 0.01-0.05 SOL

### Dashboard
- Real-time P&L visualization
- Treasury fee distribution charts
- Agent leaderboard
- Position monitoring
- Trade history

---

## 🚀 Quick Start

### 1. Clone & Setup

```bash
git clone https://github.com/kozzlost/sol-swarm-elite
cd sol-swarm-elite

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
```

### 2. Configure Environment

Edit `.env` with your settings:

```env
# Start with paper trading (default)
MAINNET_ENABLED=false

# Choose strategy
ACTIVE_STRATEGY=momentum

# Optional: Add API keys for better data
TWITTER_BEARER_TOKEN=your_token
HELIUS_API_KEY=your_key
```

### 3. Run

```bash
streamlit run main.py
```

Visit: `http://localhost:8501`

---

## 📁 Architecture

```
sol-swarm-elite/
├── src/
│   ├── agents/
│   │   ├── scout_agent.py      # Token discovery + RugCheck
│   │   ├── sentiment_agent.py  # Social analysis
│   │   ├── arbiter_agent.py    # Trade decisions
│   │   ├── sniper_agent.py     # Jupiter execution
│   │   ├── sell_agent.py       # Exit logic
│   │   ├── treasury_agent.py   # Fee management
│   │   └── agent_spawner.py    # Swarm scaling
│   ├── constants.py            # Configuration
│   ├── types.py                # Data structures
│   └── command_center.py       # Main orchestration
├── main.py                     # Streamlit entry
├── requirements.txt
├── .env.example
└── README.md
```

---

## ⚙️ Configuration

### Trading Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `MIN_TRADE_SOL` | 0.01 | Minimum trade size |
| `MAX_TRADE_SOL` | 0.05 | Maximum trade size |
| `STOP_LOSS_PCT` | 15% | Stop loss trigger |
| `TAKE_PROFIT_PCT` | 50% | Take profit trigger |
| `MAX_CONCURRENT_POSITIONS` | 3 | Position limit |
| `MIN_LIQUIDITY_USD` | $10,000 | Minimum liquidity |
| `MAX_HONEYPOT_SCORE` | 0.3 | Max RugCheck score |

### Swarm Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `MAX_AGENTS` | 100 | Maximum swarm size |
| `MIN_AGENTS` | 5 | Minimum swarm size |
| `CAPITAL_PER_AGENT_SOL` | 0.05 | Capital per agent |

---

## 🐳 Docker Deployment

```bash
# Build
docker build -t sol-swarm-elite .

# Run
docker run -p 8501:8501 --env-file .env sol-swarm-elite
```

---

## 🔐 Security

- **Never commit `.env`** - Contains sensitive keys
- **Paper trade first** - Always test before mainnet
- **Use hardware wallet** - For mainnet trading
- **Limit position sizes** - Don't risk what you can't lose

---

## ⚠️ Risk Disclaimer

```
THIS SOFTWARE IS FOR EDUCATIONAL/RESEARCH PURPOSES ONLY.

• 90%+ of memecoins result in COMPLETE LOSS
• Past performance does NOT indicate future results
• This is NOT financial advice (NFA)
• Do Your Own Research (DYOR)
• NEVER invest more than you can afford to lose

By using this software, you acknowledge and accept ALL risks.
The developers are NOT responsible for any financial losses.
```

---

## 📜 License

MIT License - See [LICENSE](LICENSE)

---

## 🤝 Contributing

1. Fork the repo
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push (`git push origin feature/amazing`)
5. Open Pull Request

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/kozzlost/sol-swarm-elite/issues)
- **Twitter**: [@kozzlost](https://twitter.com/kozzlost)

---

**Built with 🤖 by the swarm**
