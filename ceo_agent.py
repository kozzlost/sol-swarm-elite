"""
SOL-SWARM Elite - CEO Agent
Oversees the entire swarm, allocates resources, and makes high-level decisions.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict

from src.types import TradeSignal, AgentDecision, AgentAction, SwarmStatus, AgentMetrics
from src.constants import (
    MIN_LIQUIDITY_USD, MAX_HONEYPOT_SCORE, MIN_SENTIMENT_SCORE,
    CAPITAL_PER_AGENT, MAX_CONCURRENT_TRADES, VOLATILITY_ALERT,
    MARKET_CRASH_THRESHOLD, SCOUT_ALERT_THRESHOLD
)


class CEOAgent:
    """
    CEO Agent - Strategic decision maker for the swarm.
    
    Responsibilities:
    - Allocate capital and agents to trading opportunities
    - Monitor market conditions and system health
    - Pause/resume trading based on risk assessment
    - Coordinate between Scout, Sentiment, Arbiter, and Sniper agents
    """
    
    def __init__(self, capital_per_agent: float = CAPITAL_PER_AGENT):
        self.logger = logging.getLogger("CEOAgent")
        self.capital_per_agent = capital_per_agent
        self.active_trades: Dict[str, Dict] = {}
        self.market_condition = "normal"
        self.system_health = "healthy"
        self.trading_paused = False
        self.pause_reason = None
        
        # Metrics
        self.total_capital_deployed = 0.0
        self.total_profit_loss = 0.0
        self.decisions_made = 0
        self.trades_approved = 0
        self.trades_rejected = 0
        
    def allocate_resources(self, signal: TradeSignal) -> AgentDecision:
        """
        Evaluate a trade signal and decide whether to allocate agents.
        
        Args:
            signal: TradeSignal with token information
            
        Returns:
            AgentDecision with action and allocation details
        """
        self.logger.info(f"Evaluating signal for {signal.token}")
        self.decisions_made += 1
        
        # Check if trading is paused
        if self.trading_paused:
            return AgentDecision(
                action=AgentAction.PAUSE,
                reason=self.pause_reason or "Trading paused by CEO",
                risk_level=100
            )
        
        # Validate basic requirements
        basic_check = self._validate_basic_requirements(signal)
        if basic_check:
            return basic_check
        
        # Evaluate risk
        risk_level = self._assess_risk(signal)
        
        # Check capacity
        if len(self.active_trades) >= MAX_CONCURRENT_TRADES:
            self.logger.warning(f"At maximum concurrent trades ({MAX_CONCURRENT_TRADES})")
            return AgentDecision(
                action=AgentAction.SKIP,
                reason="Maximum concurrent trades reached",
                risk_level=risk_level
            )
        
        # Sentiment check (if available)
        sentiment_check = self._check_sentiment(signal)
        if sentiment_check:
            return sentiment_check
        
        # Approved for trading
        self.logger.info(f"Approving trade for {signal.token} with risk level {risk_level}")
        self.trades_approved += 1
        
        return AgentDecision(
            action=AgentAction.TRADE,
            reason=f"Signal validated - Honeypot: {signal.honeypot_score:.2f}, Liquidity: ${signal.liquidity:,.0f}",
            capital=self.capital_per_agent,
            agents_to_deploy=["scout", "sentiment", "arbiter", "sniper"],
            risk_level=risk_level,
            confidence=0.8
        )
    
    def _validate_basic_requirements(self, signal: TradeSignal) -> Optional[AgentDecision]:
        """Check basic liquidity and risk requirements"""
        
        if signal.liquidity < MIN_LIQUIDITY_USD:
            self.logger.warning(f"Low liquidity for {signal.token}: ${signal.liquidity:,.0f}")
            self.trades_rejected += 1
            return AgentDecision(
                action=AgentAction.SKIP,
                reason=f"Insufficient liquidity: ${signal.liquidity:,.0f} < ${MIN_LIQUIDITY_USD:,.0f}",
                risk_level=95
            )
        
        if signal.honeypot_score > MAX_HONEYPOT_SCORE:
            self.logger.warning(f"High honeypot risk for {signal.token}: {signal.honeypot_score:.2f}")
            self.trades_rejected += 1
            return AgentDecision(
                action=AgentAction.SKIP,
                reason=f"Honeypot risk too high: {signal.honeypot_score:.2f} > {MAX_HONEYPOT_SCORE}",
                risk_level=100
            )
        
        if signal.rug_pull_risk == "high":
            self.logger.warning(f"High rug pull risk for {signal.token}")
            self.trades_rejected += 1
            return AgentDecision(
                action=AgentAction.SKIP,
                reason="High rug pull risk detected",
                risk_level=100
            )
        
        return None
    
    def _assess_risk(self, signal: TradeSignal) -> int:
        """
        Assess overall risk level (0-100).
        
        Factors:
        - Honeypot score
        - Liquidity
        - Holder concentration
        - Volume ratio
        """
        risk_score = 0
        
        # Honeypot risk (0-40 points)
        risk_score += int(signal.honeypot_score * 40)
        
        # Liquidity risk (0-20 points) - lower liquidity = higher risk
        if signal.liquidity < MIN_LIQUIDITY_USD * 2:
            risk_score += 15
        elif signal.liquidity < MIN_LIQUIDITY_USD * 5:
            risk_score += 10
        else:
            risk_score += 5
        
        # Volume ratio (0-20 points)
        if signal.volume_ratio > 5:
            risk_score += 10  # Suspiciously high volume
        elif signal.volume_ratio < 0.5:
            risk_score += 15  # Very low volume
        
        # Holder concentration (0-20 points)
        if signal.holder_count < 100:
            risk_score += 20
        elif signal.holder_count < 500:
            risk_score += 10
        
        # Cap at 100
        return min(risk_score, 100)
    
    def _check_sentiment(self, signal: TradeSignal) -> Optional[AgentDecision]:
        """Check sentiment score if available"""
        
        if signal.sentiment_score is None:
            # Sentiment not yet analyzed, continue
            return None
        
        if signal.sentiment_score < MIN_SENTIMENT_SCORE:
            self.logger.warning(
                f"Low sentiment for {signal.token}: {signal.sentiment_score:.2f} "
                f"< {MIN_SENTIMENT_SCORE}"
            )
            self.trades_rejected += 1
            return AgentDecision(
                action=AgentAction.SKIP,
                reason=f"Sentiment too low: {signal.sentiment_score:.2f}",
                risk_level=70
            )
        
        return None
    
    def monitor_market(self, volatility: float, market_change_percent: float):
        """
        Monitor market conditions and adjust trading strategy.
        
        Args:
            volatility: Current market volatility percentage
            market_change_percent: Overall market change percentage
        """
        self.logger.info(f"Market Monitor - Volatility: {volatility:.1f}%, Change: {market_change_percent:.1f}%")
        
        # Check for extreme conditions
        if market_change_percent < MARKET_CRASH_THRESHOLD:
            self.logger.critical(f"Market crash detected! Change: {market_change_percent:.1f}%")
            self.pause_trading("Market crash detected")
            return
        
        if volatility > VOLATILITY_ALERT:
            self.logger.warning(f"High volatility detected: {volatility:.1f}%")
            self.market_condition = "volatile"
            self.system_health = "warning"
        else:
            self.market_condition = "normal"
        
        # Update system health
        self._update_system_health()
    
    def pause_trading(self, reason: str, duration_minutes: int = 30):
        """
        Pause all trading operations.
        
        Args:
            reason: Reason for pausing
            duration_minutes: How long to pause
        """
        self.logger.critical(f"PAUSING TRADING: {reason} (Duration: {duration_minutes} min)")
        self.trading_paused = True
        self.pause_reason = reason
        self.system_health = "critical"
    
    def resume_trading(self):
        """Resume trading operations"""
        self.logger.info("Resuming trading operations")
        self.trading_paused = False
        self.pause_reason = None
        self.system_health = "healthy"
    
    def track_trade(self, token: str, entry_price: float, quantity: float):
        """Track active trades"""
        self.active_trades[token] = {
            "entry_price": entry_price,
            "quantity": quantity,
            "entry_time": datetime.now().isoformat(),
            "status": "open"
        }
        self.total_capital_deployed += self.capital_per_agent
        self.logger.info(f"Tracking new trade: {token} @ ${entry_price:.6f}")
    
    def close_trade(self, token: str, exit_price: float, profit_loss: float):
        """Close and record a trade"""
        if token in self.active_trades:
            self.active_trades[token]["status"] = "closed"
            self.active_trades[token]["exit_price"] = exit_price
            self.active_trades[token]["exit_time"] = datetime.now().isoformat()
            
            self.total_profit_loss += profit_loss
            self.logger.info(
                f"Closed trade: {token} | Profit/Loss: ${profit_loss:+.2f} | "
                f"Cumulative P/L: ${self.total_profit_loss:+.2f}"
            )
    
    def _update_system_health(self):
        """Update overall system health status"""
        if self.trading_paused:
            self.system_health = "critical"
        elif self.market_condition == "volatile":
            self.system_health = "warning"
        elif len(self.active_trades) > MAX_CONCURRENT_TRADES * 0.8:
            self.system_health = "warning"
        else:
            self.system_health = "healthy"
    
    def get_status(self) -> SwarmStatus:
        """Return current swarm status"""
        return SwarmStatus(
            active_agents=4,  # Scout, Sentiment, Arbiter, Sniper
            total_active_trades=len(self.active_trades),
            total_capital_deployed=self.total_capital_deployed,
            total_profit_loss=self.total_profit_loss,
            market_condition=self.market_condition,
            system_health=self.system_health,
            last_update_time=datetime.now().isoformat()
        )
    
    def get_report(self) -> Dict:
        """Generate detailed CEO report"""
        return {
            "timestamp": datetime.now().isoformat(),
            "trading_paused": self.trading_paused,
            "pause_reason": self.pause_reason,
            "decisions_made": self.decisions_made,
            "trades_approved": self.trades_approved,
            "trades_rejected": self.trades_rejected,
            "approval_rate": self.trades_approved / max(self.decisions_made, 1),
            "active_trades": len(self.active_trades),
            "total_capital_deployed": self.total_capital_deployed,
            "total_profit_loss": self.total_profit_loss,
            "market_condition": self.market_condition,
            "system_health": self.system_health,
            "active_tokens": list(self.active_trades.keys())
        }
