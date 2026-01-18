"""
🌐 Comprehensive API Aggregation Service
Integrates: X, DexScreener, RugCheck, Cielo, LunarCrush, Telegram, Discord
"""
import aiohttp
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import httpx

class APIAggregator:
    """Unified API aggregation for all data sources"""
    
    def __init__(
        self,
        x_bearer_token: str = None,
        cielo_key: str = None,
        lunarcrush_key: str = None,
        dexscreener_timeout: float = 10.0,
        rugcheck_timeout: float = 10.0
    ):
        self.x_bearer_token = x_bearer_token
        self.cielo_key = cielo_key
        self.lunarcrush_key = lunarcrush_key
        self.session: Optional[aiohttp.ClientSession] = None
        self.dexscreener_timeout = dexscreener_timeout
        self.rugcheck_timeout = rugcheck_timeout
        self.last_request_time = {}
        self.rate_limit_delays = {
            "dexscreener": 0.5,
            "rugcheck": 1.0,
            "x_api": 1.0,
            "cielo": 1.0,
            "lunarcrush": 1.0
        }
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self.session
    
    async def close(self):
        """Close session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    # ===== X API =====
    async def get_x_sentiment(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """Fetch X (Twitter) sentiment data"""
        if not self.x_bearer_token:
            print("⚠️ X API token not configured")
            return {}
        
        try:
            headers = {"Authorization": f"Bearer {self.x_bearer_token}"}
            url = f"https://api.twitter.com/2/tweets/search/recent?query={symbol}&max_results={limit}&tweet.fields=public_metrics,created_at"
            
            session = await self.get_session()
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    tweets = data.get("data", [])
                    
                    # Calculate sentiment metrics
                    total_likes = sum(t.get("public_metrics", {}).get("like_count", 0) for t in tweets)
                    total_retweets = sum(t.get("public_metrics", {}).get("retweet_count", 0) for t in tweets)
                    total_replies = sum(t.get("public_metrics", {}).get("reply_count", 0) for t in tweets)
                    
                    return {
                        "tweet_count": len(tweets),
                        "total_likes": total_likes,
                        "total_retweets": total_retweets,
                        "total_replies": total_replies,
                        "avg_engagement": (total_likes + total_retweets + total_replies) / max(len(tweets), 1),
                        "sentiment_score": self._calculate_sentiment(total_retweets, total_likes),
                        "last_updated": datetime.now().isoformat()
                    }
        except Exception as e:
            print(f"❌ X API error: {e}")
        
        return {}
    
    # ===== DexScreener =====
    async def get_dexscreener_data(self, token_address: str) -> Dict[str, Any]:
        """Fetch comprehensive token data from DexScreener"""
        try:
            url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
            
            session = await self.get_session()
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=self.dexscreener_timeout)) as response:
                if response.status == 200:
                    data = await response.json()
                    pairs = data.get("pairs", [])
                    
                    if pairs:
                        pair = pairs[0]  # Best liquidity pair
                        return {
                            "token_address": token_address,
                            "price_usd": float(pair.get("priceUsd", 0) or 0),
                            "liquidity_usd": float(pair.get("liquidity", {}).get("usd", 0) or 0),
                            "volume_24h": float(pair.get("volume", {}).get("h24", 0) or 0),
                            "market_cap": float(pair.get("marketCap", 0) or 0),
                            "fdv": float(pair.get("fdv", 0) or 0),
                            "price_change_5m": float(pair.get("priceChange", {}).get("m5", 0) or 0),
                            "price_change_1h": float(pair.get("priceChange", {}).get("h1", 0) or 0),
                            "price_change_24h": float(pair.get("priceChange", {}).get("h24", 0) or 0),
                            "txns_24h_buy": pair.get("txns", {}).get("h24", {}).get("buys", 0),
                            "txns_24h_sell": pair.get("txns", {}).get("h24", {}).get("sells", 0),
                            "pair_address": pair.get("pairAddress"),
                            "dex_id": pair.get("dexId")
                        }
        except Exception as e:
            print(f"❌ DexScreener error: {e}")
        
        return {}
    
    # ===== RugCheck =====
    async def get_rugcheck_data(self, token_address: str) -> Dict[str, Any]:
        """Fetch security vetting from RugCheck"""
        try:
            url = f"https://api.rugcheck.xyz/v1/tokens/{token_address}/report"
            
            session = await self.get_session()
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=self.rugcheck_timeout)) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    risks = data.get("risks", [])
                    risk_level = self._calculate_risk_level(risks)
                    
                    return {
                        "token_address": token_address,
                        "is_honeypot": any("honeypot" in str(r).lower() for r in risks),
                        "honeypot_score": data.get("honeypotScore", 0),
                        "is_mintable": not data.get("mintAuthorityRevoked", False),
                        "is_freezable": not data.get("freezeAuthorityRevoked", False),
                        "lp_burned_percent": self._get_lp_burned(data),
                        "top_10_holders_percent": sum(h.get("percentage", 0) for h in data.get("topHolders", [])[:10]),
                        "risk_level": risk_level,
                        "rugcheck_score": 100 - (risk_level * 10),
                        "risks": [str(r)[:50] for r in risks[:5]]
                    }
        except Exception as e:
            print(f"❌ RugCheck error: {e}")
        
        return {}
    
    # ===== LunarCrush =====
    async def get_lunarcrush_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch LunarCrush galaxy score & sentiment"""
        if not self.lunarcrush_key:
            print("⚠️ LunarCrush key not configured")
            return {}
        
        try:
            url = f"https://lunarcrush.com/api4/public/coins/{symbol.lower()}/metrics"
            headers = {"Authorization": f"Bearer {self.lunarcrush_key}"}
            
            session = await self.get_session()
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    metrics = data.get("data", {})
                    
                    return {
                        "galaxy_score": metrics.get("galaxy_score", 0),
                        "sentiment": metrics.get("sentiment", 0),
                        "news_count": metrics.get("news_count", 0),
                        "reddit_activity": metrics.get("reddit_activity", 0),
                        "social_dominance": metrics.get("social_dominance", 0),
                        "correlation_rank": metrics.get("correlation_rank", 0)
                    }
        except Exception as e:
            print(f"⚠️ LunarCrush error (optional): {e}")
        
        return {}
    
    # ===== Cielo Smart Money =====
    async def get_cielo_smartmoney(self, token_address: str) -> Dict[str, Any]:
        """Fetch Cielo smart money data"""
        if not self.cielo_key:
            print("⚠️ Cielo key not configured")
            return {}
        
        try:
            url = f"https://api.cielo.finance/v1/tokens/{token_address}/smart_money"
            headers = {"Authorization": f"Bearer {self.cielo_key}"}
            
            session = await self.get_session()
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    return {
                        "smart_money_inflow_sol": data.get("inflow_sol", 0),
                        "whale_wallets_buying": data.get("whale_count", 0),
                        "legendary_traders": data.get("legendary_count", 0),
                        "avg_buyer_win_rate": data.get("avg_win_rate", 0),
                        "smart_money_score": data.get("score", 0)
                    }
        except Exception as e:
            print(f"⚠️ Cielo error (optional): {e}")
        
        return {}
    
    # ===== Comprehensive Token Analysis =====
    async def analyze_token_comprehensive(self, token_address: str, symbol: str = None) -> Dict[str, Any]:
        """Get complete token analysis from all sources"""
        print(f"📊 Analyzing {symbol or token_address}...")
        
        # Fetch all data in parallel
        dex_data, rug_data, cielo_data = await asyncio.gather(
            self.get_dexscreener_data(token_address),
            self.get_rugcheck_data(token_address),
            self.get_cielo_smartmoney(token_address),
            return_exceptions=True
        )
        
        # Fetch X sentiment if symbol provided
        x_data = {}
        if symbol:
            x_data = await self.get_x_sentiment(symbol)
        
        # Combine and score
        analysis = {
            "token_address": token_address,
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "dexscreener": dex_data if isinstance(dex_data, dict) else {},
            "rugcheck": rug_data if isinstance(rug_data, dict) else {},
            "cielo_smartmoney": cielo_data if isinstance(cielo_data, dict) else {},
            "x_sentiment": x_data if isinstance(x_data, dict) else {},
            "composite_score": self._calculate_composite_score(dex_data, rug_data, cielo_data, x_data)
        }
        
        return analysis
    
    # ===== Scoring Functions =====
    def _calculate_sentiment(self, retweets: int, likes: int) -> float:
        """Calculate sentiment from engagement"""
        if retweets + likes == 0:
            return 0.0
        return (retweets * 0.7 + likes * 0.3) / max((retweets + likes), 1)
    
    def _calculate_risk_level(self, risks: List) -> int:
        """Calculate overall risk level 0-10"""
        return min(len(risks) // 2, 10)
    
    def _get_lp_burned(self, data: Dict) -> float:
        """Extract LP burn percentage"""
        markets = data.get("markets", [])
        for market in markets:
            if burned := market.get("lp", {}).get("lpBurned"):
                return burned
        return 0.0
    
    def _calculate_composite_score(
        self,
        dex_data: Dict,
        rug_data: Dict,
        cielo_data: Dict,
        x_data: Dict
    ) -> float:
        """Calculate weighted composite trading score"""
        score = 0.0
        weights = 0.0
        
        # DexScreener score (40%)
        if dex_data and isinstance(dex_data, dict):
            liq = dex_data.get("liquidity_usd", 0)
            vol = dex_data.get("volume_24h", 0)
            dex_score = min((liq / 10000 + vol / 50000) * 50, 50)
            score += dex_score * 0.4
            weights += 0.4
        
        # RugCheck score (30%)
        if rug_data and isinstance(rug_data, dict):
            rug_score = rug_data.get("rugcheck_score", 0) * 0.3
            score += rug_score
            weights += 0.3
        
        # Cielo score (20%)
        if cielo_data and isinstance(cielo_data, dict):
            cielo_score = cielo_data.get("smart_money_score", 0) * 0.2
            score += cielo_score
            weights += 0.2
        
        # X sentiment (10%)
        if x_data and isinstance(x_data, dict):
            x_score = min(x_data.get("avg_engagement", 0) / 1000, 10) * 0.1
            score += x_score
            weights += 0.1
        
        return min(score / max(weights, 1), 100)

# Singleton instance
api_aggregator = APIAggregator()
