"""
Fee Router - Routes trading fees to the 4 buckets on-chain.
This integrates with Jupiter/Raydium swaps to automatically split fees.
"""

import asyncio
import os
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime, timezone
import logging
import base58

from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import TransferParams, transfer
from solders.transaction import Transaction
from solders.message import Message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FeeRouterConfig:
    """Fee router configuration"""
    # Fee rate
    fee_bps: int = 200  # 2%
    
    # Distribution (must sum to 100)
    bot_trading_pct: int = 25
    infrastructure_pct: int = 25
    development_pct: int = 25
    builder_pct: int = 25
    
    # Wallets
    bot_trading_wallet: str = ""
    infrastructure_wallet: str = ""
    development_wallet: str = ""
    builder_wallet: str = ""
    
    # RPC
    rpc_url: str = "https://api.mainnet-beta.solana.com"
    
    # Minimum fee to route (avoid dust)
    min_fee_lamports: int = 10000  # 0.00001 SOL
    
    def validate(self):
        total = self.bot_trading_pct + self.infrastructure_pct + self.development_pct + self.builder_pct
        if total != 100:
            raise ValueError(f"Percentages must sum to 100, got {total}")
        
        for wallet in [self.bot_trading_wallet, self.infrastructure_wallet, 
                       self.development_wallet, self.builder_wallet]:
            if not wallet:
                raise ValueError("All 4 wallets must be configured")
        return True


class FeeRouter:
    """
    Routes fees from trades to the 4 distribution wallets.
    
    Integration points:
    - After Jupiter swap completion
    - After Raydium swap completion
    - After any trade execution
    
    The router:
    1. Calculates fee from trade amount
    2. Splits into 4 equal parts (25% each)
    3. Sends SOL to each wallet
    4. Logs the distribution
    """
    
    def __init__(self, config: FeeRouterConfig):
        self.config = config
        self.config.validate()
        self.client: Optional[AsyncClient] = None
        self.payer: Optional[Keypair] = None
        
        # Stats
        self.total_routed: int = 0  # lamports
        self.transactions: int = 0
        self.distribution_history: List[dict] = []
        
    async def connect(self, private_key: str):
        """Connect to Solana and load payer wallet"""
        self.client = AsyncClient(self.config.rpc_url, commitment=Confirmed)
        
        secret = base58.b58decode(private_key)
        self.payer = Keypair.from_bytes(secret)
        
        balance = await self.client.get_balance(self.payer.pubkey())
        logger.info(f"Fee router connected: {self.payer.pubkey()}")
        logger.info(f"Router balance: {balance.value / 1e9:.4f} SOL")
        
    async def disconnect(self):
        if self.client:
            await self.client.close()
    
    def calculate_fee(self, trade_amount_lamports: int) -> int:
        """Calculate fee from trade amount"""
        return int(trade_amount_lamports * self.config.fee_bps / 10000)
    
    def calculate_splits(self, total_fee_lamports: int) -> dict:
        """Calculate the 4-way split"""
        return {
            "bot_trading": int(total_fee_lamports * self.config.bot_trading_pct / 100),
            "infrastructure": int(total_fee_lamports * self.config.infrastructure_pct / 100),
            "development": int(total_fee_lamports * self.config.development_pct / 100),
            "builder": int(total_fee_lamports * self.config.builder_pct / 100)
        }
    
    async def route_fee(
        self,
        trade_amount_lamports: int,
        trade_signature: str,
        agent_id: str = "unknown"
    ) -> Optional[dict]:
        """
        Route fee from a trade to the 4 wallets.
        
        Args:
            trade_amount_lamports: Size of the trade in lamports
            trade_signature: Transaction signature of the trade
            agent_id: ID of the agent that made the trade
            
        Returns:
            Distribution record or None if below minimum
        """
        if not self.client or not self.payer:
            raise RuntimeError("Router not connected")
        
        # Calculate fee
        total_fee = self.calculate_fee(trade_amount_lamports)
        
        if total_fee < self.config.min_fee_lamports:
            logger.debug(f"Fee {total_fee} below minimum, skipping")
            return None
        
        # Calculate splits
        splits = self.calculate_splits(total_fee)
        
        # Build transfer instructions
        instructions = []
        
        wallet_map = {
            "bot_trading": self.config.bot_trading_wallet,
            "infrastructure": self.config.infrastructure_wallet,
            "development": self.config.development_wallet,
            "builder": self.config.builder_wallet
        }
        
        for bucket, amount in splits.items():
            if amount > 0:
                dest = Pubkey.from_string(wallet_map[bucket])
                ix = transfer(TransferParams(
                    from_pubkey=self.payer.pubkey(),
                    to_pubkey=dest,
                    lamports=amount
                ))
                instructions.append(ix)
        
        # Get recent blockhash
        recent = await self.client.get_latest_blockhash()
        blockhash = recent.value.blockhash
        
        # Build and sign transaction
        msg = Message.new_with_blockhash(
            instructions,
            self.payer.pubkey(),
            blockhash
        )
        tx = Transaction([self.payer], msg, blockhash)
        
        # Send transaction
        try:
            result = await self.client.send_transaction(tx)
            sig = str(result.value)
            
            # Record distribution
            record = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "trade_signature": trade_signature,
                "fee_signature": sig,
                "agent_id": agent_id,
                "trade_amount_lamports": trade_amount_lamports,
                "total_fee_lamports": total_fee,
                "splits": splits
            }
            
            self.distribution_history.append(record)
            self.total_routed += total_fee
            self.transactions += 1
            
            logger.info(
                f"Fee routed: {total_fee/1e9:.6f} SOL | "
                f"Tx: {sig[:8]}... | "
                f"Agent: {agent_id}"
            )
            
            return record
            
        except Exception as e:
            logger.error(f"Fee routing failed: {e}")
            return None
    
    async def route_fee_batch(
        self,
        trades: List[dict]
    ) -> List[dict]:
        """
        Route fees for multiple trades in batch.
        More efficient than individual routing.
        
        Args:
            trades: List of {amount_lamports, signature, agent_id}
            
        Returns:
            List of distribution records
        """
        results = []
        
        # Calculate total fees
        total_fee = sum(
            self.calculate_fee(t["amount_lamports"]) 
            for t in trades
        )
        
        if total_fee < self.config.min_fee_lamports:
            return results
        
        # Single distribution for batch
        splits = self.calculate_splits(total_fee)
        
        # Build transfer instructions
        instructions = []
        wallet_map = {
            "bot_trading": self.config.bot_trading_wallet,
            "infrastructure": self.config.infrastructure_wallet,
            "development": self.config.development_wallet,
            "builder": self.config.builder_wallet
        }
        
        for bucket, amount in splits.items():
            if amount > 0:
                dest = Pubkey.from_string(wallet_map[bucket])
                ix = transfer(TransferParams(
                    from_pubkey=self.payer.pubkey(),
                    to_pubkey=dest,
                    lamports=amount
                ))
                instructions.append(ix)
        
        # Send transaction
        try:
            recent = await self.client.get_latest_blockhash()
            blockhash = recent.value.blockhash
            
            msg = Message.new_with_blockhash(
                instructions,
                self.payer.pubkey(),
                blockhash
            )
            tx = Transaction([self.payer], msg, blockhash)
            result = await self.client.send_transaction(tx)
            sig = str(result.value)
            
            record = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "fee_signature": sig,
                "trade_count": len(trades),
                "total_fee_lamports": total_fee,
                "splits": splits
            }
            
            self.distribution_history.append(record)
            self.total_routed += total_fee
            self.transactions += 1
            
            results.append(record)
            
            logger.info(f"Batch fee routed: {total_fee/1e9:.6f} SOL for {len(trades)} trades")
            
        except Exception as e:
            logger.error(f"Batch fee routing failed: {e}")
        
        return results
    
    def get_stats(self) -> dict:
        """Get routing statistics"""
        return {
            "total_routed_sol": self.total_routed / 1e9,
            "total_routed_lamports": self.total_routed,
            "total_transactions": self.transactions,
            "distribution_breakdown": {
                "bot_trading": self.total_routed * self.config.bot_trading_pct / 100 / 1e9,
                "infrastructure": self.total_routed * self.config.infrastructure_pct / 100 / 1e9,
                "development": self.total_routed * self.config.development_pct / 100 / 1e9,
                "builder": self.total_routed * self.config.builder_pct / 100 / 1e9
            },
            "recent_distributions": self.distribution_history[-10:]
        }


# Global instance
_router: Optional[FeeRouter] = None


def get_fee_router() -> FeeRouter:
    """Get or create global fee router"""
    global _router
    if _router is None:
        config = FeeRouterConfig(
            bot_trading_wallet=os.getenv("BOT_TRADING_WALLET", ""),
            infrastructure_wallet=os.getenv("INFRASTRUCTURE_WALLET", ""),
            development_wallet=os.getenv("DEVELOPMENT_WALLET", ""),
            builder_wallet=os.getenv("BUILDER_WALLET", ""),
            rpc_url=os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
        )
        _router = FeeRouter(config)
    return _router


async def init_fee_router(private_key: str) -> FeeRouter:
    """Initialize and connect the fee router"""
    router = get_fee_router()
    await router.connect(private_key)
    return router


# Decorator for automatic fee routing
def with_fee_routing(func):
    """
    Decorator to automatically route fees after trade execution.
    
    Usage:
        @with_fee_routing
        async def execute_swap(amount_lamports, ...):
            # Do the swap
            return {"signature": "...", "amount": amount_lamports}
    """
    async def wrapper(*args, **kwargs):
        result = await func(*args, **kwargs)
        
        if result and "signature" in result and "amount" in result:
            router = get_fee_router()
            if router.client:
                await router.route_fee(
                    trade_amount_lamports=result["amount"],
                    trade_signature=result["signature"],
                    agent_id=kwargs.get("agent_id", "unknown")
                )
        
        return result
    
    return wrapper
