"""
Scout Agent - Token Discovery & Initial Vetting
Monitors multiple sources for new token opportunities.
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from src.types import TokenInfo, RugCheckResult
from src.constants import (
    DEXSCREENER_API, DEXSCREENER_PAIRS_URL,
    RUGCHECK_API, RUGCHECK_TOKEN_URL,
    PUMPFUN_API, PUMPFUN_COINS_URL,
    TradingThresholds, PAPER_TRADING
)

logger = logging.getLogger(__name__)


class ScoutAgent:
    """
    Discovers new tokens and performs initial security vetting.
    
    Sources:
    - DexScreener (new pairs, trending)
    - Pump.fun (new launches, graduates)
    - RugCheck (security analysis)
    """
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.discovered_tokens: Dict[str, TokenInfo] = {}
        self.vetted_tokens: Dict[str, RugCheckResult] = {}
        self._running = False
    
    async def start(self):
        """Initialize the scout agent"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        self._running = True
        logger.info("🔭 Scout Agent initialized")
    
    async def stop(self):
        """Shutdown the scout agent"""
        self._running = False
        if self.session:
            await self.session.close()
        logger.info("Scout Agent stopped")
    
    # =========================================================================
    # TOKEN DISCOVERY
    # =========================================================================
    
    async def discover_dexscreener_pairs(self, limit: int = 20) -> List[TokenInfo]:
        """
        Fetch latest Solana pairs from DexScreener
        """
        tokens = []
        
        try:
            url = f"{DEXSCREENER_API}/search?q=solana"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    pairs = data.get("pairs", [])[:limit]
                    
                    for pair in pairs:
                        if pair.get("chainId") != "solana":
                            continue
                        
                        token = self._parse_dexscreener_pair(pair)
                        if token and self._passes_initial_filter(token):
                            tokens.append(token)
                            self.discovered_tokens[token.mint] = token
                    
                    logger.info(f"📡 DexScreener: Found {len(tokens)} potential tokens")
                else:
                    logger.warning(f"DexScreener API returned {response.status}")
        
        except Exception as e:
            logger.error(f"DexScreener discovery error: {e}")
        
        return tokens
    
    async def discover_pumpfun_launches(self, limit: int = 20) -> List[TokenInfo]:
        """
        Fetch new launches from Pump.fun
        """
        tokens = []
        
        try:
            url = f"{PUMPFUN_COINS_URL}?limit={limit}&sort=created_timestamp&order=desc"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    coins = data if isinstance(data, list) else data.get("coins", [])
                    
                    for coin in coins[:limit]:
                        token = self._parse_pumpfun_coin(coin)
                        if token:
                            tokens.append(token)
                            self.discovered_tokens[token.mint] = token
                    
                    logger.info(f"🎯 Pump.fun: Found {len(tokens)} new launches")
                else:
                    logger.warning(f"Pump.fun API returned {response.status}")
        
        except Exception as e:
            logger.error(f"Pump.fun discovery error: {e}")
        
        return tokens
    
    async def get_trending_tokens(self, limit: int = 10) -> List[TokenInfo]:
        """
        Get currently trending tokens across sources
        """
        tokens = []
        
        try:
            # DexScreener trending
            url = f"{DEXSCREENER_API}/tokens/trending"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for item in data[:limit]:
                        if item.get("chainId") == "solana":
                            token = self._parse_dexscreener_pair(item)
                            if token:
                                tokens.append(token)
        
        except Exception as e:
            logger.error(f"Trending fetch error: {e}")
        
        return tokens
    
    # =========================================================================
    # SECURITY VETTING
    # =========================================================================
    
    async def vet_token(self, mint: str) -> RugCheckResult:
        """
        Perform security analysis using RugCheck API
        """
        result = RugCheckResult(mint=mint)
        
        try:
            url = f"{RUGCHECK_TOKEN_URL}/{mint}/report"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    result = self._parse_rugcheck_response(mint, data)
                    self.vetted_tokens[mint] = result
                    
                    status = "✅ SAFE" if result.passes_safety_check else "⚠️ RISKY"
                    logger.info(f"🔍 RugCheck {mint[:8]}...: {status} (score: {result.honeypot_score:.2f})")
                else:
                    logger.warning(f"RugCheck returned {response.status} for {mint[:8]}...")
        
        except Exception as e:
            logger.error(f"RugCheck error for {mint[:8]}...: {e}")
        
        return result
    
    async def vet_multiple(self, mints: List[str]) -> Dict[str, RugCheckResult]:
        """
        Vet multiple tokens concurrently
        """
        tasks = [self.vet_token(mint) for mint in mints]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        vetted = {}
        for mint, result in zip(mints, results):
            if isinstance(result, RugCheckResult):
                vetted[mint] = result
            else:
                vetted[mint] = RugCheckResult(mint=mint)  # Failed, assume unsafe
        
        return vetted
    
    # =========================================================================
    # COMBINED DISCOVERY FLOW
    # =========================================================================
    
    async def discover_and_vet(
        self,
        sources: List[str] = ["dexscreener", "pumpfun"],
        limit_per_source: int = 10,
        vet_all: bool = True
    ) -> List[TokenInfo]:
        """
        Full discovery pipeline: find tokens, vet them, return safe ones
        """
        all_tokens = []
        
        # Discover from sources
        if "dexscreener" in sources:
            tokens = await self.discover_dexscreener_pairs(limit_per_source)
            all_tokens.extend(tokens)
        
        if "pumpfun" in sources:
            tokens = await self.discover_pumpfun_launches(limit_per_source)
            all_tokens.extend(tokens)
        
        if not all_tokens:
            return []
        
        # Deduplicate by mint
        unique_tokens = {t.mint: t for t in all_tokens}
        
        if not vet_all:
            return list(unique_tokens.values())
        
        # Vet all tokens
        mints = list(unique_tokens.keys())
        vet_results = await self.vet_multiple(mints)
        
        # Filter to safe tokens
        safe_tokens = []
        for mint, token in unique_tokens.items():
            vet_result = vet_results.get(mint)
            if vet_result and vet_result.passes_safety_check:
                safe_tokens.append(token)
        
        logger.info(f"🎯 Discovery complete: {len(safe_tokens)}/{len(unique_tokens)} passed vetting")
        
        return safe_tokens
    
    # =========================================================================
    # PARSING HELPERS
    # =========================================================================
    
    def _parse_dexscreener_pair(self, pair: Dict[str, Any]) -> Optional[TokenInfo]:
        """Parse DexScreener pair data into TokenInfo"""
        try:
            base_token = pair.get("baseToken", {})
            
            return TokenInfo(
                mint=base_token.get("address", ""),
                symbol=base_token.get("symbol", "???"),
                name=base_token.get("name", "Unknown"),
                price_usd=float(pair.get("priceUsd", 0) or 0),
                price_sol=float(pair.get("priceNative", 0) or 0),
                market_cap_usd=float(pair.get("marketCap", 0) or 0),
                liquidity_usd=float(pair.get("liquidity", {}).get("usd", 0) or 0),
                volume_24h_usd=float(pair.get("volume", {}).get("h24", 0) or 0),
                price_change_5m=float(pair.get("priceChange", {}).get("m5", 0) or 0),
                price_change_1h=float(pair.get("priceChange", {}).get("h1", 0) or 0),
                price_change_24h=float(pair.get("priceChange", {}).get("h24", 0) or 0),
                image_url=pair.get("info", {}).get("imageUrl"),
                website=pair.get("info", {}).get("websites", [{}])[0].get("url") if pair.get("info", {}).get("websites") else None,
                twitter=pair.get("info", {}).get("socials", [{}])[0].get("url") if pair.get("info", {}).get("socials") else None,
            )
        except Exception as e:
            logger.debug(f"Parse error: {e}")
            return None
    
    def _parse_pumpfun_coin(self, coin: Dict[str, Any]) -> Optional[TokenInfo]:
        """Parse Pump.fun coin data into TokenInfo"""
        try:
            return TokenInfo(
                mint=coin.get("mint", ""),
                symbol=coin.get("symbol", "???"),
                name=coin.get("name", "Unknown"),
                market_cap_usd=float(coin.get("usd_market_cap", 0) or 0),
                image_url=coin.get("image_uri"),
                twitter=coin.get("twitter"),
                telegram=coin.get("telegram"),
                website=coin.get("website"),
            )
        except Exception as e:
            logger.debug(f"Parse error: {e}")
            return None
    
    def _parse_rugcheck_response(self, mint: str, data: Dict[str, Any]) -> RugCheckResult:
        """Parse RugCheck API response"""
        risks = data.get("risks", [])
        
        # Calculate risk scores
        honeypot_score = 0.0
        is_honeypot = False
        is_mintable = False
        is_freezable = False
        
        for risk in risks:
            name = risk.get("name", "").lower()
            level = risk.get("level", "").lower()
            
            if "honeypot" in name:
                is_honeypot = level in ["danger", "high"]
                honeypot_score = 0.9 if is_honeypot else 0.3
            
            if "mint" in name and "authority" in name:
                is_mintable = level in ["danger", "warning"]
            
            if "freeze" in name:
                is_freezable = level in ["danger", "warning"]
        
        token_meta = data.get("tokenMeta", {})
        
        return RugCheckResult(
            mint=mint,
            is_safe=not is_honeypot and not is_mintable,
            honeypot_score=honeypot_score,
            overall_risk=honeypot_score,
            is_honeypot=is_honeypot,
            is_mintable=is_mintable,
            is_freezable=is_freezable,
            mint_authority_revoked=not is_mintable,
            freeze_authority_revoked=not is_freezable,
            top10_holder_pct=data.get("topHoldersPercent", 100),
            raw_data=data,
        )
    
    def _passes_initial_filter(self, token: TokenInfo) -> bool:
        """Basic filtering before full vetting"""
        # Minimum liquidity check
        if token.liquidity_usd < TradingThresholds.MIN_LIQUIDITY_USD:
            return False
        
        # Skip if no price data
        if token.price_usd <= 0:
            return False
        
        return True


# Singleton instance
_scout_agent: Optional[ScoutAgent] = None


def get_scout_agent() -> ScoutAgent:
    """Get or create the scout agent singleton"""
    global _scout_agent
    if _scout_agent is None:
        _scout_agent = ScoutAgent()
    return _scout_agent
