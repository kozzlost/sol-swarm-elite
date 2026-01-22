"""Agent tests"""
import pytest


class TestScoutAgent:
            """Tests for Scout Agent."""

    def test_scout_agent_import(self):
                    """Test ScoutAgent can be imported."""
                    from src.agents.scout_agent import ScoutAgent
                    assert ScoutAgent is not None

    def test_scout_agent_instantiation(self):
                    """Test ScoutAgent can be created."""
                    from src.agents.scout_agent import ScoutAgent
                    scout = ScoutAgent()
                    assert scout is not None

    @pytest.mark.asyncio
    async def test_scan_tokens(self):
                    """Test scan_tokens returns list."""
                    from src.agents.scout_agent import ScoutAgent
                    scout = ScoutAgent()
                    result = await scout.scan_tokens()
                    assert isinstance(result, list)


class TestSentimentAgent:
            """Tests for Sentiment Agent."""

    def test_sentiment_agent_import(self):
                    """Test SentimentAgent can be imported."""
                    from src.agents.sentiment_agent import SentimentAgent
                    assert SentimentAgent is not None


class TestArbiterAgent:
            """Tests for Arbiter Agent."""

    def test_arbiter_agent_import(self):
                    """Test ArbiterAgent can be imported."""
                    from src.agents.arbiter_agent import ArbiterAgent
                    assert ArbiterAgent is not None


class TestState:
            """Tests for state management."""

    def test_state_import(self):
                    """Test state can be imported."""
                    from src.agents.state import AgentMessage
                    assert AgentMessage is not None


class TestAPIAggregator:
            """Tests for API Aggregator."""

    def test_api_aggregator_import(self):
                    """Test APIAggregator can be imported."""
                    from src.services.api_aggregator import APIAggregator
                    assert APIAggregator is not None

    def test_api_aggregator_instantiation(self):
                    """Test APIAggregator can be created."""
                    from src.services.api_aggregator import APIAggregator
                    api = APIAggregator()
                    assert api is not None


class TestSmokeTests:
            """Basic smoke tests."""

    def test_src_package(self):
                    """Test src package exists."""
                    import src
                    assert src is not None

    def test_agents_package(self):
                    """Test agents package exists."""
                    import src.agents
                    assert src.agents is not None

    def test_services_package(self):
                    """Test services package exists."""
                    import src.services
                    assert src.services is not None
