"""
Agent Spawner - Swarm Management System
Spawns, monitors, and manages up to 100 trading agents.
"""

import asyncio
import uuid
import logging
import random
from datetime import datetime, timezone
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from src.constants import Strategy, SWARM as SwarmConfig
from src.agents.treasury_agent import get_treasury_agent

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent lifecycle states"""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    PAUSED = "paused"
    COOLDOWN = "cooldown"
    TERMINATED = "terminated"


@dataclass
class SwarmAgent:
    """Individual AI trading agent"""
    agent_id: str
    name: str
    strategy: Strategy
    status: AgentStatus = AgentStatus.INITIALIZING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Capital
    allocated_capital: float = 0.0
    current_capital: float = 0.0
    
    # Performance
    total_pnl: float = 0.0
    trades_today: int = 0
    wins: int = 0
    losses: int = 0
    
    # Timing
    last_trade_at: Optional[datetime] = None
    cooldown_until: Optional[datetime] = None
    
    @property
    def win_rate(self) -> float:
        total = self.wins + self.losses
        return (self.wins / total * 100) if total > 0 else 0.0
    
    @property
    def roi_pct(self) -> float:
        if self.allocated_capital <= 0:
            return 0.0
        return (self.total_pnl / self.allocated_capital) * 100


class AgentSpawner:
    """
    Manages the swarm of trading agents.
    
    Features:
    - Spawn agents with specific strategies
    - Auto-scale based on capital availability
    - Monitor agent performance
    - Terminate underperformers
    - Distribute capital from treasury
    """
    
    # Agent name prefixes by strategy
    STRATEGY_NAMES = {
        Strategy.MOMENTUM: ["Swift", "Flash", "Bolt", "Rocket", "Turbo"],
        Strategy.PUMP_GRADUATE: ["Graduate", "Scholar", "Elite", "Prime", "Alpha"],
        Strategy.SNIPER: ["Hawk", "Eagle", "Falcon", "Viper", "Strike"],
        Strategy.WHALE_COPY: ["Orca", "Whale", "Leviathan", "Titan", "Giant"],
        Strategy.SENTIMENT: ["Pulse", "Vibe", "Mood", "Trend", "Wave"],
        Strategy.GMGN_AI: ["Neural", "Synth", "Logic", "Matrix", "Cortex"],
        Strategy.AXIOM_MIGRATION: ["Bridge", "Portal", "Gateway", "Transit", "Flux"],
        Strategy.NOVA_JITO: ["Nova", "Star", "Comet", "Meteor", "Blaze"],
        Strategy.ARBITRAGE: ["Arbitron", "Balance", "Delta", "Hedge", "Spread"],
        Strategy.SCALPER: ["Quick", "Rapid", "Micro", "Nano", "Tick"],
    }
    
    def __init__(self):
        self._running = False
        self.agents: Dict[str, SwarmAgent] = {}
        self.agent_counter = 0
        
        # Configuration
        self.max_agents = SwarmConfig.MAX_AGENTS
        self.min_agents = SwarmConfig.MIN_AGENTS
        self.capital_per_agent = SwarmConfig.CAPITAL_PER_AGENT_SOL
    
    async def start(self):
        """Initialize the spawner"""
        self._running = True
        logger.info(f"🐝 Agent Spawner initialized (max: {self.max_agents} agents)")
    
    async def stop(self):
        """Shutdown all agents"""
        self._running = False
        for agent in self.agents.values():
            agent.status = AgentStatus.TERMINATED
        logger.info("Agent Spawner stopped")
    
    # =========================================================================
    # SPAWNING
    # =========================================================================
    
    async def spawn_agent(
        self,
        strategy: Strategy,
        initial_capital: Optional[float] = None
    ) -> Optional[SwarmAgent]:
        """
        Spawn a new trading agent
        """
        if len(self.agents) >= self.max_agents:
            logger.warning(f"Max agents ({self.max_agents}) reached")
            return None
        
        # Generate unique ID and name
        self.agent_counter += 1
        agent_id = f"agent_{uuid.uuid4().hex[:8]}"
        
        names = self.STRATEGY_NAMES.get(strategy, ["Agent"])
        name = f"{random.choice(names)}-{self.agent_counter:03d}"
        
        # Create agent
        agent = SwarmAgent(
            agent_id=agent_id,
            name=name,
            strategy=strategy
        )
        
        # Allocate capital from treasury
        capital = initial_capital or self.capital_per_agent
        treasury = get_treasury_agent()
        
        allocation = await treasury.allocate_to_agent(
            agent_id=agent_id,
            agent_type=strategy.value,
            amount_sol=capital
        )
        
        if allocation:
            agent.allocated_capital = capital
            agent.current_capital = capital
        else:
            # Try with available treasury balance
            if treasury.bot_trading_balance > 0.01:
                capital = min(capital, treasury.bot_trading_balance)
                allocation = await treasury.allocate_to_agent(
                    agent_id=agent_id,
                    agent_type=strategy.value,
                    amount_sol=capital
                )
                if allocation:
                    agent.allocated_capital = capital
                    agent.current_capital = capital
        
        # Register agent
        self.agents[agent_id] = agent
        agent.status = AgentStatus.ACTIVE
        
        logger.info(f"🐝 Spawned: {name} ({strategy.value}) with {agent.allocated_capital:.4f} SOL")
        
        return agent
    
    async def spawn_balanced_swarm(self, target_count: int = 10) -> List[SwarmAgent]:
        """
        Spawn a balanced swarm based on strategy weights
        """
        spawned = []
        
        # Calculate agents per strategy
        total_weight = sum(SwarmConfig.STRATEGY_WEIGHTS.values())
        
        for strategy, weight in SwarmConfig.STRATEGY_WEIGHTS.items():
            count = max(1, int(target_count * weight / total_weight))
            
            for _ in range(count):
                if len(self.agents) >= target_count:
                    break
                
                agent = await self.spawn_agent(strategy)
                if agent:
                    spawned.append(agent)
        
        logger.info(f"🐝 Spawned balanced swarm: {len(spawned)} agents")
        
        return spawned
    
    # =========================================================================
    # MANAGEMENT
    # =========================================================================
    
    async def terminate_agent(self, agent_id: str) -> bool:
        """
        Terminate an agent and return capital to treasury
        """
        if agent_id not in self.agents:
            return False
        
        agent = self.agents[agent_id]
        agent.status = AgentStatus.TERMINATED
        
        # Return capital to treasury
        if agent.current_capital > 0:
            treasury = get_treasury_agent()
            await treasury.recall_from_agent(agent_id, agent.current_capital)
        
        del self.agents[agent_id]
        
        logger.info(f"💀 Terminated: {agent.name} (PnL: {agent.total_pnl:.4f} SOL)")
        
        return True
    
    async def pause_agent(self, agent_id: str) -> bool:
        """Pause an agent"""
        if agent_id not in self.agents:
            return False
        
        self.agents[agent_id].status = AgentStatus.PAUSED
        return True
    
    async def resume_agent(self, agent_id: str) -> bool:
        """Resume a paused agent"""
        if agent_id not in self.agents:
            return False
        
        self.agents[agent_id].status = AgentStatus.ACTIVE
        return True
    
    def get_agent(self, agent_id: str) -> Optional[SwarmAgent]:
        """Get agent by ID"""
        return self.agents.get(agent_id)
    
    def get_active_agents(self) -> List[SwarmAgent]:
        """Get all active agents"""
        return [a for a in self.agents.values() if a.status == AgentStatus.ACTIVE]
    
    def get_agents_by_strategy(self, strategy: Strategy) -> List[SwarmAgent]:
        """Get agents using a specific strategy"""
        return [a for a in self.agents.values() if a.strategy == strategy]
    
    # =========================================================================
    # PERFORMANCE TRACKING
    # =========================================================================
    
    async def record_trade_result(
        self,
        agent_id: str,
        pnl: float,
        is_win: bool
    ):
        """
        Record a trade result for an agent
        """
        if agent_id not in self.agents:
            return
        
        agent = self.agents[agent_id]
        agent.total_pnl += pnl
        agent.current_capital += pnl
        agent.trades_today += 1
        agent.last_trade_at = datetime.now(timezone.utc)
        
        if is_win:
            agent.wins += 1
        else:
            agent.losses += 1
            
            # Cooldown after consecutive losses
            if agent.losses > 0 and agent.losses % 3 == 0:
                from datetime import timedelta
                agent.status = AgentStatus.COOLDOWN
                agent.cooldown_until = datetime.now(timezone.utc) + timedelta(minutes=5)
        
        # Update treasury
        treasury = get_treasury_agent()
        await treasury.update_agent_pnl(
            agent_id=agent_id,
            pnl=pnl,
            trades=1,
            wins=1 if is_win else 0
        )
    
    async def prune_underperformers(self, min_roi: float = -20.0):
        """
        Terminate agents with poor performance
        """
        to_terminate = []
        
        for agent in self.agents.values():
            if agent.roi_pct < min_roi and agent.trades_today >= 5:
                to_terminate.append(agent.agent_id)
        
        for agent_id in to_terminate:
            await self.terminate_agent(agent_id)
        
        if to_terminate:
            logger.info(f"🧹 Pruned {len(to_terminate)} underperforming agents")
    
    # =========================================================================
    # AUTO-SCALING
    # =========================================================================
    
    async def auto_scale(self):
        """
        Auto-scale the swarm based on treasury balance
        """
        treasury = get_treasury_agent()
        available = treasury.bot_trading_balance
        current_count = len(self.agents)
        
        # Scale up if capital available
        if available >= self.capital_per_agent * 2 and current_count < self.max_agents:
            agents_to_spawn = min(
                int(available / self.capital_per_agent),
                self.max_agents - current_count,
                5  # Max 5 at a time
            )
            
            if agents_to_spawn > 0:
                # Pick strategies for new agents
                strategies = list(Strategy)
                for _ in range(agents_to_spawn):
                    strategy = random.choice(strategies)
                    await self.spawn_agent(strategy)
        
        # Scale down if losses accumulating
        total_pnl = sum(a.total_pnl for a in self.agents.values())
        if total_pnl < -0.1 and current_count > self.min_agents:
            await self.prune_underperformers()
    
    # =========================================================================
    # STATISTICS
    # =========================================================================
    
    def get_swarm_stats(self) -> Dict:
        """
        Get overall swarm statistics
        """
        agents = list(self.agents.values())
        
        if not agents:
            return {
                "total_agents": 0,
                "active_agents": 0,
                "total_capital": 0,
                "total_pnl": 0
            }
        
        active = [a for a in agents if a.status == AgentStatus.ACTIVE]
        total_capital = sum(a.current_capital for a in agents)
        total_pnl = sum(a.total_pnl for a in agents)
        total_trades = sum(a.trades_today for a in agents)
        total_wins = sum(a.wins for a in agents)
        
        return {
            "total_agents": len(agents),
            "active_agents": len(active),
            "paused_agents": len([a for a in agents if a.status == AgentStatus.PAUSED]),
            "total_capital": total_capital,
            "total_pnl": total_pnl,
            "total_trades": total_trades,
            "overall_win_rate": (total_wins / total_trades * 100) if total_trades > 0 else 0,
            "best_agent": max(agents, key=lambda a: a.total_pnl).name if agents else None,
            "worst_agent": min(agents, key=lambda a: a.total_pnl).name if agents else None,
        }
    
    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """
        Get top performing agents
        """
        agents = sorted(self.agents.values(), key=lambda a: a.total_pnl, reverse=True)
        
        return [
            {
                "rank": i + 1,
                "name": a.name,
                "strategy": a.strategy.value,
                "pnl": a.total_pnl,
                "roi": a.roi_pct,
                "win_rate": a.win_rate,
                "trades": a.trades_today,
                "status": a.status.value
            }
            for i, a in enumerate(agents[:limit])
        ]


# Singleton instance
_spawner: Optional[AgentSpawner] = None


def get_agent_spawner() -> AgentSpawner:
    """Get or create the agent spawner singleton"""
    global _spawner
    if _spawner is None:
        _spawner = AgentSpawner()
    return _spawner
