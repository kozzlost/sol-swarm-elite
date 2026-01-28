# SOL-SWARM Elite

AI-powered autonomous trading swarm for Solana memecoins with sentiment analysis and multi-agent coordination.

## System Architecture

SOL-SWARM Elite is built on a multi-agent system with the following components:

### Core Agents

1. **CEO Agent** - Strategic decision maker
   - Allocates capital and resources
   - Monitors market conditions
   - Pauses trading during high-risk scenarios
   - Tracks portfolio performance

2. **Sentiment Agent** - Social media analyzer
   - Fetches tweets, Reddit posts, Discord messages
   - AI-powered sentiment analysis using BERT
   - Caches results for performance
   - Enriches trade signals with sentiment scores

3. **Scout Agent** - Token discovery (future)
   - Identifies new token launches
   - Monitors liquidity and volume
   - Detects honeypots and rug pulls

4. **Arbiter Agent** - Consensus voter (future)
   - Aggregates decisions from multiple agents
   - Consensus-based trade approval
   - Risk-weighted voting

5. **Sniper Agent** - Trade executor (future)
   - Executes swaps on DEXs
   - Manages slippage and fees
   - Tracks positions

## Features

### ✓ Implemented

- [x] CEO Agent with risk assessment
- [x] Sentiment Analysis Agent with AI/BERT
- [x] Trade signal pipeline
- [x] Market condition monitoring
- [x] Paper trading mode
- [x] Comprehensive logging
- [x] Type-safe data structures
- [x] Configuration management

### 🚧 In Progress

- [ ] Scout Agent token discovery
- [ ] Real Solana DEX integration (Raydium, Orca)
- [ ] Contract security scanning
- [ ] Liquidity pool monitoring
- [ ] Position management

### 📋 Planned

- [ ] Portfolio rebalancing
- [ ] Advanced technical analysis
- [ ] Telegram notifications
- [ ] Web dashboard
- [ ] REST API

## Installation

### Prerequisites

- Python 3.10+
- Solana RPC endpoint
- Social media API tokens (optional)

### Setup

1. **Clone repository**
   ```bash
   git clone https://github.com/kozzlost/sol-swarm-elite.git
   cd sol-swarm-elite
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate  # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your API credentials:
   ```
   # Solana
   SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
   SOLANA_WEBSOCKET_URL=wss://api.mainnet-beta.solana.com
   
   # Social Media APIs
   TWITTER_BEARER_TOKEN=your_token_here
   REDDIT_CLIENT_ID=your_id_here
   REDDIT_CLIENT_SECRET=your_secret_here
   REDDIT_USER_AGENT=SOL-SWARM Elite
   
   # Trading
   PRIVATE_KEY=your_base58_key_here
   PAPER_TRADING_ENABLED=true
   ```

## Usage

### Quick Start

```python
from src.command_center import CommandCenter
from src.types import TradeSignal

# Initialize
cc = CommandCenter()

# Create a trade signal
signal = TradeSignal(
    token="TOKEN",
    token_address="0x...",
    liquidity=150000,
    market_cap=1000000,
    holder_count=500,
    volume_24h=75000,
    price=0.00001,
    timestamp="2024-01-26T12:00:00Z",
    honeypot_score=0.15,
    rug_pull_risk="low",
    contract_verified=True,
    momentum=75.0,
    volume_ratio=1.2
)

# Process through pipeline
success = cc.process_signal(signal)

# Check status
cc.print_status()
```

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test
python examples/test_system.py
```

### Integration Example

```python
import asyncio
from src.command_center import CommandCenter
from src.types import TradeSignal
from datetime import datetime

async def run_trading_loop():
    cc = CommandCenter()
    
    while True:
        # 1. Fetch signals (from scout or API)
        signals = await fetch_new_signals()
        
        # 2. Process each signal
        for signal in signals:
            cc.process_signal(signal)
        
        # 3. Monitor positions
        cc.monitor_positions()
        
        # 4. Update market conditions
        volatility = await get_market_volatility()
        market_change = await get_market_change()
        cc.update_market_conditions(volatility, market_change)
        
        # 5. Print status
        cc.print_status()
        
        # Sleep before next iteration
        await asyncio.sleep(60)  # Every minute

# Run
asyncio.run(run_trading_loop())
```

## Configuration

### Constants (`src/constants.py`)

Key configuration parameters:

```python
# Risk Management
MIN_LIQUIDITY_USD = 50000          # Minimum pool liquidity
MAX_HONEYPOT_SCORE = 0.7           # Maximum rug pull risk
MIN_SENTIMENT_SCORE = 0.55         # Minimum positive sentiment

# Capital Management
CAPITAL_PER_AGENT = 0.05           # SOL per trade
MAX_CONCURRENT_TRADES = 10         # Simultaneous open trades
STOP_LOSS_PERCENT = -5             # Stop loss threshold
TAKE_PROFIT_PERCENT = 25           # Take profit threshold

# Market Conditions
VOLATILITY_ALERT = 20              # Alert if > 20%
MARKET_CRASH_THRESHOLD = -10       # Pause if < -10%
```

## Pipeline

The trading pipeline processes signals through 4 stages:

```
TradeSignal
    ↓
[1] CEO Agent Validation
    - Liquidity check
    - Honeypot check
    - Risk assessment
    ↓
[2] Sentiment Analysis
    - Fetch social media data
    - AI sentiment analysis
    - Score enrichment
    ↓
[3] Arbiter Consensus
    - Technical analysis
    - Contract verification
    - Vote aggregation
    ↓
[4] Sniper Execution
    - Build transaction
    - Execute swap
    - Track position
    ↓
Position Tracking & Monitoring
```

## Risk Management

### CEO Agent Risk Assessment

Risk is evaluated on multiple factors:

- **Honeypot Score** (0-40 points) - Contract liquidity lock risk
- **Liquidity Risk** (0-20 points) - Pool size sufficiency
- **Volume Ratio** (0-20 points) - Unusual trading volume
- **Holder Concentration** (0-20 points) - Wallet distribution

Total: 0-100 scale (0 = very safe, 100 = extremely risky)

### Trading Safeguards

- **Position Limits** - Max 10 concurrent trades
- **Capital Limits** - 0.05 SOL per trade
- **Stop Loss** - Automatic exit at -5%
- **Take Profit** - Automatic exit at +25%
- **Market Monitoring** - Pause trading during crashes (>10% down)

## Sentiment Analysis

### How It Works

1. **Data Collection**
   - Fetches recent tweets mentioning token
   - Scrapes Reddit discussions
   - Aggregates from Discord (if connected)

2. **AI Analysis**
   - Uses BERT (bert-base-uncased) model
   - Classifies text as POSITIVE/NEGATIVE/NEUTRAL
   - Aggregates into percentage scores

3. **Signal Enrichment**
   - Updates TradeSignal with sentiment_score (0-1)
   - Caches results (1 hour TTL)
   - Avoids duplicate API calls

### Example

```python
from src.agents.sentiment_agent import SentimentAgent

sentiment = SentimentAgent()

# Analyze custom texts
texts = [
    "Love this token!",
    "Great project, very bullish",
    "Scam, stay away"
]

result = sentiment.analyze("TOKEN", texts)

print(f"Overall Score: {result.overall_score:.2f}")
print(f"Positive: {result.positive_percentage:.0f}%")
print(f"Negative: {result.negative_percentage:.0f}%")
```

## Monitoring & Logging

### Log Levels

```python
from src.constants import LOG_LEVEL

# Available levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL = "INFO"
```

### Log Output

Example log output during signal processing:

```
2024-01-26 12:34:56 - CommandCenter - INFO - [PIPELINE] Processing signal #1: TOKEN
2024-01-26 12:34:56 - CommandCenter - INFO - [SIGNAL] Price: $0.000010 | Liquidity: $150,000
2024-01-26 12:34:56 - CommandCenter - INFO - [STEP 1/4] CEO Agent evaluation...
2024-01-26 12:34:56 - CEOAgent - INFO - Evaluating signal for TOKEN
2024-01-26 12:34:56 - CommandCenter - INFO - [APPROVED] CEO approved trade (Risk: 25/100)
2024-01-26 12:34:56 - CommandCenter - INFO - [STEP 2/4] Sentiment Agent analysis...
2024-01-26 12:34:58 - SentimentAgent - INFO - Sentiment for TOKEN: 0.72 (+72% / -15%)
2024-01-26 12:34:58 - CommandCenter - INFO - [STEP 3/4] Arbiter Agent voting...
2024-01-26 12:34:58 - CommandCenter - INFO - [STEP 4/4] Sniper Agent execution...
2024-01-26 12:34:59 - CommandCenter - INFO - [EXECUTED] Trade executed successfully for TOKEN
```

## API Reference

### CommandCenter

```python
class CommandCenter:
    def process_signal(signal: TradeSignal) -> bool
    def monitor_positions() -> None
    def update_market_conditions(volatility: float, market_change: float) -> None
    def get_system_status() -> Dict
    def get_detailed_report() -> Dict
    def print_status() -> None
```

### CEOAgent

```python
class CEOAgent:
    def allocate_resources(signal: TradeSignal) -> AgentDecision
    def monitor_market(volatility: float, market_change: float) -> None
    def pause_trading(reason: str, duration_minutes: int = 30) -> None
    def resume_trading() -> None
    def get_status() -> SwarmStatus
    def get_report() -> Dict
```

### SentimentAgent

```python
class SentimentAgent:
    def analyze(token: str, texts: List[str]) -> SentimentAnalysisResult
    def analyze_signal(signal: TradeSignal) -> TradeSignal
    def fetch_twitter_data(token: str, count: int = 50) -> List[str]
    def fetch_reddit_data(token: str, count: int = 50) -> List[str]
```

## Performance Metrics

### Current Benchmarks (Paper Trading)

- **Signal Processing**: ~500ms per signal
- **Sentiment Analysis**: ~2-3s per token (includes API calls)
- **Success Rate**: ~70-80% (simulated)
- **Throughput**: ~120 signals/hour

### Optimization Tips

1. **Cache Sentiment Results** - Enabled by default (1hr TTL)
2. **Batch Processing** - Process multiple signals in parallel
3. **GPU Acceleration** - Use CUDA for faster sentiment analysis
4. **Reduce API Calls** - Combine Twitter + Reddit requests

## Troubleshooting

### Issue: "transformers library not installed"

```bash
pip install transformers torch
```

### Issue: Low sentiment analysis accuracy

- Increase sample size (MIN_TWEETS_FOR_ANALYSIS)
- Use a larger model: `"bert-large-uncased"`
- Filter low-quality texts before analysis

### Issue: API rate limits

- Enable caching (default: 1 hour TTL)
- Reduce API call frequency
- Use multiple API accounts

### Issue: Out of memory during sentiment analysis

- Reduce batch size in sentiment_pipeline
- Use GPU if available
- Analyze fewer samples per token

## Contributing

Contributions are welcome! Areas of interest:

- [ ] Scout Agent implementation
- [ ] Solana DEX integration
- [ ] Technical analysis indicators
- [ ] Web dashboard
- [ ] Performance optimization

## Safety Disclaimer

**⚠️ WARNING**: This is an experimental trading system. Use at your own risk.

- Always use paper trading first
- Start with small amounts
- Monitor positions actively
- Never invest more than you can afford to lose
- This is not financial advice

## License

MIT License - See LICENSE file

## Support

Questions or issues? Open a GitHub issue or reach out:

- GitHub: https://github.com/kozzlost/sol-swarm-elite
- Twitter: @lostKozz

---

Built with ❤️ for the Solana ecosystem
