"""
Treasury Agent - Capital Management & Fee Distribution
Manages the 4-way fee split and bot trading capital.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, List
from dataclasses import dataclass, field

from src.constants import TOKENOMICS, PAPER_TRADING
from src.types import TreasurySnapshot

logger = logging.getLogger(__name__)


@dataclass
class FeeDistribution:
    """Record of a fee distribution"""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    total_fee_sol: float = 0.0
    
    # Distribution amounts
    bot_trading: float = 0.0
    infrastructure: float = 0.0
    development: float = 0.0
    builder: float = 0.0
    
    # Transaction
    tx_signature: Optional[str] = None
    source_trade_id: Optional[str] = None


@dataclass
class AgentAllocation:
    """Capital allocation to a specific trading agent"""
    agent_id: str
    agent_type: str
    allocated_sol: float = 0.0
    current_balance: float = 0.0
    pnl: float = 0.0
    trades_executed: int = 0
    win_rate: float = 0.0
    allocated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class TreasuryAgent:
    """
    Manages the $AGENT token fee distribution and trading capital.
    
    Fee Split (2% of all $AGENT trades):
    - 25% → Bot Trading Treasury
    - 25% → Infrastructure (AI APIs, servers)
    - 25% → Development Fund
    - 25% → Builder Income
    
    The Treasury Agent specifically manages the Bot Trading portion,
    allocating capital to individual trading agents.
    """
    
    def __init__(self):
        self._running = False
        
        # Treasury state
        self.total_fees_collected: float = 0.0
        self.fee_history: List[FeeDistribution] = []
        
        # Current balances (in SOL)
        self.bot_trading_balance: float = 0.0
        self.infrastructure_balance: float = 0.0
        self.development_balance: float = 0.0
        self.builder_balance: float = 0.0
        
        # Agent allocations
        self.agent_allocations: Dict[str, AgentAllocation] = {}
        
        # Config
        self.min_allocation_sol = 0.01
        self.max_allocation_sol = 0.5
    
    async def start(self):
        """Initialize the treasury agent"""
        self._running = True
        logger.info("💰 Treasury Agent initialized")
    
    async def stop(self):
        """Shutdown the treasury agent"""
        self._running = False
        logger.info("Treasury Agent stopped")
    
    # =========================================================================
    # FEE COLLECTION
    # =========================================================================
    
    async def collect_fee(
        self,
        trade_amount_sol: float,
        trade_id: Optional[str] = None
    ) -> FeeDistribution:
        """
        Collect and distribute fee from a trade
        
        Fee = 2% of trade amount, split 4 ways
        """
        # Calculate total fee (2%)
        total_fee = trade_amount_sol * (TOKENOMICS.TOTAL_FEE_PCT / 100)
        
        # Split to 4 buckets (25% each)
        bot_share = total_fee * (TOKENOMICS.BOT_TRADING_PCT / 100)
        infra_share = total_fee * (TOKENOMICS.INFRASTRUCTURE_PCT / 100)
        dev_share = total_fee * (TOKENOMICS.DEVELOPMENT_PCT / 100)
        builder_share = total_fee * (TOKENOMICS.BUILDER_PCT / 100)
        
        # Update balances
        self.bot_trading_balance += bot_share
        self.infrastructure_balance += infra_share
        self.development_balance += dev_share
        self.builder_balance += builder_share
        self.total_fees_collected += total_fee
        
        # Create distribution record
        distribution = FeeDistribution(
            total_fee_sol=total_fee,
            bot_trading=bot_share,
            infrastructure=infra_share,
            development=dev_share,
            builder=builder_share,
            source_trade_id=trade_id
        )
        
        self.fee_history.append(distribution)
        
        logger.debug(
            f"💸 Fee collected: {total_fee:.6f} SOL "
            f"(Bot: {bot_share:.6f}, Infra: {infra_share:.6f}, "
            f"Dev: {dev_share:.6f}, Builder: {builder_share:.6f})"
        )
        
        return distribution
    
    # =========================================================================
    # CAPITAL ALLOCATION
    # =========================================================================
    
    async def allocate_to_agent(
        self,
        agent_id: str,
        agent_type: str,
        amount_sol: float
    ) -> Optional[AgentAllocation]:
        """
        Allocate capital from bot trading treasury to an agent
        """
        if amount_sol > self.bot_trading_balance:
            logger.warning(
                f"Insufficient treasury balance: "
                f"requested {amount_sol:.4f}, available {self.bot_trading_balance:.4f}"
            )
            return None
        
        if amount_sol < self.min_allocation_sol:
            logger.warning(f"Allocation below minimum: {amount_sol:.4f} < {self.min_allocation_sol}")
            return None
        
        # Deduct from treasury
        self.bot_trading_balance -= amount_sol
        
        # Create or update allocation
        if agent_id in self.agent_allocations:
            allocation = self.agent_allocations[agent_id]
            allocation.allocated_sol += amount_sol
            allocation.current_balance += amount_sol
        else:
            allocation = AgentAllocation(
                agent_id=agent_id,
                agent_type=agent_type,
                allocated_sol=amount_sol,
                current_balance=amount_sol
            )
            self.agent_allocations[agent_id] = allocation
        
        logger.info(f"📊 Allocated {amount_sol:.4f} SOL to {agent_type} agent {agent_id[:8]}")
        
        return allocation
    
    async def recall_from_agent(
        self,
        agent_id: str,
        amount_sol: Optional[float] = None
    ) -> float:
        """
        Recall capital from an agent back to treasury
        """
        if agent_id not in self.agent_allocations:
            logger.warning(f"No allocation found for agent {agent_id}")
            return 0.0
        
        allocation = self.agent_allocations[agent_id]
        
        # Recall all if amount not specified
        if amount_sol is None:
            amount_sol = allocation.current_balance
        
        amount_sol = min(amount_sol, allocation.current_balance)
        
        # Update allocation
        allocation.current_balance -= amount_sol
        
        # Return to treasury
        self.bot_trading_balance += amount_sol
        
        logger.info(f"📊 Recalled {amount_sol:.4f} SOL from agent {agent_id[:8]}")
        
        return amount_sol
    
    async def update_agent_pnl(
        self,
        agent_id: str,
        pnl: float,
        trades: int = 0,
        wins: int = 0
    ):
        """
        Update an agent's P&L and stats
        """
        if agent_id not in self.agent_allocations:
            return
        
        allocation = self.agent_allocations[agent_id]
        allocation.pnl += pnl
        allocation.current_balance += pnl
        allocation.trades_executed += trades
        
        if allocation.trades_executed > 0:
            total_wins = int(allocation.win_rate * (allocation.trades_executed - trades) + wins)
            allocation.win_rate = total_wins / allocation.trades_executed
    
    # =========================================================================
    # REBALANCING
    # =========================================================================
    
    async def rebalance_agents(self):
        """
        Rebalance capital across agents based on performance
        """
        if not self.agent_allocations:
            return
        
        # Sort agents by performance (ROI)
        sorted_agents = sorted(
            self.agent_allocations.values(),
            key=lambda a: a.pnl / max(a.allocated_sol, 0.001),
            reverse=True
        )
        
        # Top performers get more capital
        for i, allocation in enumerate(sorted_agents):
            if i < len(sorted_agents) // 3:  # Top third
                roi = allocation.pnl / max(allocation.allocated_sol, 0.001)
                if roi > 0.1:  # 10%+ ROI
                    bonus = min(0.02, self.bot_trading_balance * 0.1)
                    if bonus > 0:
                        await self.allocate_to_agent(
                            allocation.agent_id,
                            allocation.agent_type,
                            bonus
                        )
        
        logger.info("📊 Agent capital rebalanced based on performance")
    
    # =========================================================================
    # WITHDRAWAL
    # =========================================================================
    
    async def withdraw_builder_income(self, amount_sol: Optional[float] = None) -> float:
        """
        Withdraw from builder income bucket
        """
        if amount_sol is None:
            amount_sol = self.builder_balance
        
        amount_sol = min(amount_sol, self.builder_balance)
        self.builder_balance -= amount_sol
        
        # In production, this would create a transfer to the builder wallet
        logger.info(f"💵 Builder withdrawal: {amount_sol:.4f} SOL")
        
        return amount_sol
    
    # =========================================================================
    # SNAPSHOTS & REPORTING
    # =========================================================================
    
    def get_snapshot(self) -> TreasurySnapshot:
        """
        Get current treasury state
        """
        return TreasurySnapshot(
            bot_trading_balance=self.bot_trading_balance,
            infrastructure_balance=self.infrastructure_balance,
            development_balance=self.development_balance,
            builder_balance=self.builder_balance,
            total_fees_collected=self.total_fees_collected,
            total_distributed=sum(f.total_fee_sol for f in self.fee_history)
        )
    
    def get_agent_leaderboard(self) -> List[Dict]:
        """
        Get agents ranked by performance
        """
        leaderboard = []
        
        for allocation in self.agent_allocations.values():
            roi = (allocation.pnl / max(allocation.allocated_sol, 0.001)) * 100
            
            leaderboard.append({
                "agent_id": allocation.agent_id[:8],
                "type": allocation.agent_type,
                "allocated": allocation.allocated_sol,
                "current": allocation.current_balance,
                "pnl": allocation.pnl,
                "roi_pct": roi,
                "trades": allocation.trades_executed,
                "win_rate": allocation.win_rate * 100
            })
        
        return sorted(leaderboard, key=lambda x: x["roi_pct"], reverse=True)
    
    def get_fee_stats(self) -> Dict:
        """
        Get fee collection statistics
        """
        if not self.fee_history:
            return {
                "total_collected": 0,
                "distribution_count": 0,
                "avg_fee": 0
            }
        
        return {
            "total_collected": self.total_fees_collected,
            "distribution_count": len(self.fee_history),
            "avg_fee": self.total_fees_collected / len(self.fee_history),
            "bot_trading_total": sum(f.bot_trading for f in self.fee_history),
            "infrastructure_total": sum(f.infrastructure for f in self.fee_history),
            "development_total": sum(f.development for f in self.fee_history),
            "builder_total": sum(f.builder for f in self.fee_history)
        }


# Singleton instance
_treasury_agent: Optional[TreasuryAgent] = None


def get_treasury_agent() -> TreasuryAgent:
    """Get or create the treasury agent singleton"""
    global _treasury_agent
    if _treasury_agent is None:
        _treasury_agent = TreasuryAgent()
    return _treasury_agent
