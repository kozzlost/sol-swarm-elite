"""
Agent Integration Hooks
Integrates fee collection with existing swarm agents.

Add these hooks to your existing agent code to enable automatic fee routing.
"""

import asyncio
from functools import wraps
from typing import Callable, Awaitable, Any, Optional
import logging

from src.tokenomics.fee_collector import (
    get_fee_collector,
    collect_snipe_fee,
    collect_buy_fee,
    collect_sell_fee,
    collect_arb_fee,
    TradeType
)
from src.tokenomics.fee_router import get_fee_router, init_fee_router
from src.agents.treasury_agent import get_treasury_agent

logger = logging.getLogger(__name__)


# ============================================================
# INTEGRATION HOOKS - Add to your existing agents
# ============================================================

class SniperAgentHooks:
    """
    Hooks for the Sniper Agent.
    
    Add to your sniper_agent.py:
    
        from src.tokenomics.agent_hooks import SniperAgentHooks
        
        class SniperAgent:
            def __init__(self):
                self.hooks = SniperAgentHooks(agent_id="sniper_001")
            
            async def execute_snipe(self, token, amount_sol):
                # Your existing snipe logic
                result = await self._do_snipe(token, amount_sol)
                
                # Add fee hook
                await self.hooks.on_snipe_executed(
                    token_address=token,
                    amount_sol=amount_sol,
                    token_amount=result.tokens_received,
                    price=result.price,
                    tx_signature=result.signature
                )
                
                return result
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.fee_collector = get_fee_collector()
        
    async def on_snipe_executed(
        self,
        token_address: str,
        amount_sol: float,
        token_amount: float,
        price: float,
        tx_signature: str
    ):
        """Call after successful snipe"""
        await collect_snipe_fee(
            agent_id=self.agent_id,
            token_address=token_address,
            amount_sol=amount_sol,
            token_amount=token_amount,
            price=price,
            tx_signature=tx_signature
        )
        logger.info(f"[{self.agent_id}] Snipe fee collected: {amount_sol * 0.02:.6f} SOL")


class ArbiterAgentHooks:
    """
    Hooks for the Arbiter Agent.
    
    Add to your arbiter_agent.py:
    
        from src.tokenomics.agent_hooks import ArbiterAgentHooks
        
        class ArbiterAgent:
            def __init__(self):
                self.hooks = ArbiterAgentHooks(agent_id="arbiter_001")
            
            async def execute_trade(self, decision):
                result = await self._execute(decision)
                
                if decision.action == "BUY":
                    await self.hooks.on_buy_executed(...)
                elif decision.action == "SELL":
                    await self.hooks.on_sell_executed(...)
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.fee_collector = get_fee_collector()
        
    async def on_buy_executed(
        self,
        token_address: str,
        amount_sol: float,
        token_amount: float,
        price: float,
        tx_signature: str
    ):
        """Call after buy execution"""
        await collect_buy_fee(
            agent_id=self.agent_id,
            agent_type="arbiter",
            token_address=token_address,
            amount_sol=amount_sol,
            token_amount=token_amount,
            price=price,
            tx_signature=tx_signature
        )
        
    async def on_sell_executed(
        self,
        token_address: str,
        amount_sol: float,
        token_amount: float,
        price: float,
        tx_signature: str,
        realized_pnl: float
    ):
        """Call after sell execution"""
        await collect_sell_fee(
            agent_id=self.agent_id,
            agent_type="arbiter",
            token_address=token_address,
            amount_sol=amount_sol,
            token_amount=token_amount,
            price=price,
            tx_signature=tx_signature,
            realized_pnl=realized_pnl
        )


class SellAgentHooks:
    """
    Hooks for the Sell Agent.
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.fee_collector = get_fee_collector()
        
    async def on_position_closed(
        self,
        token_address: str,
        amount_sol: float,
        token_amount: float,
        entry_price: float,
        exit_price: float,
        tx_signature: str
    ):
        """Call after position close"""
        pnl = (exit_price - entry_price) * token_amount
        
        await collect_sell_fee(
            agent_id=self.agent_id,
            agent_type="sell",
            token_address=token_address,
            amount_sol=amount_sol,
            token_amount=token_amount,
            price=exit_price,
            tx_signature=tx_signature,
            realized_pnl=pnl
        )


# ============================================================
# DECORATOR APPROACH - Wrap existing functions
# ============================================================

def with_fee_collection(agent_id: str, agent_type: str, trade_type: TradeType):
    """
    Decorator to automatically collect fees from trade functions.
    
    Usage:
        @with_fee_collection("sniper_001", "sniper", TradeType.SNIPE)
        async def execute_snipe(token_address, amount_sol, ...):
            # Your existing code
            return {
                "signature": tx_sig,
                "amount_sol": amount_sol,
                "token_amount": tokens,
                "price": price,
                "token_address": token_address
            }
    """
    def decorator(func: Callable[..., Awaitable[dict]]):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            if result and isinstance(result, dict):
                fee_collector = get_fee_collector()
                
                try:
                    await fee_collector.process_trade(
                        trade_id=f"{trade_type.value}_{result.get('signature', 'unknown')[:8]}",
                        agent_id=agent_id,
                        agent_type=agent_type,
                        trade_type=trade_type,
                        token_address=result.get("token_address", ""),
                        amount_sol=result.get("amount_sol", 0),
                        token_amount=result.get("token_amount", 0),
                        price=result.get("price", 0),
                        tx_signature=result.get("signature"),
                        pnl=result.get("pnl", 0)
                    )
                except Exception as e:
                    logger.error(f"Fee collection failed: {e}")
            
            return result
        
        return wrapper
    return decorator


# ============================================================
# QUICK INTEGRATION - Minimal code changes
# ============================================================

async def record_trade(
    agent_id: str,
    agent_type: str,
    action: str,  # "buy", "sell", "snipe"
    token_address: str,
    amount_sol: float,
    tx_signature: str,
    token_amount: float = 0,
    price: float = 0,
    pnl: float = 0
):
    """
    Simple function to record any trade and collect fees.
    
    Call this after ANY trade execution:
    
        # After your existing trade code:
        await record_trade(
            agent_id="my_agent",
            agent_type="sniper",
            action="snipe",
            token_address=mint,
            amount_sol=0.05,
            tx_signature=sig
        )
    """
    trade_type_map = {
        "buy": TradeType.BUY,
        "sell": TradeType.SELL,
        "snipe": TradeType.SNIPE,
        "arb": TradeType.ARB
    }
    
    trade_type = trade_type_map.get(action.lower(), TradeType.BUY)
    
    fee_collector = get_fee_collector()
    await fee_collector.process_trade(
        trade_id=f"{action}_{tx_signature[:8]}",
        agent_id=agent_id,
        agent_type=agent_type,
        trade_type=trade_type,
        token_address=token_address,
        amount_sol=amount_sol,
        token_amount=token_amount,
        price=price,
        tx_signature=tx_signature,
        pnl=pnl
    )


# ============================================================
# TREASURY INTEGRATION
# ============================================================

async def request_trading_capital(agent_id: str, agent_type: str, amount_sol: float) -> bool:
    """
    Request capital from treasury for an agent.
    
    Call when spawning new agents or when agents need more capital:
    
        if await request_trading_capital("agent_001", "sniper", 0.1):
            # Capital allocated, agent can trade
        else:
            # Insufficient treasury funds
    """
    treasury = get_treasury_agent()
    allocation = await treasury.allocate_to_agent(
        agent_id=agent_id,
        agent_type=agent_type,
        amount_sol=amount_sol
    )
    return allocation is not None


async def report_agent_pnl(agent_id: str, pnl: float, trades: int = 1, wins: int = 0):
    """
    Report agent performance to treasury.
    
    Call periodically or after trades:
    
        await report_agent_pnl("agent_001", pnl=0.005, trades=1, wins=1)
    """
    treasury = get_treasury_agent()
    await treasury.update_agent_performance(
        agent_id=agent_id,
        pnl_change=pnl,
        trades=trades,
        wins=wins
    )


# ============================================================
# EXAMPLE: Complete Integration
# ============================================================

"""
EXAMPLE: How to integrate with an existing sniper agent

# In your sniper_agent.py:

from src.tokenomics.agent_hooks import record_trade, request_trading_capital

class SniperAgent:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.capital = 0
    
    async def initialize(self):
        # Request starting capital from treasury
        if await request_trading_capital(self.agent_id, "sniper", 0.05):
            self.capital = 0.05
            print(f"Agent {self.agent_id} funded with 0.05 SOL")
        else:
            print("No capital available")
    
    async def snipe(self, token_mint: str, amount_sol: float):
        # Your existing snipe logic
        tx_sig = await self._execute_snipe(token_mint, amount_sol)
        
        # Record the trade (collects fees automatically)
        await record_trade(
            agent_id=self.agent_id,
            agent_type="sniper",
            action="snipe",
            token_address=token_mint,
            amount_sol=amount_sol,
            tx_signature=tx_sig
        )
        
        return tx_sig
"""
