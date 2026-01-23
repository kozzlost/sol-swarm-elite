"""
$AGENT Token Launch Script for Pump.fun
Deploys the token and configures fee collection.
"""

import asyncio
import os
import json
from datetime import datetime
from dataclasses import dataclass
from typing import Optional
import base58
import logging

from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from solders.keypair import Keypair
from solders.pubkey import Pubkey

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TokenLaunchConfig:
    """Configuration for $AGENT token launch"""
    # Token metadata
    name: str = "Swarm Elite Agent"
    symbol: str = "AGENT"
    description: str = "AI-powered trading swarm with 100 agents. Fees fund the bots that trade for you."
    image_url: str = ""  # Set your token image URL
    
    # Tokenomics
    total_supply: int = 1_000_000_000  # 1 billion
    decimals: int = 9
    
    # Fee wallets (25% each)
    bot_trading_wallet: str = ""
    infrastructure_wallet: str = ""
    development_wallet: str = ""
    builder_wallet: str = ""
    
    # Initial liquidity
    initial_sol_liquidity: float = 1.0  # SOL to seed LP
    
    # Pump.fun settings
    pump_fun_fee_bps: int = 100  # 1% pump.fun fee
    
    def validate(self) -> bool:
        """Validate all required fields are set"""
        required = [
            self.bot_trading_wallet,
            self.infrastructure_wallet, 
            self.development_wallet,
            self.builder_wallet
        ]
        if not all(required):
            raise ValueError("All 4 fee wallets must be configured")
        return True


class PumpFunLauncher:
    """
    Handles $AGENT token deployment on Pump.fun
    
    Pump.fun provides:
    - Instant token creation
    - Built-in bonding curve
    - Automatic LP creation at graduation
    - Fee collection infrastructure
    """
    
    PUMP_FUN_PROGRAM = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
    
    def __init__(self, config: TokenLaunchConfig):
        self.config = config
        self.config.validate()
        self.client: Optional[AsyncClient] = None
        self.keypair: Optional[Keypair] = None
        
    async def connect(self, rpc_url: str, private_key: str):
        """Initialize connection and wallet"""
        self.client = AsyncClient(rpc_url, commitment=Confirmed)
        
        # Load keypair from base58 private key
        secret = base58.b58decode(private_key)
        self.keypair = Keypair.from_bytes(secret)
        
        balance = await self.client.get_balance(self.keypair.pubkey())
        logger.info(f"Connected wallet: {self.keypair.pubkey()}")
        logger.info(f"Balance: {balance.value / 1e9:.4f} SOL")
        
        if balance.value < self.config.initial_sol_liquidity * 1e9:
            raise ValueError(f"Insufficient balance for launch. Need {self.config.initial_sol_liquidity} SOL")
    
    def generate_launch_instructions(self) -> dict:
        """
        Generate instructions for manual pump.fun launch.
        
        Since pump.fun uses a web interface, this provides the exact
        parameters to use when creating the token.
        """
        return {
            "platform": "pump.fun",
            "url": "https://pump.fun/create",
            "instructions": [
                "1. Go to https://pump.fun/create",
                "2. Connect your Solana wallet",
                "3. Fill in token details (see below)",
                "4. Upload token image",
                "5. Click 'Create Token'",
                "6. Copy the token mint address",
                "7. Update .env with AGENT_TOKEN_MINT=<address>"
            ],
            "token_details": {
                "name": self.config.name,
                "symbol": self.config.symbol,
                "description": self.config.description,
                "image": self.config.image_url or "Upload your logo",
                "twitter": "https://twitter.com/your_handle",
                "telegram": "https://t.me/your_group",
                "website": "https://your-site.com"
            },
            "fee_wallet_setup": {
                "note": "After launch, set up fee routing to these wallets:",
                "bot_trading": self.config.bot_trading_wallet,
                "infrastructure": self.config.infrastructure_wallet,
                "development": self.config.development_wallet,
                "builder": self.config.builder_wallet
            },
            "post_launch_checklist": [
                "[ ] Copy token mint address to .env",
                "[ ] Verify token on Solscan",
                "[ ] Set up fee collection (see fee_router.py)",
                "[ ] Test paper trading first",
                "[ ] Announce on socials",
                "[ ] Monitor initial trades"
            ]
        }
    
    async def create_token_metadata(self) -> dict:
        """Generate token metadata JSON for upload"""
        metadata = {
            "name": self.config.name,
            "symbol": self.config.symbol,
            "description": self.config.description,
            "image": self.config.image_url,
            "attributes": [
                {"trait_type": "Type", "value": "AI Trading Token"},
                {"trait_type": "Max Agents", "value": "100"},
                {"trait_type": "Fee Model", "value": "25/25/25/25"},
                {"trait_type": "Platform", "value": "Solana"}
            ],
            "properties": {
                "fee_structure": {
                    "total_fee_bps": 200,
                    "distribution": {
                        "bot_trading": "25%",
                        "infrastructure": "25%",
                        "development": "25%",
                        "builder": "25%"
                    }
                },
                "wallets": {
                    "bot_trading": self.config.bot_trading_wallet,
                    "infrastructure": self.config.infrastructure_wallet,
                    "development": self.config.development_wallet,
                    "builder": self.config.builder_wallet
                }
            }
        }
        return metadata
    
    async def disconnect(self):
        if self.client:
            await self.client.close()


def create_launch_package(
    bot_wallet: str,
    infra_wallet: str,
    dev_wallet: str,
    builder_wallet: str,
    image_url: str = ""
) -> dict:
    """
    Create complete launch package for $AGENT token.
    
    Returns all info needed to launch on pump.fun
    """
    config = TokenLaunchConfig(
        bot_trading_wallet=bot_wallet,
        infrastructure_wallet=infra_wallet,
        development_wallet=dev_wallet,
        builder_wallet=builder_wallet,
        image_url=image_url
    )
    
    launcher = PumpFunLauncher(config)
    
    instructions = launcher.generate_launch_instructions()
    metadata = asyncio.run(launcher.create_token_metadata())
    
    return {
        "config": {
            "name": config.name,
            "symbol": config.symbol,
            "total_supply": config.total_supply,
            "decimals": config.decimals,
            "fee_bps": 200
        },
        "launch_instructions": instructions,
        "metadata": metadata,
        "env_template": f"""
# Add these to your .env after token launch:
AGENT_TOKEN_MINT=<paste_mint_address_here>
AGENT_FEE_BPS=200
BOT_TRADING_WALLET={bot_wallet}
INFRASTRUCTURE_WALLET={infra_wallet}
DEVELOPMENT_WALLET={dev_wallet}
BUILDER_WALLET={builder_wallet}
"""
    }


# CLI
if __name__ == "__main__":
    import sys
    
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║           $AGENT TOKEN LAUNCH PREPARATION                 ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Check for wallet arguments
    if len(sys.argv) < 5:
        print("Usage: python token_launch.py <bot_wallet> <infra_wallet> <dev_wallet> <builder_wallet>")
        print("\nExample:")
        print("  python token_launch.py ABC123... DEF456... GHI789... JKL012...")
        print("\nOr set in environment variables:")
        print("  BOT_TRADING_WALLET, INFRASTRUCTURE_WALLET, DEVELOPMENT_WALLET, BUILDER_WALLET")
        
        # Try env vars
        bot = os.getenv("BOT_TRADING_WALLET", "")
        infra = os.getenv("INFRASTRUCTURE_WALLET", "")
        dev = os.getenv("DEVELOPMENT_WALLET", "")
        builder = os.getenv("BUILDER_WALLET", "")
        
        if all([bot, infra, dev, builder]):
            print("\n✅ Found wallets in environment, proceeding...")
        else:
            print("\n❌ No wallets configured. Exiting.")
            sys.exit(1)
    else:
        bot = sys.argv[1]
        infra = sys.argv[2]
        dev = sys.argv[3]
        builder = sys.argv[4]
    
    # Generate launch package
    package = create_launch_package(bot, infra, dev, builder)
    
    # Print instructions
    print("\n📋 LAUNCH INSTRUCTIONS:")
    print("-" * 50)
    for step in package["launch_instructions"]["instructions"]:
        print(f"  {step}")
    
    print("\n🪙 TOKEN DETAILS:")
    print("-" * 50)
    for key, val in package["launch_instructions"]["token_details"].items():
        print(f"  {key}: {val}")
    
    print("\n💰 FEE WALLETS:")
    print("-" * 50)
    wallets = package["launch_instructions"]["fee_wallet_setup"]
    print(f"  Bot Trading (25%):    {wallets['bot_trading']}")
    print(f"  Infrastructure (25%): {wallets['infrastructure']}")
    print(f"  Development (25%):    {wallets['development']}")
    print(f"  Builder (25%):        {wallets['builder']}")
    
    print("\n✅ POST-LAUNCH CHECKLIST:")
    print("-" * 50)
    for item in package["launch_instructions"]["post_launch_checklist"]:
        print(f"  {item}")
    
    # Save metadata
    with open("agent_token_metadata.json", "w") as f:
        json.dump(package["metadata"], f, indent=2)
    print("\n💾 Metadata saved to: agent_token_metadata.json")
    
    print("\n" + package["env_template"])
    print("\n🚀 Ready to launch! Go to https://pump.fun/create")
