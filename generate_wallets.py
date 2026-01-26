#!/usr/bin/env python3
"""
Generate Solana wallets for $AGENT fee distribution.
Creates 4 wallets for the 25/25/25/25 split.

Run: python generate_wallets.py
"""

import json
import os
from datetime import datetime

try:
    import base58
    from solders.keypair import Keypair
except ImportError:
    print("Installing required packages...")
    os.system("pip install solders base58")
    import base58
    from solders.keypair import Keypair


def generate_wallet():
    """Generate a new Solana keypair"""
    kp = Keypair()
    return {
        "pubkey": str(kp.pubkey()),
        "secret": base58.b58encode(bytes(kp)).decode()
    }


def main():
    print("\n" + "=" * 60)
    print("🔐 $AGENT FEE WALLET GENERATOR")
    print("=" * 60 + "\n")
    
    wallets = {}
    wallet_names = [
        ("bot_trading", "Bot Trading Treasury", "25%"),
        ("infrastructure", "Infrastructure Fund", "25%"),
        ("development", "Development Fund", "25%"),
        ("builder", "Builder Income", "25%"),
    ]
    
    print("Generating 4 wallets for fee distribution...\n")
    
    for key, name, pct in wallet_names:
        wallet = generate_wallet()
        wallets[key] = wallet
        print(f"✅ {name} ({pct}):")
        print(f"   Address: {wallet['pubkey']}")
        print()
    
    # Save private keys (SECURE THIS FILE!)
    secrets_file = "wallets_SECRET.json"
    with open(secrets_file, "w") as f:
        json.dump({
            "generated_at": datetime.now().isoformat(),
            "warning": "KEEP THIS FILE SECURE - NEVER SHARE PRIVATE KEYS",
            "wallets": wallets
        }, f, indent=2)
    
    print(f"🔒 Private keys saved to: {secrets_file}")
    print("   ⚠️  BACK THIS UP SECURELY - DO NOT SHARE!\n")
    
    # Generate .env snippet
    env_snippet = f"""
# =============================================================================
# $AGENT Fee Distribution Wallets (Generated {datetime.now().strftime('%Y-%m-%d %H:%M')})
# =============================================================================

# Bot Trading Treasury (25% of fees)
BOT_TRADING_WALLET={wallets['bot_trading']['pubkey']}

# Infrastructure Fund (25% of fees)
INFRASTRUCTURE_WALLET={wallets['infrastructure']['pubkey']}

# Development Fund (25% of fees)
DEVELOPMENT_WALLET={wallets['development']['pubkey']}

# Builder Income (25% of fees)
BUILDER_WALLET={wallets['builder']['pubkey']}
"""
    
    print("=" * 60)
    print("📋 ADD TO YOUR .env FILE:")
    print("=" * 60)
    print(env_snippet)
    
    # Save .env snippet
    with open("wallets.env", "w") as f:
        f.write(env_snippet)
    
    print(f"\n✅ Environment snippet saved to: wallets.env")
    print("   Copy these lines to your .env file\n")
    
    print("=" * 60)
    print("🚀 NEXT STEPS:")
    print("=" * 60)
    print("""
1. SECURE wallets_SECRET.json (backup offline, never share)
2. Copy wallet addresses from wallets.env to your .env
3. Fund the wallets with SOL for transaction fees
4. Deploy $AGENT token on pump.fun
5. Update AGENT_TOKEN_MINT in .env with the token address
6. Start the swarm: streamlit run main.py
""")


if __name__ == "__main__":
    main()
