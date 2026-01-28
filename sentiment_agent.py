"""
SOL-SWARM Elite - Sentiment Agent
Analyzes social media sentiment using AI models for tokens.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import json

from src.types import SentimentAnalysisResult, TradeSignal
from src.constants import (
    SENTIMENT_MODEL, MIN_TWEETS_FOR_ANALYSIS, SENTIMENT_CACHE_HOURS
)


class SentimentAgent:
    """
    Sentiment Agent - Analyzes social media sentiment for tokens.
    
    Responsibilities:
    - Fetch social media data (Twitter, Reddit, Discord)
    - Perform AI-powered sentiment analysis
    - Cache results to avoid duplicate API calls
    - Provide sentiment scores for trading decisions
    """
    
    def __init__(self):
        self.logger = logging.getLogger("SentimentAgent")
        self.sentiment_cache: Dict[str, Dict] = {}
        self.model_name = SENTIMENT_MODEL
        
        # Import transformers model
        try:
            from transformers import pipeline
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model=self.model_name,
                device=-1  # CPU, use 0 for GPU if available
            )
            self.logger.info(f"Loaded sentiment model: {self.model_name}")
        except ImportError:
            self.logger.error("transformers library not installed. Install with: pip install transformers torch")
            self.sentiment_pipeline = None
    
    def analyze(
        self,
        token: str,
        texts: List[str],
        use_cache: bool = True
    ) -> SentimentAnalysisResult:
        """
        Analyze sentiment for a token based on text samples.
        
        Args:
            token: Token name/symbol
            texts: List of text samples (tweets, reddit posts, etc.)
            use_cache: Whether to use cached results
            
        Returns:
            SentimentAnalysisResult with sentiment scores
        """
        
        # Check cache
        if use_cache and token in self.sentiment_cache:
            cached = self.sentiment_cache[token]
            cache_age = datetime.now() - datetime.fromisoformat(cached["cached_at"])
            if cache_age < timedelta(hours=SENTIMENT_CACHE_HOURS):
                self.logger.info(f"Using cached sentiment for {token}")
                return self._dict_to_result(cached["result"])
        
        # Validate input
        if not texts or len(texts) < MIN_TWEETS_FOR_ANALYSIS:
            self.logger.warning(
                f"Insufficient samples for {token}: {len(texts)} < {MIN_TWEETS_FOR_ANALYSIS}"
            )
            return self._default_result(token)
        
        # Analyze sentiment
        if self.sentiment_pipeline is None:
            self.logger.error("Sentiment pipeline not available, returning default result")
            return self._default_result(token)
        
        try:
            # Clean and prepare texts
            clean_texts = [self._clean_text(t) for t in texts if t]
            clean_texts = clean_texts[:100]  # Limit to 100 for performance
            
            self.logger.info(f"Analyzing {len(clean_texts)} samples for {token}")
            
            # Run sentiment analysis
            predictions = self.sentiment_pipeline(clean_texts)
            
            # Aggregate results
            result = self._aggregate_sentiments(token, predictions, clean_texts)
            
            # Cache result
            self.sentiment_cache[token] = {
                "result": self._result_to_dict(result),
                "cached_at": datetime.now().isoformat()
            }
            
            self.logger.info(
                f"Sentiment for {token}: {result.overall_score:.2f} "
                f"(+{result.positive_percentage:.1f}% / -{result.negative_percentage:.1f}%)"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing sentiment for {token}: {e}")
            return self._default_result(token)
    
    def _aggregate_sentiments(
        self,
        token: str,
        predictions: List[Dict],
        texts: List[str]
    ) -> SentimentAnalysisResult:
        """
        Aggregate sentiment predictions into overall metrics.
        
        Args:
            token: Token name
            predictions: List of sentiment predictions from model
            texts: Original text samples
            
        Returns:
            Aggregated SentimentAnalysisResult
        """
        
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        for pred in predictions:
            label = pred.get("label", "NEUTRAL").upper()
            score = pred.get("score", 0.0)
            
            if label == "POSITIVE":
                positive_count += 1
            elif label == "NEGATIVE":
                negative_count += 1
            else:
                neutral_count += 1
        
        total = len(predictions)
        positive_pct = (positive_count / total) * 100
        negative_pct = (negative_count / total) * 100
        neutral_pct = (neutral_count / total) * 100
        
        # Calculate overall score (0-1, where 0.5 is neutral)
        overall_score = positive_pct / 100
        
        return SentimentAnalysisResult(
            token=token,
            overall_score=overall_score,
            positive_percentage=positive_pct,
            negative_percentage=negative_pct,
            neutral_percentage=neutral_pct,
            text_samples=texts[:5],  # Store sample texts
            sample_count=total,
            analysis_timestamp=datetime.now().isoformat(),
            model_used=self.model_name
        )
    
    def _clean_text(self, text: str) -> str:
        """
        Clean text for sentiment analysis.
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        # Remove URLs
        text = " ".join(word for word in text.split() if not word.startswith("http"))
        
        # Remove @mentions
        text = " ".join(word for word in text.split() if not word.startswith("@"))
        
        # Remove hashtags (keep text after #)
        text = text.replace("#", " ")
        
        # Remove extra whitespace
        text = " ".join(text.split())
        
        # Limit length
        text = text[:512]  # BERT max input
        
        return text
    
    def _default_result(self, token: str) -> SentimentAnalysisResult:
        """Return neutral default result"""
        return SentimentAnalysisResult(
            token=token,
            overall_score=0.5,  # Neutral
            positive_percentage=33.3,
            negative_percentage=33.3,
            neutral_percentage=33.3,
            sample_count=0,
            analysis_timestamp=datetime.now().isoformat()
        )
    
    def fetch_twitter_data(self, token: str, count: int = 50) -> List[str]:
        """
        Fetch tweets mentioning a token.
        
        NOTE: Requires Twitter API v2 bearer token
        
        Args:
            token: Token to search for
            count: Number of tweets to fetch
            
        Returns:
            List of tweet texts
        """
        try:
            import tweepy
            
            bearer_token = self._get_twitter_token()
            if not bearer_token:
                self.logger.warning("Twitter API token not configured")
                return []
            
            client = tweepy.Client(bearer_token=bearer_token)
            
            query = f"{token} -is:retweet lang:en"
            response = client.search_recent_tweets(
                query=query,
                max_results=min(count, 100),
                tweet_fields=["created_at", "public_metrics"]
            )
            
            if not response.data:
                self.logger.info(f"No tweets found for {token}")
                return []
            
            tweets = [tweet.text for tweet in response.data]
            self.logger.info(f"Fetched {len(tweets)} tweets for {token}")
            return tweets
            
        except ImportError:
            self.logger.error("tweepy not installed. Install with: pip install tweepy")
            return []
        except Exception as e:
            self.logger.error(f"Error fetching Twitter data: {e}")
            return []
    
    def fetch_reddit_data(self, token: str, count: int = 50) -> List[str]:
        """
        Fetch Reddit posts mentioning a token.
        
        NOTE: Requires Reddit API credentials
        
        Args:
            token: Token to search for
            count: Number of posts to fetch
            
        Returns:
            List of post texts
        """
        try:
            import praw
            
            reddit = self._init_reddit()
            if not reddit:
                self.logger.warning("Reddit API not configured")
                return []
            
            posts = []
            subreddits = ["solana", "defi", "cryptocurrency"]
            
            for subreddit_name in subreddits:
                try:
                    subreddit = reddit.subreddit(subreddit_name)
                    for submission in subreddit.search(token, time_filter="week", limit=count//3):
                        posts.append(submission.title)
                        if submission.selftext:
                            posts.append(submission.selftext)
                except Exception as e:
                    self.logger.debug(f"Error fetching from r/{subreddit_name}: {e}")
            
            self.logger.info(f"Fetched {len(posts)} Reddit posts for {token}")
            return posts[:count]
            
        except ImportError:
            self.logger.error("praw not installed. Install with: pip install praw")
            return []
        except Exception as e:
            self.logger.error(f"Error fetching Reddit data: {e}")
            return []
    
    def fetch_discord_data(self, token: str) -> List[str]:
        """
        Fetch Discord messages (if you have a bot monitoring servers).
        
        NOTE: Requires Discord bot integration
        
        Args:
            token: Token to search for
            
        Returns:
            List of message texts
        """
        self.logger.info("Discord data collection requires custom bot integration")
        return []
    
    def analyze_signal(self, signal: TradeSignal) -> TradeSignal:
        """
        Perform full sentiment analysis on a trade signal.
        
        Args:
            signal: TradeSignal to enrich
            
        Returns:
            Updated TradeSignal with sentiment data
        """
        self.logger.info(f"Performing sentiment analysis on {signal.token}")
        
        # Fetch social data
        twitter_data = self.fetch_twitter_data(signal.token)
        reddit_data = self.fetch_reddit_data(signal.token)
        
        all_texts = twitter_data + reddit_data
        
        if not all_texts:
            self.logger.warning(f"No social data found for {signal.token}")
            signal.sentiment_score = 0.5  # Neutral
            return signal
        
        # Analyze sentiment
        result = self.analyze(signal.token, all_texts)
        
        # Update signal
        signal.sentiment_score = result.overall_score
        signal.social_mentions = len(all_texts)
        
        return signal
    
    @staticmethod
    def _get_twitter_token() -> Optional[str]:
        """Get Twitter API token from environment"""
        import os
        return os.getenv("TWITTER_BEARER_TOKEN")
    
    @staticmethod
    def _init_reddit():
        """Initialize Reddit API"""
        import os
        try:
            import praw
            return praw.Reddit(
                client_id=os.getenv("REDDIT_CLIENT_ID"),
                client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
                user_agent=os.getenv("REDDIT_USER_AGENT", "SOL-SWARM Elite")
            )
        except Exception as e:
            return None
    
    @staticmethod
    def _result_to_dict(result: SentimentAnalysisResult) -> Dict:
        """Convert result to dict for caching"""
        return {
            "token": result.token,
            "overall_score": result.overall_score,
            "positive_percentage": result.positive_percentage,
            "negative_percentage": result.negative_percentage,
            "neutral_percentage": result.neutral_percentage,
            "sample_count": result.sample_count,
            "model_used": result.model_used
        }
    
    @staticmethod
    def _dict_to_result(data: Dict) -> SentimentAnalysisResult:
        """Convert dict back to result"""
        return SentimentAnalysisResult(
            token=data["token"],
            overall_score=data["overall_score"],
            positive_percentage=data["positive_percentage"],
            negative_percentage=data["negative_percentage"],
            neutral_percentage=data["neutral_percentage"],
            sample_count=data["sample_count"],
            model_used=data.get("model_used", SENTIMENT_MODEL)
        )
