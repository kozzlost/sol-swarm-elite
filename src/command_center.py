"""
Command Center - Main Orchestration Hub
Coordinates all agents and manages the trading pipeline.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from src.constants import (
    PAPER_TRADING, MAINNET_ENABLED, TradingThresholds,
    Strategy, ACTIVE_STRATEGY, RISK_WARNING
)
from src.types import TokenInfo, TradeSignal, Trade, Position, SystemHealth
from src.agents import (
    get_scout_agent, get_sentiment_agent, get_arbiter_agent,
    get_sniper_agent, get_sell_agent, get_treasury_agent,
    get_agent_spawner
)

logger = logging.getLogger(__name__)

from src.agents.ceo_agent import CEOAgent

class CommandCenter:
    def __init__(self):
        self.ceo = CEOAgent()
        self.scout = ScoutAgent()
        self.sentiment = SentimentAgent()
        # ... other agents

    def process_signal(self, signal: TradeSignal):
        decision = self.ceo.allocate_resources(signal)
        if decision.action == "trade":
            # Delegate to other agents
            sentiment_score = self.sentiment.analyze(signal.token)
            arbiter_decision = self.arbiter.decide(signal, sentiment_score)
            if arbiter_decision.action == "buy":
                self.sniper.execute_trade(arbiter_decision)


@dataclass
class SystemState:
    """Current system state"""
    is_running: bool = False
    is_paused: bool = False
    mode: str = "paper"
    
    # Counters
    discovery_cycles: int = 0
    signals_generated: int = 0
    trades_executed: int = 0
    
    # Current state
    tokens_discovered: int = 0
    active_positions: int = 0
    pending_signals: int = 0
    
    # Timestamps
    started_at: Optional[datetime] = None
    last_discovery: Optional[datetime] = None
    last_trade: Optional[datetime] = None


class CommandCenter:
    """
    Central orchestration hub for SOL-SWARM Elite.
    
    Responsibilities:
    - Initialize and coordinate all agents
    - Run the main trading loop
    - Manage system state
    - Handle errors and recovery
    """
    
    def __init__(self):
        self.state = SystemState()
        
        # Agents (initialized lazily)
        self.scout = None
        self.sentiment = None
        self.arbiter = None
        self.sniper = None
        self.sell = None
        self.treasury = None
        self.spawner = None
        
        # Configuration
        self.discovery_interval_secs = 30
        self.position_check_interval_secs = 10
        
        # Data
        self.discovered_tokens: Dict[str, TokenInfo] = {}
        self.signal_queue: List[TradeSignal] = []
        
        # Tasks
        self._discovery_task = None
        self._monitoring_task = None
        self._main_loop_task = None
    
    # =========================================================================
    # LIFECYCLE
    # =========================================================================
    
    async def initialize(self):
        """
        Initialize all agents and prepare for trading
        """
        logger.info("=" * 60)
        logger.info("🚀 SOL-SWARM Elite Command Center")
        logger.info("=" * 60)
        
        if MAINNET_ENABLED:
            logger.warning(RISK_WARNING)
        
        # Initialize agents
        self.scout = get_scout_agent()
        self.sentiment = get_sentiment_agent()
        self.arbiter = get_arbiter_agent()
        self.sniper = get_sniper_agent()
        self.sell = get_sell_agent()
        self.treasury = get_treasury_agent()
        self.spawner = get_agent_spawner()
        
        # Start all agents
        await asyncio.gather(
            self.scout.start(),
            self.sentiment.start(),
            self.arbiter.start(),
            self.sniper.start(),
            self.sell.start(),
            self.treasury.start(),
            self.spawner.start(),
        )
        
        self.state.mode = "mainnet" if MAINNET_ENABLED else "paper"
        self.state.started_at = datetime.now(timezone.utc)
        
        logger.info(f"✅ All agents initialized ({self.state.mode} mode)")
        logger.info(f"📊 Strategy: {ACTIVE_STRATEGY.value}")
    
    async def shutdown(self):
        """
        Gracefully shutdown all agents
        """
        logger.info("Shutting down Command Center...")
        
        self.state.is_running = False
        
        # Cancel background tasks
        for task in [self._discovery_task, self._monitoring_task, self._main_loop_task]:
            if task:
                task.cancel()
        
        # Stop all agents
        if self.scout:
            await self.scout.stop()
        if self.sentiment:
            await self.sentiment.stop()
        if self.arbiter:
            await self.arbiter.stop()
        if self.sniper:
            await self.sniper.stop()
        if self.sell:
            await self.sell.stop()
        if self.treasury:
            await self.treasury.stop()
        if self.spawner:
            await self.spawner.stop()
        
        logger.info("✅ Command Center shutdown complete")
    
    # =========================================================================
    # MAIN LOOP
    # =========================================================================
    
    async def start(self):
        """
        Start the main trading loop
        """
        if self.state.is_running:
            logger.warning("Command Center already running")
            return
        
        await self.initialize()
        
        self.state.is_running = True
        
        # Start background tasks
        self._discovery_task = asyncio.create_task(self._discovery_loop())
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("🏁 Trading loop started")
    
    async def stop(self):
        """
        Stop the trading loop
        """
        self.state.is_running = False
        await self.shutdown()
    
    async def pause(self):
        """Pause trading"""
        self.state.is_paused = True
        logger.info("⏸️ Trading paused")
    
    async def resume(self):
        """Resume trading"""
        self.state.is_paused = False
        logger.info("▶️ Trading resumed")
    
    # =========================================================================
    # DISCOVERY LOOP
    # =========================================================================
    
    async def _discovery_loop(self):
        """
        Background task for token discovery
        """
        while self.state.is_running:
            try:
                if not self.state.is_paused:
                    await self.run_discovery_cycle()
                
                await asyncio.sleep(self.discovery_interval_secs)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Discovery loop error: {e}")
                await asyncio.sleep(5)
    
    async def run_discovery_cycle(self):
        """
        Run a single discovery cycle
        """
        self.state.discovery_cycles += 1
        self.state.last_discovery = datetime.now(timezone.utc)
        
        # 1. Discover and vet tokens
        safe_tokens = await self.scout.discover_and_vet(
            sources=["dexscreener", "pumpfun"],
            limit_per_source=10
        )
        
        if not safe_tokens:
            return
        
        self.state.tokens_discovered = len(safe_tokens)
        
        for token in safe_tokens:
            self.discovered_tokens[token.mint] = token
        
        # 2. Analyze sentiment
        sentiment_results = await self.sentiment.analyze_multiple(safe_tokens)
        
        # 3. Generate trading signals
        for token in safe_tokens:
            rug_check = self.scout.vetted_tokens.get(token.mint)
            sentiment = sentiment_results.get(token.mint)
            
            # Check if we already have a position
            existing_position = self.sniper.get_position(token.mint)
            
            signal = await self.arbiter.evaluate_and_signal(
                token=token,
                rug_check=rug_check,
                sentiment=sentiment,
                existing_position=existing_position
            )
            
            if signal:
                self.signal_queue.append(signal)
                self.state.signals_generated += 1
        
        # 4. Execute signals (if not paused)
        await self._process_signal_queue()
    
    # =========================================================================
    # SIGNAL PROCESSING
    # =========================================================================
    
    async def _process_signal_queue(self):
        """
        Process pending trade signals
        """
        if self.state.is_paused:
            return
        
        # Check position limits
        current_positions = len(self.sniper.get_all_positions())
        max_positions = TradingThresholds.MAX_CONCURRENT_POSITIONS
        
        while self.signal_queue and current_positions < max_positions:
            signal = self.signal_queue.pop(0)
            
            # Execute via sniper
            trade = await self.sniper.execute_signal(signal)
            
            if trade:
                self.state.trades_executed += 1
                self.state.last_trade = datetime.now(timezone.utc)
                
                # Collect fees (simulate for paper trading)
                await self.treasury.collect_fee(
                    trade_amount_sol=trade.amount_sol,
                    trade_id=trade.trade_id
                )
                
                current_positions = len(self.sniper.get_all_positions())
        
        self.state.pending_signals = len(self.signal_queue)
    
    # =========================================================================
    # POSITION MONITORING
    # =========================================================================
    
    async def _monitoring_loop(self):
        """
        Background task for position monitoring
        """
        while self.state.is_running:
            try:
                if not self.state.is_paused:
                    await self._check_positions()
                
                await asyncio.sleep(self.position_check_interval_secs)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(5)
    
    async def _check_positions(self):
        """
        Check all open positions and handle exits
        """
        positions = self.sniper.get_all_positions()
        
        if not positions:
            return
        
        self.state.active_positions = len(positions)
        
        # Get current prices for all positions
        current_prices = {}
        for position in positions:
            token = self.discovered_tokens.get(position.mint)
            if token:
                current_prices[position.mint] = token.price_usd
        
        # Check for exit signals
        exit_signals = await self.sell.check_positions(positions, current_prices)
        
        # Execute exits
        for signal in exit_signals:
            trade = await self.sniper.execute_signal(signal)
            
            if trade:
                self.state.trades_executed += 1
                
                # Record result for agent spawner
                is_win = trade.pnl_sol > 0
                await self.spawner.record_trade_result(
                    agent_id=trade.agent_id,
                    pnl=trade.pnl_sol,
                    is_win=is_win
                )
    
    # =========================================================================
    # MANUAL CONTROLS
    # =========================================================================
    
    async def force_sell_all(self):
        """
        Emergency: Sell all positions immediately
        """
        logger.warning("⚠️ Emergency sell all triggered")
        
        positions = self.sniper.get_all_positions()
        exit_signals = await self.sell.emergency_exit_all(positions)
        
        for signal in exit_signals:
            await self.sniper.execute_signal(signal)
    
    async def spawn_agents(self, count: int = 10):
        """
        Spawn a balanced swarm of agents
        """
        return await self.spawner.spawn_balanced_swarm(count)
    
    # =========================================================================
    # STATUS & REPORTING
    # =========================================================================
    
    def get_system_health(self) -> SystemHealth:
        """
        Get current system health status
        """
        return SystemHealth(
            is_healthy=self.state.is_running and not self.state.is_paused,
            rpc_connected=True,  # Would check actual connection
            dexscreener_ok=True,
            rugcheck_ok=True,
            active_agents=len(self.spawner.get_active_agents()) if self.spawner else 0,
            open_positions=self.state.active_positions,
            pending_signals=self.state.pending_signals
        )
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get all data needed for the dashboard
        """
        treasury_snapshot = self.treasury.get_snapshot() if self.treasury else None
        swarm_stats = self.spawner.get_swarm_stats() if self.spawner else {}
        
        return {
            "system": {
                "mode": self.state.mode,
                "is_running": self.state.is_running,
                "is_paused": self.state.is_paused,
                "uptime_secs": (datetime.now(timezone.utc) - self.state.started_at).total_seconds() if self.state.started_at else 0,
            },
            "stats": {
                "discovery_cycles": self.state.discovery_cycles,
                "tokens_discovered": self.state.tokens_discovered,
                "signals_generated": self.state.signals_generated,
                "trades_executed": self.state.trades_executed,
                "active_positions": self.state.active_positions,
            },
            "treasury": {
                "bot_trading": treasury_snapshot.bot_trading_balance if treasury_snapshot else 0,
                "infrastructure": treasury_snapshot.infrastructure_balance if treasury_snapshot else 0,
                "development": treasury_snapshot.development_balance if treasury_snapshot else 0,
                "builder": treasury_snapshot.builder_balance if treasury_snapshot else 0,
                "total_fees": treasury_snapshot.total_fees_collected if treasury_snapshot else 0,
            },
            "swarm": swarm_stats,
            "paper_balance": self.sniper.get_paper_balance() if self.sniper else 1.0,
            "positions": [
                {
                    "symbol": p.symbol,
                    "entry": p.entry_price,
                    "current": p.current_price,
                    "pnl_pct": p.unrealized_pnl_pct,
                    "pnl_sol": p.unrealized_pnl_sol,
                }
                for p in (self.sniper.get_all_positions() if self.sniper else [])
            ],
            "recent_trades": [
                {
                    "symbol": t.symbol,
                    "action": t.action.value,
                    "amount": t.amount_sol,
                    "pnl": t.pnl_sol,
                    "status": t.status.value,
                }
                for t in (self.sniper.get_trade_history(10) if self.sniper else [])
            ],
            "leaderboard": self.spawner.get_leaderboard(10) if self.spawner else [],
        }


# Singleton instance
_command_center: Optional[CommandCenter] = None


def get_command_center() -> CommandCenter:
    """Get or create the command center singleton"""
    global _command_center
    if _command_center is None:
        _command_center = CommandCenter()
    return _command_center
