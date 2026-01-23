#!/usr/bin/env python3
"""
Wallet Generator - Creates the 4 fee distribution wallets.
Run this ONCE to generate your wallet addresses.
"""

import os
import json
import base58
from datetime import datetime
from pathlib import Path

try:
    from solders.keypair import Keypair
except ImportError:
    print("Installing solders...")
    os.system("pip install solders")
    from solders.keypair import Keypair


def generate_wallet(name: str) -> dict:
    """Generate a new Solana wallet"""
    keypair = Keypair()
    return {
        "name": name,
        "pubkey": str(keypair.pubkey()),
        "secret_base58": base58.b58encode(bytes(keypair)).decode()
    }


def main():
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║         $AGENT FEE WALLET GENERATOR                       ║
    ║         Creates 4 wallets for 25/25/25/25 split           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Check if wallets already exist
    wallet_file = Path("wallets_secret.json")
    if wallet_file.exists():
        print("⚠️  wallets_secret.json already exists!")
        response = input("Generate new wallets? This will OVERWRITE existing. (yes/no): ")
        if response.lower() != "yes":
            print("Aborted.")
            return
    
    # Generate 4 wallets
    print("\n🔐 Generating wallets...\n")
    
    wallets = {
        "bot_trading": generate_wallet("Bot Trading (25%)"),
        "infrastructure": generate_wallet("Infrastructure (25%)"),
        "development": generate_wallet("Development (25%)"),
        "builder": generate_wallet("Builder Income (25%)")
    }
    
    # Save secret file (KEEP PRIVATE!)
    secret_data = {
        "generated_at": datetime.now().isoformat(),
        "WARNING": "KEEP THIS FILE SECRET! Anyone with these keys can access your funds.",
        "wallets": wallets
    }
    
    with open("wallets_secret.json", "w") as f:
        json.dump(secret_data, f, indent=2)
    
    # Create .env snippet
    env_snippet = f"""
# $AGENT Fee Distribution Wallets
# Generated: {datetime.now().isoformat()}
BOT_TRADING_WALLET={wallets['bot_trading']['pubkey']}
INFRASTRUCTURE_WALLET={wallets['infrastructure']['pubkey']}
DEVELOPMENT_WALLET={wallets['development']['pubkey']}
BUILDER_WALLET={wallets['builder']['pubkey']}
"""
    
    with open("wallets.env", "w") as f:
        f.write(env_snippet)
    
    # Display results
    print("=" * 60)
    print("WALLET ADDRESSES (Public - Safe to share)")
    print("=" * 60)
    
    for key, wallet in wallets.items():
        print(f"\n{wallet['name']}:")
        print(f"  {wallet['pubkey']}")
    
    print("\n" + "=" * 60)
    print("FILES CREATED")
    print("=" * 60)
    print(f"""
📁 wallets_secret.json
   Contains private keys - KEEP SECRET!
   Back this up securely.
   
📁 wallets.env
   Contains public addresses only.
   Copy these to your .env file.
""")
    
    print("=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print(f"""
1. BACKUP wallets_secret.json to a secure location
   (Password manager, encrypted drive, etc.)

2. Copy wallet addresses to .env:
   cat wallets.env >> .env

3. Fund the BOT_TRADING wallet with initial capital
   (This wallet funds your AI agents)

4. Launch $AGENT token on pump.fun
   Use any of these wallets as the creator

5. Add wallets_secret.json to .gitignore:
   echo "wallets_secret.json" >> .gitignore

⚠️  NEVER commit wallets_secret.json to git!
⚠️  NEVER share your private keys!
""")
    
    # Add to gitignore
    gitignore = Path(".gitignore")
    if gitignore.exists():
        content = gitignore.read_text()
        if "wallets_secret.json" not in content:
            with open(".gitignore", "a") as f:
                f.write("\n# Secret wallet keys\nwallets_secret.json\n")
            print("✓ Added wallets_secret.json to .gitignore")
    
    print("\n✅ Wallet generation complete!")


if __name__ == "__main__":
    main()
