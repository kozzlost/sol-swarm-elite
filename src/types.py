"""
SOL-SWARM Elite Type Definitions
All data structures used across the system.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from enum import Enum


# =============================================================================
# TOKEN DATA
# =============================================================================

@dataclass
class TokenInfo:
    """Basic token information"""
    mint: str
    symbol: str
    name: str
    decimals: int = 9
    
    # Market data
    price_usd: float = 0.0
    price_sol: float = 0.0
    market_cap_usd: float = 0.0
    liquidity_usd: float = 0.0
    volume_24h_usd: float = 0.0
    
    # Price changes
    price_change_5m: float = 0.0
    price_change_1h: float = 0.0
    price_change_24h: float = 0.0
    
    # Metadata
    image_url: Optional[str] = None
    website: Optional[str] = None
    twitter: Optional[str] = None
    telegram: Optional[str] = None
    
    # Timestamps
    created_at: Optional[datetime] = None
    discovered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class RugCheckResult:
    """Security analysis from RugCheck"""
    mint: str
    is_safe: bool = False
    
    # Risk scores (0-1, lower is safer)
    honeypot_score: float = 1.0
    overall_risk: float = 1.0
    
    # Specific flags
    is_honeypot: bool = True
    is_mintable: bool = True
    is_freezable: bool = True
    has_blacklist: bool = True
    
    # Authority status
    mint_authority_revoked: bool = False
    freeze_authority_revoked: bool = False
    
    # Top holders concentration
    top10_holder_pct: float = 100.0
    
    # Raw response
    raw_data: Optional[Dict[str, Any]] = None
    
    @property
    def passes_safety_check(self) -> bool:
        """Returns True if token passes basic safety checks"""
        return (
            not self.is_honeypot and
            self.honeypot_score < 0.3 and
            self.mint_authority_revoked and
            self.top10_holder_pct < 50
        )


@dataclass
class SentimentResult:
    """Social sentiment analysis"""
    mint: str
    symbol: str
    
    # Aggregate score (-10 to +10)
    overall_score: float = 0.0
    
    # Source-specific scores
    twitter_score: float = 0.0
    twitter_mentions: int = 0
    telegram_score: float = 0.0
    reddit_score: float = 0.0
    
    # Engagement metrics
    total_mentions: int = 0
    positive_mentions: int = 0
    negative_mentions: int = 0
    
    # Trending
    is_trending: bool = False
    trend_velocity: float = 0.0  # Rate of mention increase
    
    # Key phrases/topics
    top_keywords: List[str] = field(default_factory=list)
    
    analyzed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# =============================================================================
# TRADING DATA
# =============================================================================

class TradeAction(Enum):
    """Possible trade actions"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    SKIP = "skip"


class TradeStatus(Enum):
    """Trade execution status"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TradeSignal:
    """A trading signal from an agent"""
    token: TokenInfo
    action: TradeAction
    
    # Signal strength (0-1)
    confidence: float = 0.0
    
    # Recommended sizing
    suggested_amount_sol: float = 0.0
    
    # Risk assessment
    risk_level: str = "high"  # low, medium, high, extreme
    stop_loss_pct: float = 15.0
    take_profit_pct: float = 50.0
    
    # Reasoning
    reasons: List[str] = field(default_factory=list)
    
    # Source
    source_agent: str = ""
    strategy: str = ""
    
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Trade:
    """Executed trade record"""
    trade_id: str
    mint: str
    symbol: str
    
    action: TradeAction
    status: TradeStatus = TradeStatus.PENDING
    
    # Amounts
    amount_sol: float = 0.0
    amount_tokens: float = 0.0
    
    # Prices
    entry_price: float = 0.0
    exit_price: Optional[float] = None
    
    # Results
    pnl_sol: float = 0.0
    pnl_pct: float = 0.0
    fees_paid_sol: float = 0.0
    
    # Transaction details
    tx_signature: Optional[str] = None
    slot: Optional[int] = None
    
    # Agent tracking
    agent_id: str = ""
    strategy: str = ""
    
    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    executed_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None


@dataclass
class Position:
    """Open position"""
    position_id: str
    mint: str
    symbol: str
    
    # Position details
    entry_price: float = 0.0
    current_price: float = 0.0
    amount_tokens: float = 0.0
    amount_sol_invested: float = 0.0
    
    # P&L
    unrealized_pnl_sol: float = 0.0
    unrealized_pnl_pct: float = 0.0
    
    # Risk levels
    stop_loss_price: float = 0.0
    take_profit_price: float = 0.0
    
    # Tracking
    agent_id: str = ""
    entry_trade_id: str = ""
    
    opened_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def update_pnl(self, current_price: float):
        """Update unrealized P&L based on current price"""
        self.current_price = current_price
        self.last_updated = datetime.now(timezone.utc)
        
        if self.entry_price > 0:
            self.unrealized_pnl_pct = ((current_price - self.entry_price) / self.entry_price) * 100
            self.unrealized_pnl_sol = self.amount_sol_invested * (self.unrealized_pnl_pct / 100)


# =============================================================================
# AGENT DATA
# =============================================================================

class AgentStatus(Enum):
    """Agent lifecycle states"""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    PAUSED = "paused"
    COOLDOWN = "cooldown"
    TERMINATED = "terminated"


@dataclass
class AgentStats:
    """Performance statistics for an agent"""
    agent_id: str
    strategy: str
    
    # Capital
    allocated_capital: float = 0.0
    current_capital: float = 0.0
    
    # Trade stats
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    
    # P&L
    total_pnl_sol: float = 0.0
    best_trade_pnl: float = 0.0
    worst_trade_pnl: float = 0.0
    
    # Timing
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_trade_at: Optional[datetime] = None
    
    @property
    def win_rate(self) -> float:
        if self.total_trades == 0:
            return 0.0
        return (self.winning_trades / self.total_trades) * 100
    
    @property
    def roi_pct(self) -> float:
        if self.allocated_capital <= 0:
            return 0.0
        return (self.total_pnl_sol / self.allocated_capital) * 100


# =============================================================================
# TREASURY DATA
# =============================================================================

@dataclass
class TreasurySnapshot:
    """Point-in-time treasury state"""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Balances (in SOL)
    bot_trading_balance: float = 0.0
    infrastructure_balance: float = 0.0
    development_balance: float = 0.0
    builder_balance: float = 0.0
    
    # Totals
    total_fees_collected: float = 0.0
    total_distributed: float = 0.0
    
    @property
    def total_balance(self) -> float:
        return (
            self.bot_trading_balance +
            self.infrastructure_balance +
            self.development_balance +
            self.builder_balance
        )


# =============================================================================
# SYSTEM DATA
# =============================================================================

@dataclass
class SystemHealth:
    """Overall system health status"""
    is_healthy: bool = True
    
    # Component status
    rpc_connected: bool = False
    dexscreener_ok: bool = False
    rugcheck_ok: bool = False
    
    # Performance
    active_agents: int = 0
    open_positions: int = 0
    pending_signals: int = 0
    
    # Rate limits
    api_calls_remaining: int = 1000
    
    # Errors
    recent_errors: List[str] = field(default_factory=list)
    
    last_check: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
