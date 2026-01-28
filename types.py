"""
SOL-SWARM Elite - Type Definitions
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class TradeAction(str, Enum):
    """Trade execution actions"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    SKIP = "skip"


class AgentAction(str, Enum):
    """CEO Agent decision actions"""
    TRADE = "trade"
    SKIP = "skip"
    PAUSE = "pause"
    LIQUIDATE = "liquidate"


@dataclass
class TradeSignal:
    """Incoming trade signal from Scout Agent"""
    token: str
    token_address: str
    liquidity: float  # USD
    market_cap: float  # USD
    holder_count: int
    volume_24h: float  # USD
    price: float
    timestamp: str
    
    # Risk metrics
    honeypot_score: float  # 0-1 scale
    rug_pull_risk: str  # "low", "medium", "high"
    contract_verified: bool
    
    # Technical
    momentum: float  # 0-100 scale
    volume_ratio: float  # Volume ratio vs average
    
    # Social indicators (pre-fetched)
    sentiment_score: Optional[float] = None
    social_mentions: int = 0
    
    def __post_init__(self):
        """Validate signal data"""
        if self.honeypot_score < 0 or self.honeypot_score > 1:
            raise ValueError(f"Honeypot score must be 0-1, got {self.honeypot_score}")
        if self.liquidity < 0 or self.market_cap < 0:
            raise ValueError("Liquidity and market cap must be non-negative")


@dataclass
class AgentDecision:
    """CEO Agent decision output"""
    action: AgentAction
    reason: str
    
    # For TRADE action
    capital: Optional[float] = None
    agents_to_deploy: Optional[List[str]] = None
    
    # For PAUSE action
    pause_duration_minutes: Optional[int] = None
    
    # Risk level (0-100)
    risk_level: int = 0
    
    confidence: float = 0.5  # 0-1 scale


@dataclass
class SentimentAnalysisResult:
    """Result from sentiment analysis"""
    token: str
    overall_score: float  # 0-1, where 0.5 is neutral
    positive_percentage: float
    negative_percentage: float
    neutral_percentage: float
    
    text_samples: List[str] = field(default_factory=list)
    sample_count: int = 0
    
    analysis_timestamp: str = ""
    model_used: str = "bert-base-uncased"


@dataclass
class TradingPosition:
    """Active trading position"""
    token: str
    entry_price: float
    entry_time: str
    quantity: float
    invested_capital: float
    
    # Position tracking
    current_price: float
    current_value: float
    profit_loss: float
    profit_loss_percent: float
    
    # Stop loss / Take profit
    stop_loss_price: float
    take_profit_price: float
    
    # Status
    status: str = "open"  # "open", "closed", "partial_closed"
    exit_price: Optional[float] = None
    exit_time: Optional[str] = None


@dataclass
class AgentMetrics:
    """Performance metrics for individual agents"""
    agent_name: str
    trades_executed: int = 0
    successful_trades: int = 0
    failed_trades: int = 0
    
    total_capital_deployed: float = 0.0
    total_profit_loss: float = 0.0
    win_rate: float = 0.0
    
    avg_hold_time_minutes: float = 0.0
    last_trade_time: Optional[str] = None
    
    def calculate_metrics(self):
        """Calculate derived metrics"""
        if self.trades_executed > 0:
            self.win_rate = self.successful_trades / self.trades_executed
        return self


@dataclass
class SwarmStatus:
    """Overall swarm status and health"""
    active_agents: int
    total_active_trades: int
    total_capital_deployed: float
    total_profit_loss: float
    
    market_condition: str  # "normal", "volatile", "crash"
    system_health: str  # "healthy", "warning", "critical"
    
    agent_metrics: Dict[str, AgentMetrics] = field(default_factory=dict)
    last_update_time: str = ""
