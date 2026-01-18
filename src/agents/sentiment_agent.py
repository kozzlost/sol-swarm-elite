"""Real-time Multi-source Sentiment Analysis"""
from src.services.api_aggregator import api_aggregator
from typing import Dict, Any

class SentimentAgent:
    def __init__(self):
        self.aggregator = api_aggregator
    
    async def analyze_token(self, token_address: str, symbol: str = None) -> Dict[str, Any]:
        """Use real API aggregator for sentiment analysis"""
        return await self.aggregator.analyze_token_comprehensive(token_address, symbol)

sentiment_agent = SentimentAgent()
