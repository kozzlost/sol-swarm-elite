"""
SOL-SWARM Elite Agents
Multi-agent trading system components.
"""

from src.agents.scout_agent import ScoutAgent, get_scout_agent
from src.agents.sentiment_agent import SentimentAgent, get_sentiment_agent
from src.agents.arbiter_agent import ArbiterAgent, get_arbiter_agent
from src.agents.sniper_agent import SniperAgent, get_sniper_agent
from src.agents.sell_agent import SellAgent, get_sell_agent
from src.agents.treasury_agent import TreasuryAgent, get_treasury_agent
from src.agents.agent_spawner import AgentSpawner, get_agent_spawner, SwarmAgent

__all__ = [
    "ScoutAgent", "get_scout_agent",
    "SentimentAgent", "get_sentiment_agent",
    "ArbiterAgent", "get_arbiter_agent",
    "SniperAgent", "get_sniper_agent",
    "SellAgent", "get_sell_agent",
    "TreasuryAgent", "get_treasury_agent",
    "AgentSpawner", "get_agent_spawner", "SwarmAgent",
]
