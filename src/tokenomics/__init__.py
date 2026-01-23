"""$AGENT Tokenomics Module"""
from .agent_token import (
    TokenomicsConfig,
    AgentTokenManager,
    FeeAllocation,
    FeeDistribution,
    get_token_manager,
    configure_token_manager
)
from .fee_collector import (
    FeeCollector,
    TradeType,
    TradeRecord,
    get_fee_collector,
    collect_snipe_fee,
    collect_buy_fee,
    collect_sell_fee,
    collect_arb_fee
)

__all__ = [
    "TokenomicsConfig",
    "AgentTokenManager", 
    "FeeAllocation",
    "FeeDistribution",
    "get_token_manager",
    "configure_token_manager",
    "FeeCollector",
    "TradeType",
    "TradeRecord",
    "get_fee_collector",
    "collect_snipe_fee",
    "collect_buy_fee",
    "collect_sell_fee",
    "collect_arb_fee"
]
