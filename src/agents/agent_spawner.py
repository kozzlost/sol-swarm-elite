"""
Agent Spawner - Creates and manages up to 100 AI trading agents.
Each agent is funded from the treasury and specializes in different strategies.
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, List, Callable, Awaitable
from enum import Enum
import logging
import random

from src.agents.treasury_agent import get_treasury_agent
from src.tokenomics.fee_collector import get_fee_collector, TradeType

logger = logging.getLogger(__name__)


class AgentStrategy(Enum):
    """Trading strategies agents can specialize in"""
    MOMENTUM = "momentum"           # Follow price momentum
    GMGN_AI = "gmgn_ai"            # GMGN.ai signal following
    AXIOM_MIGRATION = "axiom"      # Catch Axiom migrations
    WHALE_COPY = "whale_copy"      # Copy whale wallets
    NOVA_JITO = "nova_jito"        # Jito bundle sniping
    PUMP_GRADUATE = "pump_grad"    # Pump.fun graduates
    SENTIMENT = "sentiment"        # Social sentiment plays
    ARBITRAGE = "arbitrage"        # Cross-DEX arb
    SNIPER = "sniper"             # New token sniping
    SCALPER = "scalper"           # Quick in-out scalps


class AgentStatus(Enum):
    """Agent lifecycle states"""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    PAUSED = "paused"
    COOLDOWN = "cooldown"
    TERMINATED = "terminated"


@dataclass
class AgentConfig:
    """Configuration for a trading agent"""
    strategy: AgentStrategy
    min_trade_sol: float = 0.01
    max_trade_sol: float = 0.05
    max_positions: int = 3
    stop_loss_pct: float = 15.0
    take_profit_pct: float = 50.0
    cooldown_after_loss_mins: int = 5
    max_daily_trades: int = 50
    sentiment_threshold: float = 2.0
    rug_score_max: float = 0.3


@dataclass
class SwarmAgent:
    """Individual AI trading agent in the swarm"""
    agent_id: str
    name: str
    strategy: AgentStrategy
    config: AgentConfig
    status: AgentStatus = AgentStatus.INITIALIZING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Performance tracking
    allocated_capital: float = 0.0
    current_capital: float = 0.0
    total_pnl: float = 0.0
    trades_today: int = 0
    wins: int = 0
    losses: int = 0
    
    # Position tracking
    open_positions: List[dict] = field(default_factory=list)
    
    # Timing
    last_trade_at: Optional[datetime] = None
    cooldown_until: Optional[datetime] = None
    
    @property
    def win_rate(self) -> float:
        total = self.wins + self.losses
        return self.wins / total if total > 0 else 0.0
    
    @property
    def roi_pct(self) -> float:
        if self.allocated_capital <= 0:
            return 0.0
        return (self.total_pnl / self.allocated_capital) * 100
    
    @property
    def is_active(self) -> bool:
        if self.status != AgentStatus.ACTIVE:
            return False
        if self.cooldown_until and datetime.now(timezone.utc) < self.cooldown_until:
            return False
        return True
    
    def can_trade(self) -> bool:
        """Check if agent can execute a trade"""
        if not self.is_active:
            return False
        if self.trades_today >= self.config.max_daily_trades:
            return False
        if len(self.open_positions) >= self.config.max_positions:
            return False
        if self.current_capital < self.config.min_trade_sol:
            return False
        return True


class AgentSpawner:
    """
    Spawns and manages up to 100 AI trading agents.
    
    Features:
    - Automatic agent creation based on treasury funding
    - Strategy diversification
    - Performance-based capital allocation
    - Underperformer termination
    - Dynamic scaling based on fee income
    """
    
    MAX_AGENTS = 100
    
    def __init__(self):
        self.agents: Dict[str, SwarmAgent] = {}
        self.treasury = get_treasury_agent()
        self.fee_collector = get_fee_collector()
        
        # Strategy distribution targets (will auto-balance)
        self.strategy_targets = {
            AgentStrategy.MOMENTUM: 15,
            AgentStrategy.GMGN_AI: 10,
            AgentStrategy.AXIOM_MIGRATION: 10,
            AgentStrategy.WHALE_COPY: 10,
            AgentStrategy.NOVA_JITO: 15,
            AgentStrategy.PUMP_GRADUATE: 15,
            AgentStrategy.SENTIMENT: 5,
            AgentStrategy.ARBITRAGE: 5,
            AgentStrategy.SNIPER: 10,
            AgentStrategy.SCALPER: 5,
        }
        
        # Agent name prefixes by strategy
        self.name_prefixes = {
            AgentStrategy.MOMENTUM: ["Surge", "Wave", "Thrust", "Rocket"],
            AgentStrategy.GMGN_AI: ["Oracle", "Prophet", "Sage", "Seer"],
            AgentStrategy.AXIOM_MIGRATION: ["Bridge", "Migrate", "Cross", "Leap"],
            AgentStrategy.WHALE_COPY: ["Shadow", "Mirror", "Echo", "Follow"],
            AgentStrategy.NOVA_JITO: ["Flash", "Bolt", "Strike", "Zap"],
            AgentStrategy.PUMP_GRADUATE: ["Scholar", "Graduate", "Alumni", "Elite"],
            AgentStrategy.SENTIMENT: ["Pulse", "Vibe", "Mood", "Feel"],
            AgentStrategy.ARBITRAGE: ["Arb", "Gap", "Spread", "Delta"],
            AgentStrategy.SNIPER: ["Scope", "Target", "Aim", "Lock"],
            AgentStrategy.SCALPER: ["Quick", "Swift", "Rapid", "Blink"],
        }
        
    def _generate_agent_name(self, strategy: AgentStrategy) -> str:
        """Generate a unique agent name"""
        prefix = random.choice(self.name_prefixes[strategy])
        number = len([a for a in self.agents.values() if a.strategy == strategy]) + 1
        return f"{prefix}-{number:03d}"
    
    async def spawn_agent(
        self,
        strategy: AgentStrategy,
        initial_capital: float = 0.05,
        config: Optional[AgentConfig] = None
    ) -> Optional[SwarmAgent]:
        """
        Spawn a new trading agent.
        
        Args:
            strategy: Trading strategy for the agent
            initial_capital: Starting capital in SOL
            config: Optional custom configuration
            
        Returns:
            SwarmAgent if successful, None if at capacity or insufficient funds
        """
        # Check capacity
        if len(self.agents) >= self.MAX_AGENTS:
            logger.warning(f"Cannot spawn agent: at max capacity ({self.MAX_AGENTS})")
            return None
        
        # Generate identifiers
        agent_id = f"agent_{uuid.uuid4().hex[:8]}"
        name = self._generate_agent_name(strategy)
        
        # Create config if not provided
        if config is None:
            config = AgentConfig(strategy=strategy)
        
        # Create the agent
        agent = SwarmAgent(
            agent_id=agent_id,
            name=name,
            strategy=strategy,
            config=config
        )
        
        # Request capital allocation from treasury
        allocation = await self.treasury.allocate_to_agent(
            agent_id=agent_id,
            agent_type=strategy.value,
            amount_sol=initial_capital
        )
        
        if allocation is None:
            logger.warning(f"Failed to allocate capital for {name}")
            return None
        
        agent.allocated_capital = initial_capital
        agent.current_capital = initial_capital
        agent.status = AgentStatus.ACTIVE
        
        self.agents[agent_id] = agent
        
        logger.info(f"Spawned {strategy.value} agent: {name} with {initial_capital} SOL")
        
        return agent
    
    async def spawn_swarm(self, total_capital: float) -> List[SwarmAgent]:
        """
        Spawn a diversified swarm of agents based on strategy targets.
        
        Args:
            total_capital: Total SOL to distribute across agents
            
        Returns:
            List of spawned agents
        """
        spawned = []
        
        # Calculate per-agent allocation
        total_target_agents = sum(self.strategy_targets.values())
        per_agent = total_capital / total_target_agents
        
        for strategy, target_count in self.strategy_targets.items():
            # How many of this strategy do we need?
            current_count = len([
                a for a in self.agents.values() 
                if a.strategy == strategy and a.status == AgentStatus.ACTIVE
            ])
            
            needed = target_count - current_count
            
            for _ in range(needed):
                if len(self.agents) >= self.MAX_AGENTS:
                    break
                    
                agent = await self.spawn_agent(strategy, per_agent)
                if agent:
                    spawned.append(agent)
        
        logger.info(f"Spawned {len(spawned)} agents across {len(self.strategy_targets)} strategies")
        return spawned
    
    async def auto_scale(self):
        """
        Automatically scale agent count based on available treasury capital.
        Called periodically to adjust swarm size.
        """
        await self.treasury.sync_from_fees()
        
        available = self.treasury.state.available_capital
        min_per_agent = 0.02  # Minimum SOL per agent
        
        # Calculate how many new agents we can afford
        affordable = int(available / min_per_agent)
        current = len([a for a in self.agents.values() if a.status == AgentStatus.ACTIVE])
        headroom = self.MAX_AGENTS - current
        
        to_spawn = min(affordable, headroom, 10)  # Max 10 at a time
        
        if to_spawn > 0:
            # Spawn in underrepresented strategies
            strategy_counts = {}
            for agent in self.agents.values():
                if agent.status == AgentStatus.ACTIVE:
                    strategy_counts[agent.strategy] = strategy_counts.get(agent.strategy, 0) + 1
            
            for _ in range(to_spawn):
                # Find most underrepresented strategy
                best_strategy = None
                best_deficit = -1
                
                for strategy, target in self.strategy_targets.items():
                    current = strategy_counts.get(strategy, 0)
                    deficit = target - current
                    if deficit > best_deficit:
                        best_deficit = deficit
                        best_strategy = strategy
                
                if best_strategy and best_deficit > 0:
                    agent = await self.spawn_agent(best_strategy, min_per_agent)
                    if agent:
                        strategy_counts[best_strategy] = strategy_counts.get(best_strategy, 0) + 1
        
        logger.info(f"Auto-scale complete: {current + to_spawn} agents active")
    
    async def cull_underperformers(self, roi_threshold: float = -20.0):
        """
        Terminate agents that are significantly underperforming.
        Reclaims their capital for better-performing agents.
        """
        terminated = []
        
        for agent in list(self.agents.values()):
            if agent.status != AgentStatus.ACTIVE:
                continue
                
            # Check ROI threshold
            if agent.roi_pct < roi_threshold and agent.trades_today >= 5:
                agent.status = AgentStatus.TERMINATED
                
                # Return capital to treasury
                self.treasury.state.available_capital += agent.current_capital
                self.treasury.state.allocated_capital -= agent.current_capital
                
                terminated.append(agent)
                logger.info(f"Terminated underperformer: {agent.name} (ROI: {agent.roi_pct:.1f}%)")
        
        return terminated
    
    def get_agent(self, agent_id: str) -> Optional[SwarmAgent]:
        """Get an agent by ID"""
        return self.agents.get(agent_id)
    
    def get_active_agents(self) -> List[SwarmAgent]:
        """Get all active agents"""
        return [a for a in self.agents.values() if a.status == AgentStatus.ACTIVE]
    
    def get_agents_by_strategy(self, strategy: AgentStrategy) -> List[SwarmAgent]:
        """Get all agents of a specific strategy"""
        return [a for a in self.agents.values() if a.strategy == strategy]
    
    def get_swarm_status(self) -> dict:
        """Get comprehensive swarm status"""
        active = self.get_active_agents()
        
        strategy_breakdown = {}
        for strategy in AgentStrategy:
            agents = [a for a in active if a.strategy == strategy]
            strategy_breakdown[strategy.value] = {
                "count": len(agents),
                "target": self.strategy_targets.get(strategy, 0),
                "total_capital": sum(a.current_capital for a in agents),
                "total_pnl": sum(a.total_pnl for a in agents),
                "avg_win_rate": sum(a.win_rate for a in agents) / max(len(agents), 1)
            }
        
        return {
            "total_agents": len(self.agents),
            "active_agents": len(active),
            "max_agents": self.MAX_AGENTS,
            "capacity_pct": (len(active) / self.MAX_AGENTS) * 100,
            "total_capital": sum(a.current_capital for a in active),
            "total_pnl": sum(a.total_pnl for a in active),
            "total_trades_today": sum(a.trades_today for a in active),
            "strategy_breakdown": strategy_breakdown,
            "top_performers": sorted(
                [{"name": a.name, "strategy": a.strategy.value, "roi": a.roi_pct, "pnl": a.total_pnl} 
                 for a in active],
                key=lambda x: x["roi"],
                reverse=True
            )[:10]
        }


# Global instance
_spawner: Optional[AgentSpawner] = None


def get_agent_spawner() -> AgentSpawner:
    """Get or create the global agent spawner"""
    global _spawner
    if _spawner is None:
        _spawner = AgentSpawner()
    return _spawner
