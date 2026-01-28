# SOL-SWARM Elite - Quick Start Guide

Get up and running in 5 minutes.

## 1. Clone & Setup (2 min)

```bash
# Clone the repo
git clone https://github.com/kozzlost/sol-swarm-elite.git
cd sol-swarm-elite

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

## 2. Configure (1 min)

```bash
# Copy example config
cp .env.example .env

# Edit .env with your settings (at minimum, set paper trading mode)
# nano .env
```

Minimum required (for paper trading):
```
PAPER_TRADING_ENABLED=true
SENTIMENT_MODEL=bert-base-uncased
```

## 3. Run Tests (1 min)

```bash
# Run example tests
python examples/test_system.py
```

Expected output:
```
====================================================================
SOL-SWARM Elite - System Tests
====================================================================

[TEST 1: Basic Trading Pipeline]
...
[TEST 2: Sentiment Analysis]
...
[TEST 3: CEO Agent Decision Making]
...
[TEST 4: Market Monitoring]
...

✓ All tests completed!
```

## 4. Use in Your Code (1 min)

```python
from src.command_center import CommandCenter
from src.types import TradeSignal
from datetime import datetime

# Initialize
cc = CommandCenter()

# Create a trade signal
signal = TradeSignal(
    token="MYTOKEN",
    token_address="0x1234567890abcdef1234567890abcdef12345678",
    liquidity=150000,  # $150k
    market_cap=1000000,  # $1M
    holder_count=500,
    volume_24h=75000,
    price=0.00001,
    timestamp=datetime.now().isoformat(),
    honeypot_score=0.15,
    rug_pull_risk="low",
    contract_verified=True,
    momentum=75.0,
    volume_ratio=1.2
)

# Process through pipeline
print("Processing signal...")
success = cc.process_signal(signal)

# View results
if success:
    print("✓ Trade executed!")
else:
    print("✗ Trade rejected")

# Check status
cc.print_status()
```

## What You Get

### ✓ Working Components

1. **CEO Agent** - Validates signals and allocates resources
2. **Sentiment Agent** - Analyzes Twitter/Reddit sentiment
3. **Command Center** - Orchestrates entire pipeline
4. **Type System** - Type-safe data structures
5. **Paper Trading** - Safe testing mode

### 📊 Metrics

- Signal validation
- Risk assessment
- Sentiment analysis
- Trade tracking
- Performance monitoring

### 🔧 Customization Points

```python
# In src/constants.py
MIN_LIQUIDITY_USD = 50000        # Change liquidity threshold
MAX_HONEYPOT_SCORE = 0.7         # Change risk tolerance
MIN_SENTIMENT_SCORE = 0.55       # Change sentiment threshold
CAPITAL_PER_AGENT = 0.05         # Change capital per trade
```

## Next Steps

### Level 1: Understanding (30 min read)

- [ ] Read [README.md](README.md) for overview
- [ ] Review [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) for architecture
- [ ] Check `src/types.py` for data structures

### Level 2: Exploration (1 hour)

- [ ] Run example tests: `python examples/test_system.py`
- [ ] Modify constants and re-run tests
- [ ] Add custom trade signals
- [ ] Review sentiment analysis results

### Level 3: Integration (2-3 hours)

- [ ] Connect your own data source
- [ ] Implement Scout Agent
- [ ] Add real DEX integration
- [ ] Connect to Solana network

### Level 4: Production (ongoing)

- [ ] Deploy to VPS
- [ ] Set up monitoring/alerting
- [ ] Live trading with small amounts
- [ ] Optimize strategy based on results

## Useful Commands

```bash
# View project structure
tree -I 'venv|__pycache__|*.pyc'

# Run tests
python examples/test_system.py

# Check code quality
flake8 src/

# Format code
black src/

# Run type checker
mypy src/ --ignore-missing-imports

# Watch logs
tail -f logs/sol-swarm-elite.log

# Install GPU support (optional)
pip install torch[cuda]
```

## Common Issues

### Issue: "No module named 'transformers'"
```bash
pip install transformers torch
```

### Issue: "CUDA out of memory"
```python
# In src/agents/sentiment_agent.py
device=-1  # Use CPU instead of GPU
```

### Issue: Tests running slowly
```python
# In src/constants.py
MIN_TWEETS_FOR_ANALYSIS = 3  # Fewer samples for testing
```

## Architecture at a Glance

```
MarketSignal
    ↓
[CEO Agent] - Validates & allocates
    ↓
[Sentiment Agent] - Analyzes Twitter/Reddit
    ↓
[Arbiter Agent] - Consensus voting (simulated)
    ↓
[Sniper Agent] - Executes trade (simulated)
    ↓
Position Tracking
```

## Key Files

| File | Purpose |
|------|---------|
| `src/command_center.py` | Main orchestrator |
| `src/agents/ceo_agent.py` | Signal validation & allocation |
| `src/agents/sentiment_agent.py` | Social sentiment analysis |
| `src/types.py` | Data structures |
| `src/constants.py` | Configuration |
| `examples/test_system.py` | Example usage & tests |

## Performance Tips

1. **Cache sentiment results** (1 hour default)
2. **Process signals in parallel** (4 workers)
3. **Use GPU for BERT** if available
4. **Reduce sample size** for faster analysis

## Getting Help

- 📖 **Docs**: Check [README.md](README.md)
- 🔧 **Implementation**: See [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)
- 💬 **Questions**: Open GitHub issue
- 🐛 **Bugs**: Report with logs and steps to reproduce

## Safety Reminders

⚠️ **This is experimental software**

- Always test in paper trading mode first
- Never invest more than you can afford to lose
- Monitor positions actively
- Start with small amounts
- This is NOT financial advice

## Success Checklist

- [ ] Environment setup (venv, pip install)
- [ ] Dependencies installed
- [ ] .env configured
- [ ] Tests passing
- [ ] First signal processed
- [ ] Status printed successfully
- [ ] Read README and guides
- [ ] Ready to customize

---

**Next**: Read [README.md](README.md) for comprehensive documentation
