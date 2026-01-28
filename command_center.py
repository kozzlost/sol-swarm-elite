"""
SOL-SWARM Elite - Command Center
Central orchestrator for the entire trading swarm.
"""

import logging
import json
from datetime import datetime
from typing import Dict, List, Optional

from src.types import TradeSignal, AgentAction
from src.agents.ceo_agent import CEOAgent
from src.agents.sentiment_agent import SentimentAgent
from src.constants import LOG_LEVEL, LOG_FORMAT


# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT
)


class CommandCenter:
    """
    Command Center - Central orchestrator for the SOL-SWARM Elite system.
    
    Orchestrates:
    - CEO Agent (strategic decisions)
    - Sentiment Agent (social media analysis)
    - Scout Agent (token discovery)
    - Arbiter Agent (consensus voting)
    - Sniper Agent (trade execution)
    """
    
    def __init__(self):
        self.logger = logging.getLogger("CommandCenter")
        
        # Initialize agents
        self.ceo = CEOAgent()
        self.sentiment = SentimentAgent()
        
        # Placeholder for other agents (implement separately)
        self.scout = None
        self.arbiter = None
        self.sniper = None
        
        # Pipeline tracking
        self.signals_processed = 0
        self.trades_executed = 0
        self.trades_failed = 0
        
        self.logger.info("=" * 60)
        self.logger.info("SOL-SWARM Elite Command Center initialized")
        self.logger.info("=" * 60)
    
    def process_signal(self, signal: TradeSignal) -> bool:
        """
        Process a trade signal through the entire pipeline.
        
        Pipeline:
        1. CEO Agent validates basic requirements
        2. Sentiment Agent analyzes social sentiment
        3. Arbiter Agent votes on trade
        4. Sniper Agent executes if approved
        
        Args:
            signal: TradeSignal to process
            
        Returns:
            True if trade was executed, False otherwise
        """
        self.signals_processed += 1
        token = signal.token
        
        self.logger.info("-" * 60)
        self.logger.info(f"[PIPELINE] Processing signal #{self.signals_processed}: {token}")
        self.logger.info(f"[SIGNAL] Price: ${signal.price:.6f} | Liquidity: ${signal.liquidity:,.0f}")
        
        # Step 1: CEO Agent evaluation
        self.logger.info(f"[STEP 1/4] CEO Agent evaluation...")
        ceo_decision = self.ceo.allocate_resources(signal)
        
        if ceo_decision.action != AgentAction.TRADE:
            self.logger.info(
                f"[RESULT] Trade REJECTED by CEO: {ceo_decision.reason} "
                f"(Risk: {ceo_decision.risk_level}/100)"
            )
            return False
        
        self.logger.info(f"[APPROVED] CEO approved trade (Risk: {ceo_decision.risk_level}/100)")
        
        # Step 2: Sentiment Agent analysis
        self.logger.info(f"[STEP 2/4] Sentiment Agent analysis...")
        try:
            signal = self.sentiment.analyze_signal(signal)
            self.logger.info(
                f"[SENTIMENT] Score: {signal.sentiment_score:.2f} "
                f"({signal.sentiment_score*100:.0f}% positive) | "
                f"Mentions: {signal.social_mentions}"
            )
        except Exception as e:
            self.logger.warning(f"[SENTIMENT] Error during analysis: {e}")
            signal.sentiment_score = 0.5  # Neutral default
        
        # Re-check sentiment in CEO decision
        ceo_sentiment_check = self.ceo._check_sentiment(signal)
        if ceo_sentiment_check:
            self.logger.info(f"[REJECTED] Sentiment threshold not met: {ceo_sentiment_check.reason}")
            return False
        
        # Step 3: Arbiter Agent consensus (placeholder)
        self.logger.info(f"[STEP 3/4] Arbiter Agent voting...")
        arbiter_approved = self._simulate_arbiter_vote(signal)
        
        if not arbiter_approved:
            self.logger.info(f"[REJECTED] Arbiter consensus not reached")
            return False
        
        # Step 4: Sniper Agent execution
        self.logger.info(f"[STEP 4/4] Sniper Agent execution...")
        execution_success = self._simulate_sniper_execution(signal)
        
        if execution_success:
            self.logger.info(f"[EXECUTED] Trade executed successfully for {token}")
            self.trades_executed += 1
            
            # Track in CEO agent
            self.ceo.track_trade(signal.token, signal.price, 0.01)  # Example quantity
            
            return True
        else:
            self.logger.error(f"[FAILED] Sniper execution failed for {token}")
            self.trades_failed += 1
            return False
    
    def _simulate_arbiter_vote(self, signal: TradeSignal) -> bool:
        """
        Simulate Arbiter Agent voting.
        
        In a full implementation, this would:
        - Aggregate votes from multiple analysis agents
        - Check technical indicators
        - Verify contract safety
        
        Args:
            signal: TradeSignal to evaluate
            
        Returns:
            True if consensus reached, False otherwise
        """
        # Placeholder: approve if sentiment is decent and liquidity is good
        if signal.sentiment_score is None:
            consensus_vote = 0.7  # 70% confidence
        else:
            consensus_vote = (signal.sentiment_score + 0.6) / 2  # Average sentiment and baseline
        
        self.logger.debug(f"[ARBITER] Consensus vote: {consensus_vote:.2f}")
        return consensus_vote > 0.65
    
    def _simulate_sniper_execution(self, signal: TradeSignal) -> bool:
        """
        Simulate Sniper Agent execution.
        
        In a full implementation, this would:
        - Monitor liquidity pools
        - Execute actual swaps
        - Handle slippage and fees
        - Track position
        
        Args:
            signal: TradeSignal to execute
            
        Returns:
            True if execution successful, False otherwise
        """
        # Placeholder: assume 90% success rate
        import random
        success = random.random() < 0.9
        
        if success:
            self.logger.debug(f"[SNIPER] Successfully bought {signal.token}")
        else:
            self.logger.debug(f"[SNIPER] Execution failed - network error")
        
        return success
    
    def monitor_positions(self):
        """Monitor and update all active trading positions"""
        self.logger.info(f"[MONITOR] Checking {len(self.ceo.active_trades)} active positions...")
        
        for token, position_data in list(self.ceo.active_trades.items()):
            # In a real implementation, fetch current price from DEX
            # For now, simulate price movement
            import random
            price_change = random.gauss(0, 5)  # Random walk
            current_price = position_data["entry_price"] * (1 + price_change / 100)
            
            # Check stop loss / take profit
            entry_price = position_data["entry_price"]
            if current_price <= entry_price * 0.95:  # -5% stop loss
                self.logger.info(f"[STOP LOSS] {token} hit stop loss")
                self.ceo.close_trade(token, current_price, -100)  # Example loss
            elif current_price >= entry_price * 1.25:  # +25% take profit
                self.logger.info(f"[TAKE PROFIT] {token} hit take profit")
                self.ceo.close_trade(token, current_price, 500)  # Example gain
    
    def update_market_conditions(self, volatility: float, market_change: float):
        """
        Update market conditions and adjust strategy.
        
        Args:
            volatility: Market volatility percentage
            market_change: Overall market change percentage
        """
        self.ceo.monitor_market(volatility, market_change)
    
    def get_system_status(self) -> Dict:
        """Get current system status"""
        status = self.ceo.get_status()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "signals_processed": self.signals_processed,
            "trades_executed": self.trades_executed,
            "trades_failed": self.trades_failed,
            "success_rate": self.trades_executed / max(self.trades_executed + self.trades_failed, 1),
            "active_trades": status.total_active_trades,
            "total_capital_deployed": status.total_capital_deployed,
            "total_profit_loss": status.total_profit_loss,
            "market_condition": status.market_condition,
            "system_health": status.system_health,
            "trading_paused": self.ceo.trading_paused
        }
    
    def get_detailed_report(self) -> Dict:
        """Get detailed operational report"""
        ceo_report = self.ceo.get_report()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "pipeline": {
                "signals_processed": self.signals_processed,
                "trades_executed": self.trades_executed,
                "trades_failed": self.trades_failed,
                "success_rate": self.trades_executed / max(self.trades_executed + self.trades_failed, 1)
            },
            "ceo_agent": ceo_report,
            "system_status": self.get_system_status()
        }
    
    def print_status(self):
        """Print formatted status to console"""
        status = self.get_system_status()
        
        print("\n" + "=" * 70)
        print("SOL-SWARM ELITE - COMMAND CENTER STATUS")
        print("=" * 70)
        print(f"Timestamp: {status['timestamp']}")
        print("-" * 70)
        print(f"Signals Processed: {status['signals_processed']}")
        print(f"Trades Executed: {status['trades_executed']}")
        print(f"Success Rate: {status['success_rate']*100:.1f}%")
        print("-" * 70)
        print(f"Active Trades: {status['active_trades']}")
        print(f"Capital Deployed: ${status['total_capital_deployed']:.2f}")
        print(f"Profit/Loss: ${status['total_profit_loss']:+.2f}")
        print("-" * 70)
        print(f"Market: {status['market_condition'].upper()}")
        print(f"System Health: {status['system_health'].upper()}")
        print(f"Trading Status: {'PAUSED' if status['trading_paused'] else 'ACTIVE'}")
        print("=" * 70 + "\n")
