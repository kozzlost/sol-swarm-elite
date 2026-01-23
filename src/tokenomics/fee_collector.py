"""
Fee Collector - Intercepts all swarm trades and routes fees to the 4 buckets.
This is the integration layer between trading agents and the $AGENT tokenomics.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Callable, Awaitable
from enum import Enum
import logging

from src.tokenomics.agent_token import get_token_manager, FeeDistribution
from src.agents.treasury_agent import get_treasury_agent

logger = logging.getLogger(__name__)


class TradeType(Enum):
    """Types of trades the swarm can execute"""
    BUY = "buy"
    SELL = "sell"
    SNIPE = "snipe"
    ARB = "arb"


@dataclass
class TradeRecord:
    """Record of a trade with fee information"""
    trade_id: str
    agent_id: str
    agent_type: str
    trade_type: TradeType
    token_address: str
    amount_sol: float
    token_amount: float
    price: float
    timestamp: datetime
    tx_signature: Optional[str]
    fee_distribution: Optional[FeeDistribution]
    pnl: float = 0.0  # Realized PnL for sells


class FeeCollector:
    """
    Central fee collection system for all swarm trading activity.
    
    Hooks into:
    - Sniper Agent executions
    - Arbiter Agent trades
    - Sell Agent exits
    - Any other trading activity
    
    Automatically:
    - Calculates fees on every trade
    - Routes to 4 buckets (25/25/25/25)
    - Updates treasury agent with new capital
    - Tracks performance for each agent
    """
    
    def __init__(self):
        self.token_manager = get_token_manager()
        self.treasury_agent = get_treasury_agent()
        
        self.trade_history: list[TradeRecord] = []
        self.total_volume: float = 0.0
        self.total_fees: float = 0.0
        
        # Callbacks for external integrations
        self._on_fee_collected: list[Callable[[FeeDistribution], Awaitable[None]]] = []
        self._on_trade_recorded: list[Callable[[TradeRecord], Awaitable[None]]] = []
        
    async def process_trade(
        self,
        trade_id: str,
        agent_id: str,
        agent_type: str,
        trade_type: TradeType,
        token_address: str,
        amount_sol: float,
        token_amount: float,
        price: float,
        tx_signature: Optional[str] = None,
        pnl: float = 0.0
    ) -> TradeRecord:
        """
        Process a trade and collect fees.
        
        This is the main entry point - call this after every trade execution.
        
        Args:
            trade_id: Unique identifier for this trade
            agent_id: ID of the agent that executed the trade
            agent_type: Type of agent (sniper, arbiter, etc.)
            trade_type: Buy, sell, snipe, or arb
            token_address: Solana token mint address
            amount_sol: SOL value of the trade
            token_amount: Number of tokens traded
            price: Price per token
            tx_signature: Solana transaction signature
            pnl: Realized PnL (for sell trades)
            
        Returns:
            TradeRecord with fee information
        """
        # Calculate and process fee
        fee_distribution = await self.token_manager.process_trade_fee(
            trade_amount_sol=amount_sol,
            tx_signature=tx_signature or trade_id
        )
        
        # Create trade record
        record = TradeRecord(
            trade_id=trade_id,
            agent_id=agent_id,
            agent_type=agent_type,
            trade_type=trade_type,
            token_address=token_address,
            amount_sol=amount_sol,
            token_amount=token_amount,
            price=price,
            timestamp=datetime.now(timezone.utc),
            tx_signature=tx_signature,
            fee_distribution=fee_distribution,
            pnl=pnl
        )
        
        # Update tracking
        self.trade_history.append(record)
        self.total_volume += amount_sol
        self.total_fees += fee_distribution.total_fee
        
        # Update treasury agent with performance
        win = 1 if pnl > 0 else 0
        await self.treasury_agent.update_agent_performance(
            agent_id=agent_id,
            pnl_change=pnl - fee_distribution.total_fee,  # Net of fees
            trades=1,
            wins=win
        )
        
        # Sync new fee capital to treasury
        await self.treasury_agent.sync_from_fees()
        
        # Fire callbacks
        for callback in self._on_fee_collected:
            try:
                await callback(fee_distribution)
            except Exception as e:
                logger.error(f"Fee callback error: {e}")
                
        for callback in self._on_trade_recorded:
            try:
                await callback(record)
            except Exception as e:
                logger.error(f"Trade callback error: {e}")
        
        logger.info(
            f"Trade processed: {trade_type.value} {amount_sol:.4f} SOL | "
            f"Fee: {fee_distribution.total_fee:.6f} SOL | "
            f"Agent: {agent_id}"
        )
        
        return record
    
    def on_fee_collected(self, callback: Callable[[FeeDistribution], Awaitable[None]]):
        """Register a callback for when fees are collected"""
        self._on_fee_collected.append(callback)
        
    def on_trade_recorded(self, callback: Callable[[TradeRecord], Awaitable[None]]):
        """Register a callback for when trades are recorded"""
        self._on_trade_recorded.append(callback)
    
    def get_stats(self) -> dict:
        """Get fee collection statistics"""
        return {
            "total_trades": len(self.trade_history),
            "total_volume_sol": self.total_volume,
            "total_fees_sol": self.total_fees,
            "avg_fee_per_trade": self.total_fees / max(len(self.trade_history), 1),
            "fee_rate_bps": self.token_manager.config.transaction_fee_bps,
            "trades_by_type": self._count_by_type(),
            "trades_by_agent_type": self._count_by_agent_type(),
            "volume_by_agent": self._volume_by_agent()
        }
    
    def _count_by_type(self) -> dict:
        counts = {}
        for trade in self.trade_history:
            trade_type = trade.trade_type.value
            counts[trade_type] = counts.get(trade_type, 0) + 1
        return counts
    
    def _count_by_agent_type(self) -> dict:
        counts = {}
        for trade in self.trade_history:
            counts[trade.agent_type] = counts.get(trade.agent_type, 0) + 1
        return counts
    
    def _volume_by_agent(self) -> dict:
        volumes = {}
        for trade in self.trade_history:
            volumes[trade.agent_id] = volumes.get(trade.agent_id, 0) + trade.amount_sol
        return volumes
    
    def get_recent_trades(self, limit: int = 50) -> list[dict]:
        """Get recent trades for display"""
        recent = self.trade_history[-limit:]
        return [
            {
                "trade_id": t.trade_id,
                "agent_id": t.agent_id,
                "agent_type": t.agent_type,
                "type": t.trade_type.value,
                "token": t.token_address[:8] + "...",
                "amount_sol": t.amount_sol,
                "fee": t.fee_distribution.total_fee if t.fee_distribution else 0,
                "pnl": t.pnl,
                "time": t.timestamp.strftime("%H:%M:%S")
            }
            for t in reversed(recent)
        ]


# Global instance
_fee_collector: Optional[FeeCollector] = None


def get_fee_collector() -> FeeCollector:
    """Get or create the global fee collector"""
    global _fee_collector
    if _fee_collector is None:
        _fee_collector = FeeCollector()
    return _fee_collector


# Convenience functions for integration with existing agents

async def collect_snipe_fee(
    agent_id: str,
    token_address: str,
    amount_sol: float,
    token_amount: float,
    price: float,
    tx_signature: str
) -> TradeRecord:
    """Convenience function for sniper agent"""
    return await get_fee_collector().process_trade(
        trade_id=f"snipe_{tx_signature[:8]}",
        agent_id=agent_id,
        agent_type="sniper",
        trade_type=TradeType.SNIPE,
        token_address=token_address,
        amount_sol=amount_sol,
        token_amount=token_amount,
        price=price,
        tx_signature=tx_signature
    )


async def collect_buy_fee(
    agent_id: str,
    agent_type: str,
    token_address: str,
    amount_sol: float,
    token_amount: float,
    price: float,
    tx_signature: str
) -> TradeRecord:
    """Convenience function for buy trades"""
    return await get_fee_collector().process_trade(
        trade_id=f"buy_{tx_signature[:8]}",
        agent_id=agent_id,
        agent_type=agent_type,
        trade_type=TradeType.BUY,
        token_address=token_address,
        amount_sol=amount_sol,
        token_amount=token_amount,
        price=price,
        tx_signature=tx_signature
    )


async def collect_sell_fee(
    agent_id: str,
    agent_type: str,
    token_address: str,
    amount_sol: float,
    token_amount: float,
    price: float,
    tx_signature: str,
    realized_pnl: float
) -> TradeRecord:
    """Convenience function for sell trades"""
    return await get_fee_collector().process_trade(
        trade_id=f"sell_{tx_signature[:8]}",
        agent_id=agent_id,
        agent_type=agent_type,
        trade_type=TradeType.SELL,
        token_address=token_address,
        amount_sol=amount_sol,
        token_amount=token_amount,
        price=price,
        tx_signature=tx_signature,
        pnl=realized_pnl
    )


async def collect_arb_fee(
    agent_id: str,
    token_address: str,
    amount_sol: float,
    profit_sol: float,
    tx_signature: str
) -> TradeRecord:
    """Convenience function for arbitrage trades"""
    return await get_fee_collector().process_trade(
        trade_id=f"arb_{tx_signature[:8]}",
        agent_id=agent_id,
        agent_type="arbiter",
        trade_type=TradeType.ARB,
        token_address=token_address,
        amount_sol=amount_sol,
        token_amount=0,
        price=0,
        tx_signature=tx_signature,
        pnl=profit_sol
    )
