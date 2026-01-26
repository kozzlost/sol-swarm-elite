"""
Sell Agent - Position Exit & Risk Management
Monitors positions and executes exits based on risk parameters.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict

from src.types import Position, TradeSignal, TradeAction, TokenInfo
from src.constants import TradingThresholds

logger = logging.getLogger(__name__)


class SellAgent:
    """
    Monitors open positions and triggers exits based on:
    - Stop loss
    - Take profit
    - Time-based expiry
    - Trailing stops
    - Sentiment reversal
    """
    
    def __init__(self):
        self._running = False
        self.exit_signals: List[TradeSignal] = []
        
        # Configuration
        self.check_interval_secs = 10
        self.position_timeout_mins = TradingThresholds.POSITION_TIMEOUT_MINS
    
    async def start(self):
        """Initialize the sell agent"""
        self._running = True
        logger.info("🔴 Sell Agent initialized")
    
    async def stop(self):
        """Shutdown the sell agent"""
        self._running = False
        logger.info("Sell Agent stopped")
    
    # =========================================================================
    # POSITION MONITORING
    # =========================================================================
    
    async def check_positions(
        self,
        positions: List[Position],
        current_prices: Dict[str, float]
    ) -> List[TradeSignal]:
        """
        Check all positions and generate exit signals where needed
        """
        exit_signals = []
        
        for position in positions:
            # Update current price
            current_price = current_prices.get(position.mint, position.current_price)
            position.update_pnl(current_price)
            
            # Check exit conditions
            signal = await self._evaluate_position(position)
            
            if signal:
                exit_signals.append(signal)
                self.exit_signals.append(signal)
        
        return exit_signals
    
    async def _evaluate_position(self, position: Position) -> Optional[TradeSignal]:
        """
        Evaluate a single position for exit conditions
        """
        reasons = []
        should_exit = False
        
        # 1. Stop Loss Check
        if position.current_price <= position.stop_loss_price:
            reasons.append(f"Stop loss hit: {position.unrealized_pnl_pct:.1f}%")
            should_exit = True
        
        # 2. Take Profit Check
        elif position.current_price >= position.take_profit_price:
            reasons.append(f"Take profit hit: {position.unrealized_pnl_pct:.1f}%")
            should_exit = True
        
        # 3. Time-based Expiry
        position_age = datetime.now(timezone.utc) - position.opened_at
        if position_age > timedelta(minutes=self.position_timeout_mins):
            reasons.append(f"Position timeout ({self.position_timeout_mins}m)")
            should_exit = True
        
        # 4. Severe Loss Check (emergency exit)
        if position.unrealized_pnl_pct <= -25:
            reasons.append(f"Emergency exit: {position.unrealized_pnl_pct:.1f}% loss")
            should_exit = True
        
        if not should_exit:
            return None
        
        # Create exit signal
        token = TokenInfo(
            mint=position.mint,
            symbol=position.symbol,
            name=position.symbol,
            price_usd=position.current_price
        )
        
        signal = TradeSignal(
            token=token,
            action=TradeAction.SELL,
            confidence=1.0,
            suggested_amount_sol=position.amount_sol_invested,
            risk_level="exit",
            reasons=reasons,
            source_agent="sell_agent",
            strategy="exit"
        )
        
        logger.info(f"🚨 Exit signal for ${position.symbol}: {', '.join(reasons)}")
        
        return signal
    
    # =========================================================================
    # TRAILING STOP
    # =========================================================================
    
    def update_trailing_stop(
        self,
        position: Position,
        trail_pct: float = 10.0
    ) -> Position:
        """
        Update trailing stop based on highest price reached
        """
        # Track highest price (would need to store this)
        highest_price = getattr(position, '_highest_price', position.entry_price)
        
        if position.current_price > highest_price:
            highest_price = position.current_price
            position._highest_price = highest_price
            
            # Update stop loss to trail
            new_stop = highest_price * (1 - trail_pct / 100)
            if new_stop > position.stop_loss_price:
                position.stop_loss_price = new_stop
                logger.debug(f"Trailing stop updated for {position.symbol}: {new_stop:.6f}")
        
        return position
    
    # =========================================================================
    # BATCH OPERATIONS
    # =========================================================================
    
    async def emergency_exit_all(self, positions: List[Position]) -> List[TradeSignal]:
        """
        Generate exit signals for all positions (emergency mode)
        """
        signals = []
        
        for position in positions:
            token = TokenInfo(
                mint=position.mint,
                symbol=position.symbol,
                name=position.symbol,
                price_usd=position.current_price
            )
            
            signal = TradeSignal(
                token=token,
                action=TradeAction.SELL,
                confidence=1.0,
                suggested_amount_sol=position.amount_sol_invested,
                risk_level="emergency",
                reasons=["Emergency exit triggered"],
                source_agent="sell_agent",
                strategy="emergency"
            )
            
            signals.append(signal)
        
        logger.warning(f"⚠️ Emergency exit: {len(signals)} positions flagged")
        
        return signals
    
    def get_profitable_positions(self, positions: List[Position]) -> List[Position]:
        """
        Filter to only profitable positions
        """
        return [p for p in positions if p.unrealized_pnl_pct > 0]
    
    def get_losing_positions(self, positions: List[Position]) -> List[Position]:
        """
        Filter to only losing positions
        """
        return [p for p in positions if p.unrealized_pnl_pct < 0]
    
    # =========================================================================
    # STATISTICS
    # =========================================================================
    
    def get_exit_stats(self) -> Dict:
        """
        Get statistics on exit signals
        """
        if not self.exit_signals:
            return {"total": 0}
        
        stop_losses = sum(1 for s in self.exit_signals if "stop loss" in str(s.reasons).lower())
        take_profits = sum(1 for s in self.exit_signals if "take profit" in str(s.reasons).lower())
        timeouts = sum(1 for s in self.exit_signals if "timeout" in str(s.reasons).lower())
        emergencies = sum(1 for s in self.exit_signals if "emergency" in str(s.reasons).lower())
        
        return {
            "total": len(self.exit_signals),
            "stop_losses": stop_losses,
            "take_profits": take_profits,
            "timeouts": timeouts,
            "emergencies": emergencies
        }


# Singleton instance
_sell_agent: Optional[SellAgent] = None


def get_sell_agent() -> SellAgent:
    """Get or create the sell agent singleton"""
    global _sell_agent
    if _sell_agent is None:
        _sell_agent = SellAgent()
    return _sell_agent
