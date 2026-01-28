# SOL-SWARM Elite - Implementation Guide

Complete guide to understanding, deploying, and extending the system.

## Overview

SOL-SWARM Elite is a multi-agent trading system with the following architecture:

```
Market Data → Scout Agent → TradeSignal
                              ↓
                         Command Center
                              ↓
                    ┌────────┬────────┬──────────┐
                    ↓        ↓        ↓          ↓
                CEO Agent Sentiment Arbiter  Sniper
                Agent     Agent     Agent
                    ↓        ↓        ↓          ↓
              Pipeline Decision→Consensus→Execution
                    ↓        ↓        ↓          ↓
              Position Tracking & Monitoring
                    ↓
              Portfolio Management
```

## Core Components

### 1. Types System (`src/types.py`)

All data structures use Python dataclasses for type safety and validation.

**Key Types:**

- `TradeSignal`: Incoming trade opportunity
- `AgentDecision`: Decision from an agent
- `SentimentAnalysisResult`: Sentiment analysis output
- `TradingPosition`: Active position tracking
- `SwarmStatus`: Overall system status

**Usage:**
```python
from src.types import TradeSignal, AgentDecision

signal = TradeSignal(
    token="SOL",
    price=100.0,
    liquidity=1000000,
    # ... other fields
)

# Type checking works automatically
signal.token  # ✓ str
signal.liquidity  # ✓ float
```

### 2. Constants (`src/constants.py`)

Centralized configuration for all thresholds and parameters.

**Key Constants:**
- `MIN_LIQUIDITY_USD` - Minimum pool liquidity
- `MAX_HONEYPOT_SCORE` - Maximum acceptable risk
- `CAPITAL_PER_AGENT` - Capital allocation per trade
- `MAX_CONCURRENT_TRADES` - Position limit

**Why centralize?**
- Easy parameter tuning
- Single source of truth
- No hardcoded values scattered in code

### 3. CEO Agent (`src/agents/ceo_agent.py`)

**Responsibilities:**
1. **Signal Validation**
   - Check liquidity requirements
   - Assess honeypot/rug pull risk
   - Calculate risk score

2. **Resource Allocation**
   - Approve or reject trades
   - Allocate capital
   - Deploy agents

3. **Market Monitoring**
   - Track volatility
   - Pause trading during crashes
   - Manage system health

**Key Methods:**

```python
# Evaluate signal and make allocation decision
decision = ceo.allocate_resources(signal)

# Monitor market conditions
ceo.monitor_market(volatility=15.2, market_change=2.1)

# Pause trading if needed
ceo.pause_trading("Market crash detected", duration_minutes=60)

# Track trades
ceo.track_trade("TOKEN", entry_price=0.001, quantity=1000)
ceo.close_trade("TOKEN", exit_price=0.0015, profit_loss=500)
```

**Decision Flow:**

```
signal → _validate_basic_requirements()
         ├─ liquidity < MIN_LIQUIDITY → SKIP
         ├─ honeypot_score > MAX_HONEYPOT → SKIP
         └─ pass → _assess_risk()
             → _check_sentiment()
             ├─ sentiment < MIN_SENTIMENT → SKIP
             └─ pass → APPROVE (return AgentDecision)
```

### 4. Sentiment Agent (`src/agents/sentiment_agent.py`)

**Responsibilities:**
1. **Data Collection**
   - Fetch Twitter tweets
   - Scrape Reddit posts
   - Integrate Discord messages

2. **AI Analysis**
   - Use transformer models (BERT)
   - Classify sentiment
   - Aggregate scores

3. **Caching**
   - Cache results to avoid duplicate API calls
   - 1-hour TTL by default
   - Reduce API usage

**Key Methods:**

```python
# Analyze text samples
result = sentiment.analyze("TOKEN", texts)

# Fetch social media data
tweets = sentiment.fetch_twitter_data("TOKEN", count=50)
posts = sentiment.fetch_reddit_data("TOKEN", count=50)

# Analyze full signal with social data
signal = sentiment.analyze_signal(signal)
```

**Model Integration:**

```python
from transformers import pipeline

# Initialize model
self.sentiment_pipeline = pipeline(
    "sentiment-analysis",
    model="bert-base-uncased",
    device=-1  # CPU: -1, GPU: 0
)

# Predict
predictions = self.sentiment_pipeline(texts)
# Returns: [{"label": "POSITIVE", "score": 0.95}, ...]
```

### 5. Command Center (`src/command_center.py`)

**Central Orchestrator** - Coordinates all agents and pipeline.

**Key Methods:**

```python
# Process signal through full pipeline
success = cc.process_signal(signal)

# Get current status
status = cc.get_system_status()

# Get detailed report
report = cc.get_detailed_report()

# Monitor positions
cc.monitor_positions()

# Update market conditions
cc.update_market_conditions(volatility, market_change)
```

**Pipeline Flow:**

```
1. CEO Validation → AgentDecision.action == TRADE?
2. Sentiment Analysis → Enrich signal with sentiment_score
3. Arbiter Voting → Consensus check (simulated)
4. Sniper Execution → Execute trade (simulated)
```

## Data Flow Example

### Scenario: Process New Token

```python
from src.command_center import CommandCenter
from src.types import TradeSignal

cc = CommandCenter()

# 1. Receive signal from market data feed
signal = TradeSignal(
    token="MEMECOIN",
    token_address="0x...",
    price=0.00001,
    liquidity=200000,  # > MIN_LIQUIDITY_USD ✓
    honeypot_score=0.15,  # < MAX_HONEYPOT_SCORE ✓
    # ... other fields
)

# 2. Process through pipeline
success = cc.process_signal(signal)

# Behind the scenes:
# a) CEO Agent checks liquidity & honeypot → APPROVED
# b) Sentiment Agent:
#    - Fetches tweets/posts about MEMECOIN
#    - Analyzes sentiment using BERT
#    - Updates signal.sentiment_score
# c) Arbiter Agent (simulated) → APPROVED
# d) Sniper Agent (simulated) → EXECUTED

# 3. Track position
if success:
    ceo = cc.ceo
    ceo.active_trades["MEMECOIN"]  # ✓ Added to tracking
    
# 4. Monitor
cc.monitor_positions()
# Checks stop loss / take profit
# May close position if thresholds hit

# 5. Check status
status = cc.get_system_status()
print(f"Trades executed: {status['trades_executed']}")
print(f"P/L: {status['total_profit_loss']}")
```

## Development Workflow

### Adding a New Agent

1. **Create agent file** in `src/agents/`

```python
# src/agents/new_agent.py
class NewAgent:
    def __init__(self):
        self.logger = logging.getLogger("NewAgent")
    
    def analyze(self, signal: TradeSignal) -> Dict:
        # Analysis logic
        return result
```

2. **Update Command Center**

```python
# src/command_center.py
from src.agents.new_agent import NewAgent

class CommandCenter:
    def __init__(self):
        self.new_agent = NewAgent()
    
    def process_signal(self, signal):
        # ... existing steps ...
        
        # Add new agent step
        result = self.new_agent.analyze(signal)
```

3. **Update Pipeline**

```python
# Update documentation and type hints
@dataclass
class TradeSignal:
    # Add field if needed
    new_agent_score: Optional[float] = None
```

### Testing an Agent

```python
# examples/test_new_agent.py
from src.agents.new_agent import NewAgent
from src.types import TradeSignal

agent = NewAgent()

# Create test signal
signal = TradeSignal(...)

# Test analysis
result = agent.analyze(signal)

# Verify results
assert result["score"] > 0
assert "reason" in result
```

### Deploying New Code

1. **Test locally**
   ```bash
   python examples/test_system.py
   ```

2. **Run unit tests**
   ```bash
   pytest tests/
   ```

3. **Paper trade**
   ```bash
   PAPER_TRADING_ENABLED=true python main.py
   ```

4. **Monitor logs**
   ```bash
   tail -f logs/sol-swarm-elite.log
   ```

## Performance Optimization

### 1. Sentiment Analysis Caching

Default behavior:
```python
# Caches result for 1 hour
result = sentiment.analyze("TOKEN", texts, use_cache=True)

# Force fresh analysis
result = sentiment.analyze("TOKEN", texts, use_cache=False)
```

**Impact**: Reduces sentiment analysis time from 2-3s to <10ms

### 2. Batch Processing

Instead of processing signals one-by-one:
```python
# ✗ Slow (sequential)
for signal in signals:
    cc.process_signal(signal)

# ✓ Fast (parallel)
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(cc.process_signal, s) for s in signals]
    results = [f.result() for f in futures]
```

### 3. GPU Acceleration

For sentiment analysis on large batches:
```python
# In src/agents/sentiment_agent.py
self.sentiment_pipeline = pipeline(
    "sentiment-analysis",
    model="bert-base-uncased",
    device=0  # Use GPU (change from -1)
)
```

## Monitoring & Metrics

### Key Metrics to Track

```python
# Success rate
success_rate = trades_executed / (trades_executed + trades_failed)

# Win rate
win_rate = successful_trades / trades_executed

# Average profit per trade
avg_profit = total_profit_loss / trades_executed

# Capital efficiency
roi = total_profit_loss / total_capital_deployed

# System health
health = ceo.system_health  # "healthy", "warning", "critical"
```

### Alerting Strategy

```python
# Set up alerts for critical conditions
if ceo.market_condition == "crash":
    send_alert("Market crash detected - trading paused")

if win_rate < 0.50:
    send_alert("Win rate below 50% - review strategy")

if capital_efficiency < 0:
    send_alert("Losing money - stop trading")
```

## Integration with Solana

### Future: Real DEX Integration

```python
# Scout Agent (to be implemented)
class ScoutAgent:
    def discover_tokens(self):
        # Fetch from Raydium/Orca
        # Monitor new pool launches
        # Return TradeSignals
        pass

# Sniper Agent (to be implemented)
class SniperAgent:
    def execute_trade(self, decision):
        # Build swap transaction
        # Submit to Solana network
        # Confirm and track
        pass
```

## Troubleshooting Guide

### Issue: Sentiment analysis is slow

**Solution:**
1. Reduce number of tweets: `MIN_TWEETS_FOR_ANALYSIS = 5`
2. Enable GPU: `device=0` in sentiment_pipeline
3. Use smaller model: `"distilbert-base-uncased"`

### Issue: Many trades getting rejected

**Solution:**
1. Lower liquidity threshold: `MIN_LIQUIDITY_USD = 25000`
2. Increase honeypot tolerance: `MAX_HONEYPOT_SCORE = 0.85`
3. Check sentiment score: `MIN_SENTIMENT_SCORE = 0.45`

### Issue: Running out of memory

**Solution:**
1. Reduce `MAX_CONCURRENT_TRADES`
2. Clear cache: `sentiment_cache = {}`
3. Process fewer signals per batch

## Next Steps

1. **Implement Scout Agent** - Token discovery
2. **Add Real DEX Integration** - Raydium/Orca swaps
3. **Build Web Dashboard** - Real-time monitoring
4. **Create REST API** - External integrations
5. **Deploy to Production** - Live trading

---

Questions? Check the README.md or create an issue on GitHub.
