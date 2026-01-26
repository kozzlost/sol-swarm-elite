"""
Arbiter Agent - AI-Powered Trading Decision Engine
Makes final buy/sell decisions based on all available intelligence.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from src.types import (
    TokenInfo, RugCheckResult, SentimentResult,
    TradeSignal, TradeAction, Position
)
from src.constants import (
    TradingThresholds, Strategy, ACTIVE_STRATEGY,
    PAPER_TRADING
)

logger = logging.getLogger(__name__)


@dataclass
class TokenAnalysis:
    """Complete analysis for a token"""
    token: TokenInfo
    rug_check: Optional[RugCheckResult] = None
    sentiment: Optional[SentimentResult] = None
    
    # Scores (0-100)
    safety_score: float = 0.0
    momentum_score: float = 0.0
    sentiment_score: float = 0.0
    overall_score: float = 0.0
    
    # Flags
    is_tradeable: bool = False
    reasons: List[str] = None
    
    def __post_init__(self):
        if self.reasons is None:
            self.reasons = []


class ArbiterAgent:
    """
    The Arbiter makes final trading decisions by aggregating intelligence
    from Scout, Sentiment, and other agents.
    
    Decision Framework:
    1. Safety Check (RugCheck must pass)
    2. Sentiment Check (must meet threshold)
    3. Momentum Check (price action analysis)
    4. Strategy-specific filters
    5. Position sizing
    """
    
    def __init__(self, strategy: Strategy = None):
        self.strategy = strategy or ACTIVE_STRATEGY
        self.pending_signals: List[TradeSignal] = []
        self.signal_history: List[TradeSignal] = []
        self._running = False
        
        # Decision thresholds
        self.min_overall_score = 60  # 0-100 scale
        self.min_confidence = 0.5    # 0-1 scale
    
    async def start(self):
        """Initialize the arbiter agent"""
        self._running = True
        logger.info(f"⚖️ Arbiter Agent initialized (Strategy: {self.strategy.value})")
    
    async def stop(self):
        """Shutdown the arbiter agent"""
        self._running = False
        logger.info("Arbiter Agent stopped")
    
    # =========================================================================
    # DECISION MAKING
    # =========================================================================
    
    async def evaluate_token(
        self,
        token: TokenInfo,
        rug_check: Optional[RugCheckResult] = None,
        sentiment: Optional[SentimentResult] = None
    ) -> TokenAnalysis:
        """
        Perform comprehensive evaluation of a token
        """
        analysis = TokenAnalysis(
            token=token,
            rug_check=rug_check,
            sentiment=sentiment
        )
        
        # 1. Safety Score (0-100)
        analysis.safety_score = self._calculate_safety_score(rug_check)
        
        # 2. Sentiment Score (0-100)
        analysis.sentiment_score = self._calculate_sentiment_score(sentiment)
        
        # 3. Momentum Score (0-100)
        analysis.momentum_score = self._calculate_momentum_score(token)
        
        # 4. Strategy-specific adjustments
        strategy_multiplier = self._get_strategy_multiplier(token, analysis)
        
        # 5. Calculate overall score
        weights = self._get_score_weights()
        analysis.overall_score = (
            analysis.safety_score * weights["safety"] +
            analysis.sentiment_score * weights["sentiment"] +
            analysis.momentum_score * weights["momentum"]
        ) * strategy_multiplier
        
        # 6. Determine if tradeable
        analysis.is_tradeable = self._is_tradeable(analysis)
        
        return analysis
    
    async def generate_signal(
        self,
        analysis: TokenAnalysis,
        existing_position: Optional[Position] = None
    ) -> Optional[TradeSignal]:
        """
        Generate a trade signal based on analysis
        """
        if not analysis.is_tradeable:
            return None
        
        # Determine action
        if existing_position:
            action = self._evaluate_exit(existing_position, analysis)
        else:
            action = self._evaluate_entry(analysis)
        
        if action == TradeAction.SKIP:
            return None
        
        # Calculate confidence
        confidence = analysis.overall_score / 100
        
        # Determine position size
        suggested_amount = self._calculate_position_size(analysis, confidence)
        
        # Determine risk levels
        stop_loss = self._calculate_stop_loss(analysis)
        take_profit = self._calculate_take_profit(analysis)
        
        signal = TradeSignal(
            token=analysis.token,
            action=action,
            confidence=confidence,
            suggested_amount_sol=suggested_amount,
            risk_level=self._assess_risk_level(analysis),
            stop_loss_pct=stop_loss,
            take_profit_pct=take_profit,
            reasons=analysis.reasons,
            source_agent="arbiter",
            strategy=self.strategy.value
        )
        
        self.pending_signals.append(signal)
        self.signal_history.append(signal)
        
        action_emoji = "🟢" if action == TradeAction.BUY else "🔴"
        logger.info(
            f"{action_emoji} Signal: {action.value.upper()} ${analysis.token.symbol} "
            f"@ {confidence:.0%} confidence, {suggested_amount:.4f} SOL"
        )
        
        return signal
    
    async def evaluate_and_signal(
        self,
        token: TokenInfo,
        rug_check: Optional[RugCheckResult] = None,
        sentiment: Optional[SentimentResult] = None,
        existing_position: Optional[Position] = None
    ) -> Optional[TradeSignal]:
        """
        Combined evaluation and signal generation
        """
        analysis = await self.evaluate_token(token, rug_check, sentiment)
        return await self.generate_signal(analysis, existing_position)
    
    # =========================================================================
    # SCORING CALCULATIONS
    # =========================================================================
    
    def _calculate_safety_score(self, rug_check: Optional[RugCheckResult]) -> float:
        """
        Calculate safety score (0-100) from RugCheck results
        """
        if not rug_check:
            return 0.0  # No data = assume unsafe
        
        score = 100.0
        
        # Honeypot detection (-50 if detected)
        if rug_check.is_honeypot:
            return 0.0  # Immediate fail
        
        # Honeypot score penalty
        score -= rug_check.honeypot_score * 30
        
        # Mint authority (-20 if not revoked)
        if rug_check.is_mintable:
            score -= 20
        
        # Freeze authority (-15 if not revoked)
        if rug_check.is_freezable:
            score -= 15
        
        # Top holder concentration
        if rug_check.top10_holder_pct > 80:
            score -= 30
        elif rug_check.top10_holder_pct > 60:
            score -= 15
        elif rug_check.top10_holder_pct > 40:
            score -= 5
        
        return max(0.0, min(100.0, score))
    
    def _calculate_sentiment_score(self, sentiment: Optional[SentimentResult]) -> float:
        """
        Calculate sentiment score (0-100) from social analysis
        """
        if not sentiment:
            return 50.0  # Neutral if no data
        
        # Convert -10 to +10 scale to 0-100
        # -10 -> 0, 0 -> 50, +10 -> 100
        base_score = (sentiment.overall_score + 10) * 5
        
        # Bonus for high mention count
        if sentiment.total_mentions > 100:
            base_score += 10
        elif sentiment.total_mentions > 50:
            base_score += 5
        
        # Bonus if trending
        if sentiment.is_trending:
            base_score += 15
        
        return max(0.0, min(100.0, base_score))
    
    def _calculate_momentum_score(self, token: TokenInfo) -> float:
        """
        Calculate momentum score (0-100) from price action
        """
        score = 50.0  # Start neutral
        
        # 5-minute momentum
        if token.price_change_5m > 10:
            score += 20
        elif token.price_change_5m > 5:
            score += 10
        elif token.price_change_5m < -10:
            score -= 20
        elif token.price_change_5m < -5:
            score -= 10
        
        # 1-hour momentum
        if token.price_change_1h > 20:
            score += 15
        elif token.price_change_1h > 10:
            score += 8
        elif token.price_change_1h < -20:
            score -= 15
        elif token.price_change_1h < -10:
            score -= 8
        
        # Volume consideration (higher volume = more confidence)
        if token.volume_24h_usd > 100000:
            score += 10
        elif token.volume_24h_usd > 50000:
            score += 5
        
        # Liquidity consideration
        if token.liquidity_usd > 50000:
            score += 5
        elif token.liquidity_usd < 10000:
            score -= 10
        
        return max(0.0, min(100.0, score))
    
    # =========================================================================
    # STRATEGY LOGIC
    # =========================================================================
    
    def _get_score_weights(self) -> Dict[str, float]:
        """
        Get scoring weights based on active strategy
        """
        weights = {
            Strategy.MOMENTUM: {"safety": 0.3, "sentiment": 0.2, "momentum": 0.5},
            Strategy.SENTIMENT: {"safety": 0.3, "sentiment": 0.5, "momentum": 0.2},
            Strategy.PUMP_GRADUATE: {"safety": 0.4, "sentiment": 0.3, "momentum": 0.3},
            Strategy.WHALE_COPY: {"safety": 0.35, "sentiment": 0.25, "momentum": 0.4},
            Strategy.SNIPER: {"safety": 0.25, "sentiment": 0.25, "momentum": 0.5},
            Strategy.SCALPER: {"safety": 0.2, "sentiment": 0.2, "momentum": 0.6},
        }
        
        return weights.get(self.strategy, {"safety": 0.33, "sentiment": 0.33, "momentum": 0.34})
    
    def _get_strategy_multiplier(self, token: TokenInfo, analysis: TokenAnalysis) -> float:
        """
        Apply strategy-specific multipliers
        """
        multiplier = 1.0
        
        if self.strategy == Strategy.MOMENTUM:
            # Boost for strong short-term momentum
            if token.price_change_5m > 15:
                multiplier = 1.2
                analysis.reasons.append("Strong 5m momentum")
        
        elif self.strategy == Strategy.PUMP_GRADUATE:
            # Boost for tokens graduating from pump.fun
            if token.market_cap_usd > 50000 and token.liquidity_usd > 20000:
                multiplier = 1.15
                analysis.reasons.append("Pump.fun graduate candidate")
        
        elif self.strategy == Strategy.SENTIMENT:
            # Boost for viral sentiment
            if analysis.sentiment and analysis.sentiment.is_trending:
                multiplier = 1.25
                analysis.reasons.append("Viral social sentiment")
        
        return multiplier
    
    # =========================================================================
    # ENTRY/EXIT LOGIC
    # =========================================================================
    
    def _evaluate_entry(self, analysis: TokenAnalysis) -> TradeAction:
        """
        Determine if we should enter a position
        """
        if analysis.overall_score < self.min_overall_score:
            return TradeAction.SKIP
        
        # Additional entry conditions
        if analysis.safety_score < 50:
            analysis.reasons.append("Safety too low for entry")
            return TradeAction.SKIP
        
        analysis.reasons.append(f"Score: {analysis.overall_score:.0f}/100")
        return TradeAction.BUY
    
    def _evaluate_exit(self, position: Position, analysis: TokenAnalysis) -> TradeAction:
        """
        Determine if we should exit an existing position
        """
        # Check stop loss
        if position.unrealized_pnl_pct <= -TradingThresholds.STOP_LOSS_PCT:
            analysis.reasons.append(f"Stop loss triggered: {position.unrealized_pnl_pct:.1f}%")
            return TradeAction.SELL
        
        # Check take profit
        if position.unrealized_pnl_pct >= TradingThresholds.TAKE_PROFIT_PCT:
            analysis.reasons.append(f"Take profit triggered: {position.unrealized_pnl_pct:.1f}%")
            return TradeAction.SELL
        
        # Sentiment reversal
        if analysis.sentiment_score < 30:
            analysis.reasons.append("Sentiment deteriorating")
            return TradeAction.SELL
        
        # Momentum reversal
        if analysis.momentum_score < 30 and position.unrealized_pnl_pct > 0:
            analysis.reasons.append("Taking profit on momentum reversal")
            return TradeAction.SELL
        
        return TradeAction.HOLD
    
    def _is_tradeable(self, analysis: TokenAnalysis) -> bool:
        """
        Final check if token is tradeable
        """
        # Must have rug check
        if not analysis.rug_check:
            analysis.reasons.append("No safety data")
            return False
        
        # Must pass safety
        if not analysis.rug_check.passes_safety_check:
            analysis.reasons.append("Failed safety check")
            return False
        
        # Must meet minimum liquidity
        if analysis.token.liquidity_usd < TradingThresholds.MIN_LIQUIDITY_USD:
            analysis.reasons.append("Liquidity too low")
            return False
        
        # Must meet overall score threshold
        if analysis.overall_score < self.min_overall_score:
            analysis.reasons.append(f"Score {analysis.overall_score:.0f} < {self.min_overall_score}")
            return False
        
        return True
    
    # =========================================================================
    # POSITION SIZING & RISK
    # =========================================================================
    
    def _calculate_position_size(self, analysis: TokenAnalysis, confidence: float) -> float:
        """
        Calculate recommended position size in SOL
        """
        # Base sizing on confidence
        base_size = TradingThresholds.MIN_TRADE_SOL
        max_size = TradingThresholds.MAX_TRADE_SOL
        
        # Scale between min and max based on confidence
        size = base_size + (max_size - base_size) * confidence
        
        # Reduce for lower safety scores
        if analysis.safety_score < 70:
            size *= 0.7
        
        return round(min(size, max_size), 4)
    
    def _calculate_stop_loss(self, analysis: TokenAnalysis) -> float:
        """
        Calculate stop loss percentage
        """
        base_stop = TradingThresholds.STOP_LOSS_PCT
        
        # Tighten stop for lower safety scores
        if analysis.safety_score < 60:
            return base_stop * 0.8
        
        return base_stop
    
    def _calculate_take_profit(self, analysis: TokenAnalysis) -> float:
        """
        Calculate take profit percentage
        """
        base_tp = TradingThresholds.TAKE_PROFIT_PCT
        
        # Higher targets for high momentum
        if analysis.momentum_score > 80:
            return base_tp * 1.5
        
        return base_tp
    
    def _assess_risk_level(self, analysis: TokenAnalysis) -> str:
        """
        Assess overall risk level
        """
        if analysis.safety_score > 80 and analysis.overall_score > 75:
            return "medium"
        elif analysis.safety_score > 60:
            return "high"
        else:
            return "extreme"


# Singleton instance
_arbiter_agent: Optional[ArbiterAgent] = None


def get_arbiter_agent() -> ArbiterAgent:
    """Get or create the arbiter agent singleton"""
    global _arbiter_agent
    if _arbiter_agent is None:
        _arbiter_agent = ArbiterAgent()
    return _arbiter_agent
