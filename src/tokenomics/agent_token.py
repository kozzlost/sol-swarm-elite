"""
$AGENT Token - Fee Distribution System
Handles the 25/25/25/25 fee split for the Swarm Elite ecosystem
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional
import asyncio
from datetime import datetime, timezone
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
import logging

logger = logging.getLogger(__name__)


class FeeAllocation(Enum):
    """Fee distribution buckets"""
    BOT_TRADING = "bot_trading"      # 25% - Capital for bots to trade with
    INFRASTRUCTURE = "infrastructure" # 25% - Server costs, AI tokens, APIs
    DEVELOPMENT = "development"       # 25% - Freelance coders, future features
    BUILDER = "builder"               # 25% - Direct payment to you while building


@dataclass
class TokenomicsConfig:
    """$AGENT Token Configuration"""
    # Token details
    token_mint: str = ""  # Set after deployment
    token_symbol: str = "AGENT"
    token_name: str = "Swarm Elite Agent"
    decimals: int = 9
    total_supply: int = 1_000_000_000  # 1 billion tokens
    
    # Fee configuration
    transaction_fee_bps: int = 200  # 2% fee on trades (200 basis points)
    
    # Fee distribution (must sum to 100)
    bot_trading_pct: int = 25
    infrastructure_pct: int = 25
    development_pct: int = 25
    builder_pct: int = 25
    
    # Wallet addresses (SET THESE)
    bot_trading_wallet: str = ""
    infrastructure_wallet: str = ""
    development_wallet: str = ""
    builder_wallet: str = ""
    
    # RPC
    rpc_url: str = "https://api.mainnet-beta.solana.com"
    
    def validate(self) -> bool:
        """Ensure fee percentages sum to 100"""
        total = (self.bot_trading_pct + self.infrastructure_pct + 
                 self.development_pct + self.builder_pct)
        if total != 100:
            raise ValueError(f"Fee percentages must sum to 100, got {total}")
        return True


@dataclass
class FeeDistribution:
    """Calculated fee amounts for a transaction"""
    total_fee: float
    bot_trading: float
    infrastructure: float
    development: float
    builder: float
    timestamp: datetime
    tx_signature: Optional[str] = None


class AgentTokenManager:
    """
    Manages $AGENT token fee collection and distribution.
    Integrates with the swarm trading system.
    """
    
    def __init__(self, config: TokenomicsConfig):
        self.config = config
        self.config.validate()
        self.client: Optional[AsyncClient] = None
        
        # Running totals
        self.total_fees_collected: float = 0.0
        self.total_distributed: dict[FeeAllocation, float] = {
            FeeAllocation.BOT_TRADING: 0.0,
            FeeAllocation.INFRASTRUCTURE: 0.0,
            FeeAllocation.DEVELOPMENT: 0.0,
            FeeAllocation.BUILDER: 0.0,
        }
        
        # Fee history
        self.fee_history: list[FeeDistribution] = []
        
    async def connect(self):
        """Initialize Solana RPC connection"""
        self.client = AsyncClient(self.config.rpc_url, commitment=Confirmed)
        logger.info(f"Connected to Solana RPC: {self.config.rpc_url}")
        
    async def disconnect(self):
        """Close RPC connection"""
        if self.client:
            await self.client.close()
            
    def calculate_fee(self, trade_amount_sol: float) -> FeeDistribution:
        """
        Calculate fee distribution for a trade.
        
        Args:
            trade_amount_sol: Trade size in SOL
            
        Returns:
            FeeDistribution with amounts for each bucket
        """
        # Calculate total fee (2% default)
        fee_rate = self.config.transaction_fee_bps / 10000
        total_fee = trade_amount_sol * fee_rate
        
        # Distribute to buckets
        distribution = FeeDistribution(
            total_fee=total_fee,
            bot_trading=total_fee * (self.config.bot_trading_pct / 100),
            infrastructure=total_fee * (self.config.infrastructure_pct / 100),
            development=total_fee * (self.config.development_pct / 100),
            builder=total_fee * (self.config.builder_pct / 100),
            timestamp=datetime.now(timezone.utc)
        )
        
        return distribution
    
    async def process_trade_fee(self, trade_amount_sol: float, tx_signature: str) -> FeeDistribution:
        """
        Process a trade and record fee distribution.
        In production, this would trigger actual token transfers.
        
        Args:
            trade_amount_sol: Size of the trade in SOL
            tx_signature: Transaction signature for tracking
            
        Returns:
            FeeDistribution record
        """
        distribution = self.calculate_fee(trade_amount_sol)
        distribution.tx_signature = tx_signature
        
        # Update running totals
        self.total_fees_collected += distribution.total_fee
        self.total_distributed[FeeAllocation.BOT_TRADING] += distribution.bot_trading
        self.total_distributed[FeeAllocation.INFRASTRUCTURE] += distribution.infrastructure
        self.total_distributed[FeeAllocation.DEVELOPMENT] += distribution.development
        self.total_distributed[FeeAllocation.BUILDER] += distribution.builder
        
        # Store in history
        self.fee_history.append(distribution)
        
        logger.info(
            f"Fee processed: {distribution.total_fee:.6f} SOL from trade of {trade_amount_sol:.4f} SOL"
        )
        
        return distribution
    
    def get_treasury_status(self) -> dict:
        """Get current treasury balances across all buckets"""
        return {
            "total_fees_collected": self.total_fees_collected,
            "buckets": {
                "bot_trading": {
                    "balance": self.total_distributed[FeeAllocation.BOT_TRADING],
                    "wallet": self.config.bot_trading_wallet,
                    "purpose": "Capital for AI agents to trade with"
                },
                "infrastructure": {
                    "balance": self.total_distributed[FeeAllocation.INFRASTRUCTURE],
                    "wallet": self.config.infrastructure_wallet,
                    "purpose": "Server costs, AI API tokens, data feeds"
                },
                "development": {
                    "balance": self.total_distributed[FeeAllocation.DEVELOPMENT],
                    "wallet": self.config.development_wallet,
                    "purpose": "Freelance developers, new features"
                },
                "builder": {
                    "balance": self.total_distributed[FeeAllocation.BUILDER],
                    "wallet": self.config.builder_wallet,
                    "purpose": "Direct income while building"
                }
            },
            "fee_rate_bps": self.config.transaction_fee_bps,
            "total_transactions": len(self.fee_history)
        }
    
    def get_flywheel_metrics(self) -> dict:
        """
        Calculate flywheel efficiency metrics.
        Shows how fees are compounding into more trading capital.
        """
        bot_capital = self.total_distributed[FeeAllocation.BOT_TRADING]
        
        # Estimate additional trades enabled by fee-funded capital
        # Assuming average trade size of 0.05 SOL
        avg_trade_size = 0.05
        additional_trades_enabled = int(bot_capital / avg_trade_size) if avg_trade_size > 0 else 0
        
        # Estimate potential fee generation from those trades
        potential_fees = additional_trades_enabled * avg_trade_size * (self.config.transaction_fee_bps / 10000)
        
        return {
            "bot_trading_capital": bot_capital,
            "additional_trades_enabled": additional_trades_enabled,
            "potential_recursive_fees": potential_fees,
            "flywheel_multiplier": (bot_capital + potential_fees) / max(bot_capital, 0.001),
            "infrastructure_runway_days": self._estimate_runway(
                self.total_distributed[FeeAllocation.INFRASTRUCTURE],
                daily_cost_estimate=5.0  # $5/day for servers/APIs
            ),
            "development_hours_funded": self.total_distributed[FeeAllocation.DEVELOPMENT] * 200 / 50,  # $50/hr rate
        }
    
    def _estimate_runway(self, balance: float, daily_cost_estimate: float) -> float:
        """Estimate days of runway for infrastructure costs"""
        sol_price = 150  # Rough estimate, should fetch real price
        usd_balance = balance * sol_price
        return usd_balance / daily_cost_estimate if daily_cost_estimate > 0 else 0


# Global instance
_token_manager: Optional[AgentTokenManager] = None


def get_token_manager() -> AgentTokenManager:
    """Get or create the global token manager instance"""
    global _token_manager
    if _token_manager is None:
        _token_manager = AgentTokenManager(TokenomicsConfig())
    return _token_manager


def configure_token_manager(config: TokenomicsConfig) -> AgentTokenManager:
    """Configure the global token manager with custom settings"""
    global _token_manager
    _token_manager = AgentTokenManager(config)
    return _token_manager
