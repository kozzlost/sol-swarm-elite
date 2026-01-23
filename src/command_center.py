"""
Swarm Elite Command Center
Central orchestration hub for the entire AI trading swarm.
"""

import asyncio
import os
from datetime import datetime, timezone
from typing import Optional
import logging

from src.tokenomics.agent_token import (
    TokenomicsConfig, 
    configure_token_manager, 
    get_token_manager
)
from src.tokenomics.fee_collector import get_fee_collector
from src.agents.treasury_agent import get_treasury_agent
from src.agents.agent_spawner import get_agent_spawner, AgentStrategy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CommandCenter:
    """
    The brain of SOL-SWARM Elite.
    
    Coordinates:
    - $AGENT token fee collection
    - Treasury management (25/25/25/25 split)
    - Agent spawning and lifecycle
    - Performance monitoring
    - Auto-scaling based on fee income
    """
    
    def __init__(self):
        self.started_at: Optional[datetime] = None
        self.is_running = False
        
        # Core components (lazy loaded)
        self._token_manager = None
        self._fee_collector = None
        self._treasury = None
        self._spawner = None
        
        # Background task handles
        self._auto_scale_task: Optional[asyncio.Task] = None
        self._cull_task: Optional[asyncio.Task] = None
        self._sync_task: Optional[asyncio.Task] = None
        
    def configure(self):
        """Load configuration from environment"""
        config = TokenomicsConfig(
            token_mint=os.getenv("AGENT_TOKEN_MINT", ""),
            transaction_fee_bps=int(os.getenv("AGENT_FEE_BPS", "200")),
            bot_trading_wallet=os.getenv("BOT_TRADING_WALLET", ""),
            infrastructure_wallet=os.getenv("INFRASTRUCTURE_WALLET", ""),
            development_wallet=os.getenv("DEVELOPMENT_WALLET", ""),
            builder_wallet=os.getenv("BUILDER_WALLET", ""),
            rpc_url=os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
        )
        
        configure_token_manager(config)
        logger.info("Command center configured")
        
    async def start(self, initial_capital: float = 0.0):
        """
        Start the command center and all subsystems.
        
        Args:
            initial_capital: Optional starting capital to seed the treasury
        """
        self.configure()
        
        self._token_manager = get_token_manager()
        self._fee_collector = get_fee_collector()
        self._treasury = get_treasury_agent()
        self._spawner = get_agent_spawner()
        
        # Connect to Solana
        await self._token_manager.connect()
        
        # If we have initial capital, spawn initial swarm
        if initial_capital > 0:
            # Manually add to treasury for bootstrapping
            self._treasury.state.available_capital = initial_capital
            
            # Spawn diversified swarm
            await self._spawner.spawn_swarm(initial_capital)
        
        # Start background tasks
        self._start_background_tasks()
        
        self.started_at = datetime.now(timezone.utc)
        self.is_running = True
        
        logger.info(f"Command center started with {len(self._spawner.get_active_agents())} agents")
        
    def _start_background_tasks(self):
        """Start periodic background tasks"""
        # Auto-scale every 5 minutes
        self._auto_scale_task = asyncio.create_task(self._auto_scale_loop())
        
        # Cull underperformers every 15 minutes
        self._cull_task = asyncio.create_task(self._cull_loop())
        
        # Sync fees every minute
        self._sync_task = asyncio.create_task(self._sync_loop())
        
    async def _auto_scale_loop(self):
        """Background task: auto-scale agent count"""
        while self.is_running:
            try:
                await asyncio.sleep(300)  # 5 minutes
                if os.getenv("AUTO_SCALE_ENABLED", "true").lower() == "true":
                    await self._spawner.auto_scale()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Auto-scale error: {e}")
                
    async def _cull_loop(self):
        """Background task: cull underperforming agents"""
        while self.is_running:
            try:
                await asyncio.sleep(900)  # 15 minutes
                if os.getenv("CULL_UNDERPERFORMERS", "true").lower() == "true":
                    await self._spawner.cull_underperformers()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cull error: {e}")
                
    async def _sync_loop(self):
        """Background task: sync fees to treasury"""
        while self.is_running:
            try:
                await asyncio.sleep(60)  # 1 minute
                await self._treasury.sync_from_fees()
                await self._treasury.auto_allocate_new_capital()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Sync error: {e}")
    
    async def stop(self):
        """Gracefully stop the command center"""
        self.is_running = False
        
        # Cancel background tasks
        for task in [self._auto_scale_task, self._cull_task, self._sync_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Disconnect from Solana
        if self._token_manager:
            await self._token_manager.disconnect()
            
        logger.info("Command center stopped")
    
    def get_full_status(self) -> dict:
        """Get comprehensive system status"""
        uptime = None
        if self.started_at:
            uptime = (datetime.now(timezone.utc) - self.started_at).total_seconds()
        
        return {
            "command_center": {
                "is_running": self.is_running,
                "started_at": self.started_at.isoformat() if self.started_at else None,
                "uptime_seconds": uptime
            },
            "tokenomics": self._token_manager.get_treasury_status() if self._token_manager else {},
            "flywheel": self._token_manager.get_flywheel_metrics() if self._token_manager else {},
            "treasury": self._treasury.get_status_report() if self._treasury else {},
            "swarm": self._spawner.get_swarm_status() if self._spawner else {},
            "fee_stats": self._fee_collector.get_stats() if self._fee_collector else {},
            "recent_trades": self._fee_collector.get_recent_trades(20) if self._fee_collector else []
        }
    
    async def manual_spawn(self, strategy: str, capital: float) -> dict:
        """Manually spawn an agent"""
        try:
            strat = AgentStrategy(strategy)
        except ValueError:
            return {"error": f"Unknown strategy: {strategy}"}
        
        agent = await self._spawner.spawn_agent(strat, capital)
        if agent:
            return {"success": True, "agent_id": agent.agent_id, "name": agent.name}
        return {"error": "Failed to spawn agent (check capacity/capital)"}
    
    async def rebalance_treasury(self):
        """Manually trigger treasury rebalance"""
        await self._treasury.rebalance()
        return {"success": True}


# Global instance
_command_center: Optional[CommandCenter] = None


def get_command_center() -> CommandCenter:
    """Get or create the global command center"""
    global _command_center
    if _command_center is None:
        _command_center = CommandCenter()
    return _command_center


# CLI entry point
async def main():
    """Main entry point for running the command center"""
    from dotenv import load_dotenv
    load_dotenv()
    
    cc = get_command_center()
    
    # Get initial capital from env or use 0 (will bootstrap from fees)
    initial = float(os.getenv("INITIAL_CAPITAL_SOL", "0"))
    
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║   🤖 SOL-SWARM ELITE COMMAND CENTER 🤖                       ║
    ║                                                               ║
    ║   $AGENT Token Powered | 100 AI Agents | 25/25/25/25 Fees    ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    await cc.start(initial_capital=initial)
    
    print(f"\n✅ Command center active with {len(cc._spawner.get_active_agents())} agents")
    print(f"📊 Dashboard: http://localhost:{os.getenv('DASHBOARD_PORT', '8501')}")
    print(f"\nPress Ctrl+C to stop\n")
    
    try:
        while True:
            await asyncio.sleep(60)
            status = cc.get_full_status()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                  f"Agents: {status['swarm']['active_agents']} | "
                  f"Capital: {status['treasury']['summary']['total_capital']:.4f} SOL | "
                  f"Fees: {status['fee_stats']['total_fees_sol']:.6f} SOL")
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        await cc.stop()
        print("Goodbye! 👋")


if __name__ == "__main__":
    asyncio.run(main())
