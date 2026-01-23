"""
Treasury Agent - Manages the bot trading treasury funded by $AGENT fees.
Part of the Swarm Elite multi-agent system.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, List
from enum import Enum
import logging

from src.tokenomics.agent_token import get_token_manager, FeeAllocation

logger = logging.getLogger(__name__)


class TreasuryAction(Enum):
    """Actions the treasury agent can take"""
    ALLOCATE = "allocate"           # Allocate capital to a trading agent
    RECALL = "recall"               # Recall capital from an agent
    REBALANCE = "rebalance"         # Rebalance across agents
    COMPOUND = "compound"           # Reinvest profits
    REPORT = "report"               # Generate status report


@dataclass
class AgentAllocation:
    """Capital allocation to a specific trading agent"""
    agent_id: str
    agent_type: str  # scout, sniper, arbiter, etc.
    allocated_sol: float
    pnl: float = 0.0
    trades_executed: int = 0
    win_rate: float = 0.0
    allocated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: Optional[datetime] = None
    
    @property
    def current_value(self) -> float:
        return self.allocated_sol + self.pnl
    
    @property
    def roi_pct(self) -> float:
        if self.allocated_sol <= 0:
            return 0.0
        return (self.pnl / self.allocated_sol) * 100


@dataclass
class TreasuryState:
    """Current state of the trading treasury"""
    available_capital: float = 0.0
    allocated_capital: float = 0.0
    total_pnl: float = 0.0
    allocations: List[AgentAllocation] = field(default_factory=list)
    
    @property
    def total_capital(self) -> float:
        return self.available_capital + self.allocated_capital
    
    @property
    def utilization_pct(self) -> float:
        if self.total_capital <= 0:
            return 0.0
        return (self.allocated_capital / self.total_capital) * 100


class TreasuryAgent:
    """
    Manages the 25% of fees allocated to bot trading capital.
    
    Responsibilities:
    - Track available trading capital from fee accumulation
    - Allocate capital to trading agents based on performance
    - Monitor agent performance and rebalance
    - Compound winning strategies
    - Enforce risk limits
    """
    
    def __init__(
        self,
        max_single_allocation_pct: float = 20.0,  # Max 20% to any single agent
        min_allocation_sol: float = 0.01,          # Minimum allocation
        max_agents: int = 100,                     # Support up to 100 agents
        risk_threshold_drawdown: float = 0.15,    # 15% drawdown triggers review
    ):
        self.max_single_allocation_pct = max_single_allocation_pct
        self.min_allocation_sol = min_allocation_sol
        self.max_agents = max_agents
        self.risk_threshold_drawdown = risk_threshold_drawdown
        
        self.state = TreasuryState()
        self.action_history: List[dict] = []
        
        # Performance tracking by agent type
        self.agent_type_performance: dict[str, dict] = {}
        
    async def sync_from_fees(self):
        """
        Sync available capital from the fee distribution system.
        Called periodically to update treasury with new fee income.
        """
        token_manager = get_token_manager()
        bot_trading_balance = token_manager.total_distributed[FeeAllocation.BOT_TRADING]
        
        # Calculate how much is new (not yet in our state)
        current_total = self.state.total_capital
        new_capital = bot_trading_balance - current_total
        
        if new_capital > 0:
            self.state.available_capital += new_capital
            logger.info(f"Treasury synced: +{new_capital:.6f} SOL from fees")
            
            self._record_action(TreasuryAction.COMPOUND, {
                "new_capital": new_capital,
                "total_available": self.state.available_capital
            })
            
        return new_capital
    
    async def allocate_to_agent(
        self,
        agent_id: str,
        agent_type: str,
        amount_sol: float
    ) -> Optional[AgentAllocation]:
        """
        Allocate capital to a trading agent.
        
        Args:
            agent_id: Unique identifier for the agent
            agent_type: Type of agent (scout, sniper, arbiter, etc.)
            amount_sol: Amount to allocate in SOL
            
        Returns:
            AgentAllocation if successful, None if rejected
        """
        # Validation checks
        if amount_sol < self.min_allocation_sol:
            logger.warning(f"Allocation {amount_sol} SOL below minimum {self.min_allocation_sol}")
            return None
            
        if amount_sol > self.state.available_capital:
            logger.warning(f"Insufficient capital: {amount_sol} > {self.state.available_capital}")
            return None
            
        # Check single allocation limit
        max_allowed = self.state.total_capital * (self.max_single_allocation_pct / 100)
        if amount_sol > max_allowed:
            logger.warning(f"Allocation exceeds {self.max_single_allocation_pct}% limit")
            amount_sol = max_allowed
            
        # Check agent count limit
        if len(self.state.allocations) >= self.max_agents:
            logger.warning(f"Max agents ({self.max_agents}) reached")
            return None
            
        # Check for existing allocation to this agent
        existing = next((a for a in self.state.allocations if a.agent_id == agent_id), None)
        if existing:
            # Add to existing allocation
            existing.allocated_sol += amount_sol
            self.state.available_capital -= amount_sol
            self.state.allocated_capital += amount_sol
            logger.info(f"Added {amount_sol} SOL to existing allocation for {agent_id}")
            return existing
            
        # Create new allocation
        allocation = AgentAllocation(
            agent_id=agent_id,
            agent_type=agent_type,
            allocated_sol=amount_sol
        )
        
        self.state.allocations.append(allocation)
        self.state.available_capital -= amount_sol
        self.state.allocated_capital += amount_sol
        
        self._record_action(TreasuryAction.ALLOCATE, {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "amount": amount_sol
        })
        
        logger.info(f"Allocated {amount_sol} SOL to {agent_type} agent {agent_id}")
        return allocation
    
    async def update_agent_performance(
        self,
        agent_id: str,
        pnl_change: float,
        trades: int = 1,
        wins: int = 0
    ):
        """
        Update performance metrics for an agent.
        Called after each trade execution.
        """
        allocation = next((a for a in self.state.allocations if a.agent_id == agent_id), None)
        if not allocation:
            logger.warning(f"No allocation found for agent {agent_id}")
            return
            
        allocation.pnl += pnl_change
        allocation.trades_executed += trades
        allocation.last_activity = datetime.now(timezone.utc)
        
        # Update win rate
        if trades > 0:
            total_wins = (allocation.win_rate * (allocation.trades_executed - trades)) + wins
            allocation.win_rate = total_wins / allocation.trades_executed
            
        # Update total PnL
        self.state.total_pnl = sum(a.pnl for a in self.state.allocations)
        
        # Track by agent type
        if allocation.agent_type not in self.agent_type_performance:
            self.agent_type_performance[allocation.agent_type] = {
                "total_pnl": 0.0,
                "total_trades": 0,
                "total_wins": 0
            }
        self.agent_type_performance[allocation.agent_type]["total_pnl"] += pnl_change
        self.agent_type_performance[allocation.agent_type]["total_trades"] += trades
        self.agent_type_performance[allocation.agent_type]["total_wins"] += wins
        
        # Check for drawdown threshold breach
        if allocation.roi_pct < -self.risk_threshold_drawdown * 100:
            logger.warning(f"Agent {agent_id} breached {self.risk_threshold_drawdown*100}% drawdown threshold")
            await self._handle_drawdown_breach(allocation)
    
    async def _handle_drawdown_breach(self, allocation: AgentAllocation):
        """Handle an agent that has exceeded drawdown limits"""
        # Reduce allocation by 50%
        reduction = allocation.allocated_sol * 0.5
        allocation.allocated_sol -= reduction
        self.state.allocated_capital -= reduction
        self.state.available_capital += reduction
        
        self._record_action(TreasuryAction.RECALL, {
            "agent_id": allocation.agent_id,
            "reason": "drawdown_breach",
            "amount_recalled": reduction
        })
        
        logger.info(f"Recalled {reduction} SOL from {allocation.agent_id} due to drawdown")
    
    async def rebalance(self):
        """
        Rebalance allocations based on agent performance.
        Shift capital from underperformers to top performers.
        """
        if len(self.state.allocations) < 2:
            return
            
        # Sort by ROI
        sorted_allocations = sorted(
            self.state.allocations,
            key=lambda a: a.roi_pct,
            reverse=True
        )
        
        # Top performers (top 25%)
        top_count = max(1, len(sorted_allocations) // 4)
        top_performers = sorted_allocations[:top_count]
        
        # Bottom performers (bottom 25%)
        bottom_performers = sorted_allocations[-top_count:]
        
        # Move 10% from each bottom performer to top performers
        for bottom in bottom_performers:
            if bottom.allocated_sol < self.min_allocation_sol * 2:
                continue
                
            shift_amount = bottom.allocated_sol * 0.1
            bottom.allocated_sol -= shift_amount
            
            # Distribute to top performers
            per_top = shift_amount / len(top_performers)
            for top in top_performers:
                top.allocated_sol += per_top
                
        self._record_action(TreasuryAction.REBALANCE, {
            "top_performers": [a.agent_id for a in top_performers],
            "bottom_performers": [a.agent_id for a in bottom_performers]
        })
        
        logger.info("Treasury rebalanced based on performance")
    
    async def auto_allocate_new_capital(self):
        """
        Automatically allocate new capital that comes in from fees.
        Distributes based on agent type performance.
        """
        await self.sync_from_fees()
        
        available = self.state.available_capital
        if available < self.min_allocation_sol:
            return
            
        # If we have performance data, weight by it
        if self.agent_type_performance:
            # Calculate weights based on PnL (with floor to prevent negative weights)
            type_scores = {}
            for agent_type, perf in self.agent_type_performance.items():
                # Score = PnL + small bonus for trade count
                score = max(0.1, perf["total_pnl"] + (perf["total_trades"] * 0.001))
                type_scores[agent_type] = score
                
            total_score = sum(type_scores.values())
            
            # Allocate proportionally
            for agent_type, score in type_scores.items():
                allocation_pct = score / total_score
                allocation_amount = available * allocation_pct
                
                # Find agents of this type
                agents_of_type = [a for a in self.state.allocations if a.agent_type == agent_type]
                if agents_of_type:
                    # Distribute evenly among agents of this type
                    per_agent = allocation_amount / len(agents_of_type)
                    for agent in agents_of_type:
                        agent.allocated_sol += per_agent
                        self.state.available_capital -= per_agent
                        self.state.allocated_capital += per_agent
        else:
            # No performance data yet - distribute evenly
            if self.state.allocations:
                per_agent = available / len(self.state.allocations)
                for allocation in self.state.allocations:
                    allocation.allocated_sol += per_agent
                    self.state.available_capital -= per_agent
                    self.state.allocated_capital += per_agent
    
    def get_status_report(self) -> dict:
        """Generate comprehensive treasury status report"""
        return {
            "summary": {
                "total_capital": self.state.total_capital,
                "available_capital": self.state.available_capital,
                "allocated_capital": self.state.allocated_capital,
                "utilization_pct": self.state.utilization_pct,
                "total_pnl": self.state.total_pnl,
                "total_roi_pct": (self.state.total_pnl / max(self.state.total_capital, 0.001)) * 100
            },
            "agent_count": len(self.state.allocations),
            "max_agents": self.max_agents,
            "agents_available": self.max_agents - len(self.state.allocations),
            "allocations": [
                {
                    "agent_id": a.agent_id,
                    "agent_type": a.agent_type,
                    "allocated_sol": a.allocated_sol,
                    "current_value": a.current_value,
                    "pnl": a.pnl,
                    "roi_pct": a.roi_pct,
                    "trades": a.trades_executed,
                    "win_rate": a.win_rate,
                    "last_activity": a.last_activity.isoformat() if a.last_activity else None
                }
                for a in sorted(self.state.allocations, key=lambda x: x.roi_pct, reverse=True)
            ],
            "performance_by_type": self.agent_type_performance,
            "risk_metrics": {
                "max_single_allocation_pct": self.max_single_allocation_pct,
                "drawdown_threshold": self.risk_threshold_drawdown * 100,
                "agents_in_drawdown": len([
                    a for a in self.state.allocations 
                    if a.roi_pct < -self.risk_threshold_drawdown * 100
                ])
            }
        }
    
    def _record_action(self, action: TreasuryAction, details: dict):
        """Record an action in the history"""
        self.action_history.append({
            "action": action.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": details
        })


# Global instance
_treasury_agent: Optional[TreasuryAgent] = None


def get_treasury_agent() -> TreasuryAgent:
    """Get or create the global treasury agent"""
    global _treasury_agent
    if _treasury_agent is None:
        _treasury_agent = TreasuryAgent()
    return _treasury_agent
