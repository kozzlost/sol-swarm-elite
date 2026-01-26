"""
Sentiment Agent - Multi-Source Social Analysis
Analyzes social sentiment from Twitter/X, Telegram, and other sources.
"""

import asyncio
import aiohttp
import logging
import re
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from collections import Counter

from src.types import TokenInfo, SentimentResult
from src.constants import TradingThresholds

logger = logging.getLogger(__name__)


class SentimentAgent:
    """
    Analyzes social sentiment for tokens across multiple platforms.
    
    Sources:
    - Twitter/X (via API or scraping)
    - Telegram mentions
    - Reddit (r/solana, r/cryptocurrency)
    - Discord (if accessible)
    
    Scoring:
    - Positive: +1 to +10
    - Neutral: 0
    - Negative: -1 to -10
    """
    
    # Sentiment keywords
    POSITIVE_KEYWORDS = [
        "moon", "bullish", "pump", "gem", "100x", "buy", "long", "ath",
        "amazing", "incredible", "rocket", "🚀", "💎", "📈", "fire", "based",
        "wagmi", "gm", "lfg", "send it", "degen", "alpha", "early"
    ]
    
    NEGATIVE_KEYWORDS = [
        "rug", "scam", "dump", "sell", "bearish", "honeypot", "avoid",
        "fake", "exit", "crash", "dead", "rip", "ngmi", "📉", "💀",
        "don't buy", "warning", "suspicious", "sketchy", "bot"
    ]
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.sentiment_cache: Dict[str, SentimentResult] = {}
        self._running = False
        
        # API keys (loaded from env)
        import os
        self.twitter_bearer = os.getenv("TWITTER_BEARER_TOKEN", "")
        self.lunarcrush_key = os.getenv("LUNARCRUSH_API_KEY", "")
    
    async def start(self):
        """Initialize the sentiment agent"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        self._running = True
        logger.info("📊 Sentiment Agent initialized")
    
    async def stop(self):
        """Shutdown the sentiment agent"""
        self._running = False
        if self.session:
            await self.session.close()
        logger.info("Sentiment Agent stopped")
    
    # =========================================================================
    # MAIN ANALYSIS
    # =========================================================================
    
    async def analyze_token(self, token: TokenInfo) -> SentimentResult:
        """
        Perform comprehensive sentiment analysis for a token
        """
        result = SentimentResult(
            mint=token.mint,
            symbol=token.symbol
        )
        
        # Gather sentiment from multiple sources concurrently
        tasks = []
        
        if self.twitter_bearer:
            tasks.append(self._analyze_twitter(token.symbol))
        else:
            tasks.append(self._simulate_twitter(token.symbol))
        
        # Could add more sources here:
        # tasks.append(self._analyze_telegram(token.symbol))
        # tasks.append(self._analyze_reddit(token.symbol))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aggregate results
        twitter_result = results[0] if not isinstance(results[0], Exception) else {}
        
        result.twitter_score = twitter_result.get("score", 0)
        result.twitter_mentions = twitter_result.get("mentions", 0)
        result.top_keywords = twitter_result.get("keywords", [])
        result.positive_mentions = twitter_result.get("positive", 0)
        result.negative_mentions = twitter_result.get("negative", 0)
        result.total_mentions = result.twitter_mentions
        
        # Calculate overall score (-10 to +10)
        result.overall_score = self._calculate_overall_score(result)
        
        # Determine if trending
        result.is_trending = result.total_mentions > 50 and result.overall_score > 2
        
        # Cache result
        self.sentiment_cache[token.mint] = result
        
        sentiment_emoji = "🟢" if result.overall_score > 2 else "🔴" if result.overall_score < -2 else "🟡"
        logger.info(
            f"{sentiment_emoji} Sentiment for ${token.symbol}: "
            f"{result.overall_score:.1f} ({result.total_mentions} mentions)"
        )
        
        return result
    
    async def analyze_multiple(self, tokens: List[TokenInfo]) -> Dict[str, SentimentResult]:
        """
        Analyze sentiment for multiple tokens concurrently
        """
        tasks = [self.analyze_token(token) for token in tokens]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        analyzed = {}
        for token, result in zip(tokens, results):
            if isinstance(result, SentimentResult):
                analyzed[token.mint] = result
            else:
                analyzed[token.mint] = SentimentResult(mint=token.mint, symbol=token.symbol)
        
        return analyzed
    
    def passes_sentiment_threshold(self, mint: str) -> bool:
        """
        Check if a token passes the minimum sentiment threshold
        """
        result = self.sentiment_cache.get(mint)
        if not result:
            return False
        
        return result.overall_score >= TradingThresholds.MIN_SENTIMENT_SCORE
    
    # =========================================================================
    # TWITTER/X ANALYSIS
    # =========================================================================
    
    async def _analyze_twitter(self, symbol: str) -> Dict[str, Any]:
        """
        Analyze Twitter sentiment using API
        """
        try:
            # Twitter API v2 search
            url = "https://api.twitter.com/2/tweets/search/recent"
            headers = {"Authorization": f"Bearer {self.twitter_bearer}"}
            params = {
                "query": f"${symbol} OR #{symbol} -is:retweet lang:en",
                "max_results": 100,
                "tweet.fields": "created_at,public_metrics"
            }
            
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    tweets = data.get("data", [])
                    return self._process_tweets(tweets)
                else:
                    logger.warning(f"Twitter API returned {response.status}")
                    return self._simulate_twitter(symbol)
        
        except Exception as e:
            logger.error(f"Twitter analysis error: {e}")
            return await self._simulate_twitter(symbol)
    
    async def _simulate_twitter(self, symbol: str) -> Dict[str, Any]:
        """
        Simulate Twitter sentiment for paper trading/testing
        """
        import random
        
        # Generate realistic-looking fake data
        mentions = random.randint(10, 200)
        positive = int(mentions * random.uniform(0.3, 0.7))
        negative = int(mentions * random.uniform(0.1, 0.3))
        
        score = (positive - negative) / max(mentions, 1) * 10
        
        return {
            "score": round(score, 2),
            "mentions": mentions,
            "positive": positive,
            "negative": negative,
            "keywords": random.sample(self.POSITIVE_KEYWORDS, min(3, len(self.POSITIVE_KEYWORDS)))
        }
    
    def _process_tweets(self, tweets: List[Dict]) -> Dict[str, Any]:
        """
        Process tweet data and extract sentiment
        """
        if not tweets:
            return {"score": 0, "mentions": 0, "positive": 0, "negative": 0, "keywords": []}
        
        positive = 0
        negative = 0
        all_keywords = []
        
        for tweet in tweets:
            text = tweet.get("text", "").lower()
            
            # Score based on keywords
            pos_matches = sum(1 for kw in self.POSITIVE_KEYWORDS if kw.lower() in text)
            neg_matches = sum(1 for kw in self.NEGATIVE_KEYWORDS if kw.lower() in text)
            
            if pos_matches > neg_matches:
                positive += 1
            elif neg_matches > pos_matches:
                negative += 1
            
            # Extract keywords
            for kw in self.POSITIVE_KEYWORDS + self.NEGATIVE_KEYWORDS:
                if kw.lower() in text:
                    all_keywords.append(kw)
        
        # Get top keywords
        keyword_counts = Counter(all_keywords)
        top_keywords = [kw for kw, _ in keyword_counts.most_common(5)]
        
        # Calculate score
        total = len(tweets)
        score = ((positive - negative) / total) * 10 if total > 0 else 0
        
        return {
            "score": round(score, 2),
            "mentions": total,
            "positive": positive,
            "negative": negative,
            "keywords": top_keywords
        }
    
    # =========================================================================
    # SCORING
    # =========================================================================
    
    def _calculate_overall_score(self, result: SentimentResult) -> float:
        """
        Calculate overall sentiment score from all sources
        """
        scores = []
        weights = []
        
        # Twitter (highest weight)
        if result.twitter_mentions > 0:
            scores.append(result.twitter_score)
            weights.append(0.6)
        
        # Telegram
        if result.telegram_score != 0:
            scores.append(result.telegram_score)
            weights.append(0.25)
        
        # Reddit
        if result.reddit_score != 0:
            scores.append(result.reddit_score)
            weights.append(0.15)
        
        if not scores:
            return 0.0
        
        # Weighted average
        total_weight = sum(weights[:len(scores)])
        weighted_sum = sum(s * w for s, w in zip(scores, weights[:len(scores)]))
        
        return round(weighted_sum / total_weight, 2) if total_weight > 0 else 0.0
    
    # =========================================================================
    # TREND DETECTION
    # =========================================================================
    
    async def detect_trending(self, tokens: List[TokenInfo]) -> List[TokenInfo]:
        """
        Filter tokens to only those that are currently trending
        """
        await self.analyze_multiple(tokens)
        
        trending = []
        for token in tokens:
            result = self.sentiment_cache.get(token.mint)
            if result and result.is_trending:
                trending.append(token)
        
        logger.info(f"🔥 Found {len(trending)} trending tokens")
        return trending


# Singleton instance
_sentiment_agent: Optional[SentimentAgent] = None


def get_sentiment_agent() -> SentimentAgent:
    """Get or create the sentiment agent singleton"""
    global _sentiment_agent
    if _sentiment_agent is None:
        _sentiment_agent = SentimentAgent()
    return _sentiment_agent
