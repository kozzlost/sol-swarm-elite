# 📚 SOL-SWARM Elite - API Documentation

## Agent Interfaces

### Scout Agent

```python
from src.agents.scout_agent import scout_agent

# Scan for tokens
tokens = await scout_agent.scan_tokens()

# Filter by criteria
safe_tokens = [t for t in tokens if t.liquidity > 5000]
```

### Sentiment Agent

```python
from src.agents.sentiment_agent import sentiment_agent

# Analyze token sentiment
sentiment = await sentiment_agent.analyze_token("MYTOKEN")
# Returns: {"overall_sentiment": 2.5, "confidence": 0.75}
```

### Arbiter Agent

```python
from src.agents.arbiter_agent import arbiter_agent

decision, confidence, reasoning = await arbiter_agent.evaluate_token(
    token=token_metadata,
    sentiment=sentiment_data,
    rug_check=rug_result,
    strategy=StrategyType.MOMENTUM
)
# Returns: ("BUY" | "SKIP", 0.0-1.0, "Reasoning string")
```

### Sniper Agent

```python
from src.agents.sniper_agent import sniper_agent

# Execute trade
position = await sniper_agent.execute_buy(
    token=token_metadata,
    amount_sol=0.05,
    strategy="MOMENTUM"
)
```

### Sell Agent

```python
from src.agents.sell_agent import sell_agent

# Check exit condition
exit_signal = await sell_agent.evaluate_exit(
    position=position,
    current_price=1.25
)
# Returns: ("PARTIAL_EXIT" | "FULL_EXIT" | None, "reason")
```

## Service APIs

### DexScreener

```python
from src.services.dexscreener import dexscreener

# Get trending tokens
tokens = await dexscreener.get_trending_tokens(
    min_liquidity=5000,
    max_market_cap=500000
)

# Get specific token
token = await dexscreener.get_token_by_address(
    address="EPjFWaJY42CCwmWYvgnxbRrJsqkBDicsH3B5CBdAfsV"
)
```

### RugCheck

```python
from src.services.rugcheck import rug_service

# Check token safety
result = await rug_service.check_token(
    token_address="..."
)
# Returns: {
#   "is_honeypot": bool,
#   "is_mintable": bool,
#   "is_freezable": bool,
#   "lp_burned_percent": float,
#   "score": 0-100
# }
```

### Phantom Wallet

```python
from src.services.phantom_wallet import phantom_wallet

# Connect wallet
phantom_wallet._load_from_private_key(private_key_base58)

# Check balance
balance_sol = await phantom_wallet.get_balance(rpc_client)

# Sign & send transaction
signed_tx = await phantom_wallet.sign_transaction(tx)
signature = await phantom_wallet.send_transaction(
    tx_bytes=bytes(signed_tx),
    rpc_url=mainnet_rpc
)
```

## Backtesting

```python
from src.analysis.backtest import backtest_engine
import pandas as pd

# Load historical data
df = pd.read_csv("solana_ohlcv_data.csv")

# Run backtest
results = backtest_engine.execute_backtest(
    historical_data=df,
    strategy_func=my_strategy_function,
    max_position_size=0.05
)

# Results: {
#   "total_trades": 50,
#   "win_rate": 0.45,
#   "total_pnl": 2.5,
#   "max_drawdown": -0.15
# }
```

## Configuration

See `.env.example` for all available options.

### Trading Parameters

- `MIN_SENTIMENT_SCORE`: Minimum sentiment for BUY (default: 2.0)
- `MAX_HONEYPOT_SCORE`: Max honeypot % to trade (default: 0.3)
- `MIN_LIQUIDITY_USD`: Minimum liquidity (default: 5000)
- `MAX_POSITION_SIZE`: Max SOL per trade (default: 0.05)

### Risk Parameters

- `MAX_DAILY_DRAWDOWN_PERCENT`: Auto-pause threshold (default: 15)
- `MAX_CONCURRENT_POSITIONS`: Position limit (default: 3)
- `MAX_POSITION_AGE_MINUTES`: Time exit (default: 30)

