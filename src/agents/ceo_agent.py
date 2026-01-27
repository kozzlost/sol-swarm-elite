from src.types import TradeSignal, AgentDecision
from src.constants import MIN_LIQUIDITY_USD, MAX_HONEYPOT_SCORE
import logging

class CEOAgent:
    def __init__(self, capital_per_agent=0.05):
        self.capital_per_agent = capital_per_agent
        self.active_agents = []
        self.logger = logging.getLogger("CEOAgent")

    def allocate_resources(self, signal: TradeSignal) -> AgentDecision:
        """Decide whether to allocate agents to a trade."""
        if signal.liquidity < MIN_LIQUIDITY_USD:
            self.logger.warning(f"Low liquidity for {signal.token}. Skipping.")
            return AgentDecision(action="skip", reason="low_liquidity")

        if signal.honeypot_score > MAX_HONEYPOT_SCORE:
            self.logger.warning(f"High honeypot risk for {signal.token}. Skipping.")
            return AgentDecision(action="skip", reason="high_risk")

        # Allocate agents
        self.logger.info(f"Allocating agents to {signal.token}.")
        return AgentDecision(
            action="trade",
            capital=self.capital_per_agent,
            agents=["scout", "sentiment", "arbiter", "sniper"]
        )

    def pause_trading(self, market_condition: str):
        """Pause trading during extreme market conditions."""
        self.logger.warning(f"Pausing trading due to {market_condition}.")
        # Logic to pause all agents
