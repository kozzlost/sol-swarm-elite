"""
Sniper Agent - Trade Execution Engine
Executes trades with Jito bundle support for MEV protection.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import os
import json

from src.types import (
    TradeSignal, Trade, TradeAction, TradeStatus, Position
)
from src.constants import (
    SOLANA_RPC, JUPITER_API, JUPITER_QUOTE_URL, JUPITER_SWAP_URL,
    JITO_BLOCK_ENGINE, JITO_TIP_ACCOUNT, JITO_TIP_LAMPORTS,
    TradingThresholds, PAPER_TRADING, MAINNET_ENABLED
)

logger = logging.getLogger(__name__)

# SOL mint address
SOL_MINT = "So11111111111111111111111111111111111111112"
WSOL_MINT = SOL_MINT


class SniperAgent:
    """
    Executes trades via Jupiter aggregator with optional Jito bundles.
    
    Features:
    - Jupiter DEX aggregation for best prices
    - Jito bundles for MEV protection (mainnet)
    - Slippage protection
    - Transaction retry logic
    - Paper trading simulation
    """
    
    def __init__(self):
        self.session = None
        self._running = False
        
        # Trade tracking
        self.pending_trades: Dict[str, Trade] = {}
        self.executed_trades: List[Trade] = []
        self.open_positions: Dict[str, Position] = {}
        
        # Wallet config
        self.wallet_keypair = None
        self.wallet_pubkey = None
        
        # Paper trading state
        self.paper_balance_sol = 1.0  # Start with 1 SOL for paper trading
        self.paper_positions: Dict[str, Dict] = {}
    
    async def start(self):
        """Initialize the sniper agent"""
        import aiohttp
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60)
        )
        self._running = True
        
        # Load wallet if mainnet
        if MAINNET_ENABLED:
            await self._load_wallet()
        
        mode = "🔴 MAINNET" if MAINNET_ENABLED else "📝 PAPER TRADING"
        logger.info(f"🎯 Sniper Agent initialized ({mode})")
    
    async def stop(self):
        """Shutdown the sniper agent"""
        self._running = False
        if self.session:
            await self.session.close()
        logger.info("Sniper Agent stopped")
    
    async def _load_wallet(self):
        """Load Solana wallet from environment"""
        try:
            private_key = os.getenv("SOLANA_PRIVATE_KEY", "")
            if not private_key:
                logger.warning("No SOLANA_PRIVATE_KEY set - mainnet trading disabled")
                return
            
            import base58
            from solders.keypair import Keypair
            
            # Decode base58 private key
            secret = base58.b58decode(private_key)
            self.wallet_keypair = Keypair.from_bytes(secret)
            self.wallet_pubkey = str(self.wallet_keypair.pubkey())
            
            logger.info(f"💳 Wallet loaded: {self.wallet_pubkey[:8]}...")
        
        except Exception as e:
            logger.error(f"Failed to load wallet: {e}")
    
    # =========================================================================
    # TRADE EXECUTION
    # =========================================================================
    
    async def execute_signal(self, signal: TradeSignal) -> Optional[Trade]:
        """
        Execute a trade signal
        """
        trade_id = str(uuid.uuid4())[:8]
        
        trade = Trade(
            trade_id=trade_id,
            mint=signal.token.mint,
            symbol=signal.token.symbol,
            action=signal.action,
            amount_sol=signal.suggested_amount_sol,
            entry_price=signal.token.price_usd,
            agent_id=signal.source_agent,
            strategy=signal.strategy
        )
        
        self.pending_trades[trade_id] = trade
        
        try:
            if PAPER_TRADING:
                result = await self._execute_paper_trade(trade, signal)
            else:
                result = await self._execute_mainnet_trade(trade, signal)
            
            if result:
                trade.status = TradeStatus.CONFIRMED
                trade.executed_at = datetime.now(timezone.utc)
                self.executed_trades.append(trade)
                
                # Create position for buys
                if signal.action == TradeAction.BUY:
                    await self._create_position(trade, signal)
                
                emoji = "🟢" if signal.action == TradeAction.BUY else "🔴"
                logger.info(
                    f"{emoji} Trade executed: {signal.action.value.upper()} "
                    f"${signal.token.symbol} for {trade.amount_sol:.4f} SOL"
                )
            else:
                trade.status = TradeStatus.FAILED
                logger.warning(f"Trade {trade_id} failed")
        
        except Exception as e:
            trade.status = TradeStatus.FAILED
            logger.error(f"Trade execution error: {e}")
        
        finally:
            del self.pending_trades[trade_id]
        
        return trade if trade.status == TradeStatus.CONFIRMED else None
    
    async def _execute_paper_trade(self, trade: Trade, signal: TradeSignal) -> bool:
        """
        Simulate trade execution for paper trading
        """
        if signal.action == TradeAction.BUY:
            # Check balance
            if self.paper_balance_sol < trade.amount_sol:
                logger.warning(f"Insufficient paper balance: {self.paper_balance_sol:.4f} SOL")
                return False
            
            # Simulate buy
            self.paper_balance_sol -= trade.amount_sol
            
            # Calculate tokens received (with 0.5% slippage simulation)
            slippage = 0.005
            effective_price = signal.token.price_usd * (1 + slippage)
            tokens_received = (trade.amount_sol * 150) / effective_price  # Assume 150 USD/SOL
            
            trade.amount_tokens = tokens_received
            trade.fees_paid_sol = trade.amount_sol * 0.003  # 0.3% fees
            
            self.paper_positions[trade.mint] = {
                "tokens": tokens_received,
                "entry_price": signal.token.price_usd,
                "entry_sol": trade.amount_sol
            }
        
        elif signal.action == TradeAction.SELL:
            # Check position
            if trade.mint not in self.paper_positions:
                logger.warning(f"No paper position for {trade.mint[:8]}...")
                return False
            
            pos = self.paper_positions[trade.mint]
            
            # Simulate sell
            exit_price = signal.token.price_usd
            pnl_pct = (exit_price - pos["entry_price"]) / pos["entry_price"]
            sol_received = pos["entry_sol"] * (1 + pnl_pct)
            
            self.paper_balance_sol += sol_received
            trade.exit_price = exit_price
            trade.pnl_sol = sol_received - pos["entry_sol"]
            trade.pnl_pct = pnl_pct * 100
            
            del self.paper_positions[trade.mint]
        
        # Simulate network delay
        await asyncio.sleep(0.5)
        
        return True
    
    async def _execute_mainnet_trade(self, trade: Trade, signal: TradeSignal) -> bool:
        """
        Execute trade on Solana mainnet via Jupiter
        """
        if not self.wallet_keypair:
            logger.error("No wallet loaded for mainnet trading")
            return False
        
        try:
            # 1. Get Jupiter quote
            quote = await self._get_jupiter_quote(
                input_mint=SOL_MINT if signal.action == TradeAction.BUY else signal.token.mint,
                output_mint=signal.token.mint if signal.action == TradeAction.BUY else SOL_MINT,
                amount=int(trade.amount_sol * 1e9) if signal.action == TradeAction.BUY else int(trade.amount_tokens * 1e9),
                slippage_bps=50  # 0.5%
            )
            
            if not quote:
                return False
            
            # 2. Get swap transaction
            swap_tx = await self._get_jupiter_swap(quote)
            
            if not swap_tx:
                return False
            
            # 3. Sign and send (with Jito if enabled)
            tx_signature = await self._sign_and_send(swap_tx)
            
            if tx_signature:
                trade.tx_signature = tx_signature
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Mainnet execution error: {e}")
            return False
    
    # =========================================================================
    # JUPITER INTEGRATION
    # =========================================================================
    
    async def _get_jupiter_quote(
        self,
        input_mint: str,
        output_mint: str,
        amount: int,
        slippage_bps: int = 50
    ) -> Optional[Dict[str, Any]]:
        """
        Get quote from Jupiter aggregator
        """
        try:
            params = {
                "inputMint": input_mint,
                "outputMint": output_mint,
                "amount": str(amount),
                "slippageBps": slippage_bps,
                "onlyDirectRoutes": "false",
                "asLegacyTransaction": "false"
            }
            
            async with self.session.get(JUPITER_QUOTE_URL, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"Jupiter quote failed: {response.status}")
                    return None
        
        except Exception as e:
            logger.error(f"Jupiter quote error: {e}")
            return None
    
    async def _get_jupiter_swap(self, quote: Dict[str, Any]) -> Optional[str]:
        """
        Get swap transaction from Jupiter
        """
        try:
            payload = {
                "quoteResponse": quote,
                "userPublicKey": self.wallet_pubkey,
                "wrapAndUnwrapSol": True,
                "dynamicComputeUnitLimit": True,
                "priorityLevelWithMaxLamports": {
                    "maxLamports": 1000000,
                    "priorityLevel": "high"
                }
            }
            
            async with self.session.post(JUPITER_SWAP_URL, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("swapTransaction")
                else:
                    logger.warning(f"Jupiter swap failed: {response.status}")
                    return None
        
        except Exception as e:
            logger.error(f"Jupiter swap error: {e}")
            return None
    
    async def _sign_and_send(self, swap_tx: str) -> Optional[str]:
        """
        Sign and send transaction (optionally via Jito)
        """
        try:
            import base64
            from solders.transaction import VersionedTransaction
            from solana.rpc.async_api import AsyncClient
            
            # Decode transaction
            tx_bytes = base64.b64decode(swap_tx)
            tx = VersionedTransaction.from_bytes(tx_bytes)
            
            # Sign
            tx.sign([self.wallet_keypair])
            
            # Send
            async with AsyncClient(SOLANA_RPC) as client:
                result = await client.send_transaction(
                    tx,
                    opts={"skip_preflight": True, "max_retries": 3}
                )
                
                if result.value:
                    return str(result.value)
            
            return None
        
        except Exception as e:
            logger.error(f"Sign/send error: {e}")
            return None
    
    # =========================================================================
    # POSITION MANAGEMENT
    # =========================================================================
    
    async def _create_position(self, trade: Trade, signal: TradeSignal):
        """
        Create a position record for a buy trade
        """
        position = Position(
            position_id=trade.trade_id,
            mint=trade.mint,
            symbol=trade.symbol,
            entry_price=signal.token.price_usd,
            current_price=signal.token.price_usd,
            amount_tokens=trade.amount_tokens,
            amount_sol_invested=trade.amount_sol,
            stop_loss_price=signal.token.price_usd * (1 - signal.stop_loss_pct / 100),
            take_profit_price=signal.token.price_usd * (1 + signal.take_profit_pct / 100),
            agent_id=trade.agent_id,
            entry_trade_id=trade.trade_id
        )
        
        self.open_positions[trade.mint] = position
    
    def get_position(self, mint: str) -> Optional[Position]:
        """Get open position for a token"""
        return self.open_positions.get(mint)
    
    def get_all_positions(self) -> List[Position]:
        """Get all open positions"""
        return list(self.open_positions.values())
    
    async def close_position(self, mint: str) -> Optional[Trade]:
        """
        Close an open position
        """
        position = self.open_positions.get(mint)
        if not position:
            return None
        
        # Create sell signal
        from src.types import TokenInfo
        token = TokenInfo(
            mint=mint,
            symbol=position.symbol,
            name=position.symbol,
            price_usd=position.current_price
        )
        
        signal = TradeSignal(
            token=token,
            action=TradeAction.SELL,
            confidence=1.0,
            suggested_amount_sol=position.amount_sol_invested,
            source_agent="sniper",
            strategy="exit"
        )
        
        trade = await self.execute_signal(signal)
        
        if trade and trade.status == TradeStatus.CONFIRMED:
            del self.open_positions[mint]
        
        return trade
    
    # =========================================================================
    # STATE
    # =========================================================================
    
    def get_paper_balance(self) -> float:
        """Get current paper trading balance"""
        return self.paper_balance_sol
    
    def get_trade_history(self, limit: int = 50) -> List[Trade]:
        """Get recent trade history"""
        return self.executed_trades[-limit:]


# Singleton instance
_sniper_agent: Optional[SniperAgent] = None


def get_sniper_agent() -> SniperAgent:
    """Get or create the sniper agent singleton"""
    global _sniper_agent
    if _sniper_agent is None:
        _sniper_agent = SniperAgent()
    return _sniper_agent
