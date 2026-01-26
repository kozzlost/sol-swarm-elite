"""
SOL-SWARM Elite Constants and Configuration
All thresholds, API endpoints, and system configuration.
"""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional

# =============================================================================
# ENVIRONMENT CONFIGURATION
# =============================================================================

MAINNET_ENABLED = os.getenv("MAINNET_ENABLED", "false").lower() == "true"
PAPER_TRADING = not MAINNET_ENABLED

# Solana RPC endpoints
SOLANA_RPC_MAINNET = os.getenv("SOLANA_RPC_MAINNET", "https://api.mainnet-beta.solana.com")
SOLANA_RPC_DEVNET = os.getenv("SOLANA_RPC_DEVNET", "https://api.devnet.solana.com")
SOLANA_RPC = SOLANA_RPC_MAINNET if MAINNET_ENABLED else SOLANA_RPC_DEVNET

# Jito for MEV protection
JITO_BLOCK_ENGINE = os.getenv("JITO_BLOCK_ENGINE", "https://mainnet.block-engine.jito.wtf")
JITO_TIP_ACCOUNT = os.getenv("JITO_TIP_ACCOUNT", "96gYZGLnJYVFmbjzopPSU6QiEV5fGqZNyN9nmNhvrZU5")
JITO_TIP_LAMPORTS = int(os.getenv("JITO_TIP_LAMPORTS", "10000"))

# =============================================================================
# API ENDPOINTS
# =============================================================================

# DexScreener - Token discovery
DEXSCREENER_API = "https://api.dexscreener.com/latest/dex"
DEXSCREENER_PAIRS_URL = f"{DEXSCREENER_API}/pairs/solana"
DEXSCREENER_SEARCH_URL = f"{DEXSCREENER_API}/search"
DEXSCREENER_TOKENS_URL = f"{DEXSCREENER_API}/tokens"

# RugCheck - Security vetting
RUGCHECK_API = "https://api.rugcheck.xyz/v1"
RUGCHECK_TOKEN_URL = f"{RUGCHECK_API}/tokens"

# Pump.fun - Memecoin launches
PUMPFUN_API = "https://frontend-api.pump.fun"
PUMPFUN_COINS_URL = f"{PUMPFUN_API}/coins"

# Jupiter - DEX aggregator
JUPITER_API = "https://quote-api.jup.ag/v6"
JUPITER_QUOTE_URL = f"{JUPITER_API}/quote"
JUPITER_SWAP_URL = f"{JUPITER_API}/swap"

# Solscan - Whale tracking
SOLSCAN_API = "https://public-api.solscan.io"

# Helius - Enhanced RPC
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY", "")
HELIUS_RPC = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}" if HELIUS_API_KEY else ""

# Birdeye - Market data
BIRDEYE_API = "https://public-api.birdeye.so"
BIRDEYE_API_KEY = os.getenv("BIRDEYE_API_KEY", "")

# =============================================================================
# TRADING THRESHOLDS
# =============================================================================

class TradingThresholds:
    """All trading-related thresholds"""
    
    # Position sizing (in SOL)
    MIN_TRADE_SOL = float(os.getenv("MIN_TRADE_SOL", "0.01"))
    MAX_TRADE_SOL = float(os.getenv("MAX_TRADE_SOL", "0.05"))
    MAX_POSITION_SOL = float(os.getenv("MAX_POSITION_SOL", "0.1"))
    
    # Risk management
    STOP_LOSS_PCT = float(os.getenv("STOP_LOSS_PCT", "15.0"))
    TAKE_PROFIT_PCT = float(os.getenv("TAKE_PROFIT_PCT", "50.0"))
    MAX_DRAWDOWN_PCT = float(os.getenv("MAX_DRAWDOWN_PCT", "15.0"))
    
    # Position limits
    MAX_CONCURRENT_POSITIONS = int(os.getenv("MAX_CONCURRENT_POSITIONS", "3"))
    POSITION_TIMEOUT_MINS = int(os.getenv("POSITION_TIMEOUT_MINS", "30"))
    
    # Token vetting
    MIN_LIQUIDITY_USD = float(os.getenv("MIN_LIQUIDITY_USD", "10000"))
    MAX_HONEYPOT_SCORE = float(os.getenv("MAX_HONEYPOT_SCORE", "0.3"))
    MIN_SENTIMENT_SCORE = float(os.getenv("MIN_SENTIMENT_SCORE", "2.0"))
    
    # Rate limiting
    MAX_TRADES_PER_HOUR = int(os.getenv("MAX_TRADES_PER_HOUR", "20"))
    COOLDOWN_AFTER_LOSS_SECS = int(os.getenv("COOLDOWN_AFTER_LOSS_SECS", "300"))


# =============================================================================
# STRATEGIES
# =============================================================================

class Strategy(Enum):
    """Available trading strategies"""
    MOMENTUM = "momentum"
    GMGN_AI = "gmgn_ai"
    AXIOM_MIGRATION = "axiom_migration"
    WHALE_COPY = "whale_copy"
    NOVA_JITO = "nova_jito"
    PUMP_GRADUATE = "pump_graduate"
    SENTIMENT = "sentiment"
    ARBITRAGE = "arbitrage"
    SNIPER = "sniper"
    SCALPER = "scalper"


ACTIVE_STRATEGY = Strategy(os.getenv("ACTIVE_STRATEGY", "momentum").lower())


# =============================================================================
# $AGENT TOKEN CONFIGURATION
# =============================================================================

@dataclass
class TokenomicsConfig:
    """$AGENT token fee distribution"""
    
    # Token details
    TOKEN_MINT: str = os.getenv("AGENT_TOKEN_MINT", "")
    TOKEN_SYMBOL: str = "AGENT"
    TOKEN_DECIMALS: int = 9
    
    # Fee structure
    TOTAL_FEE_PCT: float = 2.0  # 2% on all trades
    
    # Fee distribution (must sum to 100%)
    BOT_TRADING_PCT: float = 25.0      # Funds the trading bots
    INFRASTRUCTURE_PCT: float = 25.0   # Server costs, AI APIs
    DEVELOPMENT_PCT: float = 25.0      # Future development
    BUILDER_PCT: float = 25.0          # Your income
    
    # Wallet addresses
    BOT_TRADING_WALLET: str = os.getenv("BOT_TRADING_WALLET", "")
    INFRASTRUCTURE_WALLET: str = os.getenv("INFRASTRUCTURE_WALLET", "")
    DEVELOPMENT_WALLET: str = os.getenv("DEVELOPMENT_WALLET", "")
    BUILDER_WALLET: str = os.getenv("BUILDER_WALLET", "")


TOKENOMICS = TokenomicsConfig()


# =============================================================================
# AGENT SWARM CONFIGURATION
# =============================================================================

class SwarmConfig:
    """Configuration for the agent swarm"""
    
    MAX_AGENTS = int(os.getenv("MAX_AGENTS", "100"))
    MIN_AGENTS = int(os.getenv("MIN_AGENTS", "5"))
    
    # Auto-scaling thresholds
    SCALE_UP_CAPITAL_THRESHOLD = float(os.getenv("SCALE_UP_CAPITAL_THRESHOLD", "1.0"))  # SOL
    SCALE_DOWN_LOSS_THRESHOLD = float(os.getenv("SCALE_DOWN_LOSS_THRESHOLD", "0.1"))    # SOL
    
    # Agent allocation
    CAPITAL_PER_AGENT_SOL = float(os.getenv("CAPITAL_PER_AGENT_SOL", "0.05"))
    
    # Strategy distribution (approximate percentages)
    STRATEGY_WEIGHTS = {
        Strategy.MOMENTUM: 20,
        Strategy.PUMP_GRADUATE: 15,
        Strategy.SNIPER: 15,
        Strategy.WHALE_COPY: 10,
        Strategy.SENTIMENT: 10,
        Strategy.GMGN_AI: 10,
        Strategy.AXIOM_MIGRATION: 5,
        Strategy.NOVA_JITO: 5,
        Strategy.ARBITRAGE: 5,
        Strategy.SCALPER: 5,
    }


SWARM = SwarmConfig()


# =============================================================================
# LOGGING & DEBUG
# =============================================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"


# =============================================================================
# RISK WARNINGS
# =============================================================================

RISK_WARNING = """
⚠️ EXTREME RISK WARNING ⚠️
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• 90%+ of memecoins result in COMPLETE LOSS
• This is RESEARCH/EDUCATIONAL software only
• NEVER invest more than you can afford to lose
• Past performance does NOT indicate future results
• This is NOT financial advice (NFA)
• Do Your Own Research (DYOR)

By using this software, you acknowledge and accept these risks.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

if MAINNET_ENABLED:
    print(RISK_WARNING)
