#!/usr/bin/env python3
"""
SOL-SWARM Elite - Main Entry Point
===================================
AI-powered Solana memecoin research and paper trading system.

⚠️ WARNING: This is for EDUCATIONAL/RESEARCH purposes ONLY.
90%+ of memecoins result in complete loss. NFA/DYOR.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def print_banner():
      """Display startup banner with risk warnings."""
      banner = """
      ╔═══════════════════════════════════════════════════════════════╗
      ║           🤖 SOL-SWARM Elite v1.0.0                           ║
      ║           Solana Memecoin Research Lab                        ║
      ╠═══════════════════════════════════════════════════════════════╣
      ║  ⚠️  EXTREME RISK WARNING ⚠️                                   ║
      ║  • 90%+ of memecoins result in COMPLETE LOSS                  ║
      ║  • This is NOT financial advice (NFA/DYOR)                    ║
      ║  • Paper trading mode is ON by default                        ║
      ║  • NEVER use real funds without extensive testing             ║
      ╚═══════════════════════════════════════════════════════════════╝
      """
      print(banner)


def check_environment():
      """Verify required environment variables."""
      mainnet_enabled = os.getenv("MAINNET_ENABLED", "false").lower() == "true"

    if mainnet_enabled:
              print("\n🔴 MAINNET MODE DETECTED - REAL FUNDS AT RISK!")
              private_key = os.getenv("SOLANA_PRIVATE_KEY", "")
              if not private_key:
                            print("❌ Error: SOLANA_PRIVATE_KEY required for mainnet")
                            sys.exit(1)
                        print("⚠️  Confirm you understand the risks before proceeding.")
else:
        print("\n🟢 Paper Trading Mode (Safe - No real funds)")
        paper_balance = os.getenv("PAPER_BALANCE", "25.0")
        print(f"📊 Starting paper balance: {paper_balance} SOL")

    return mainnet_enabled


async def run_swarm():
      """Initialize and run the swarm trading system."""
    from src.agents.scout_agent import ScoutAgent
    from src.agents.sentiment_agent import SentimentAgent
    from src.agents.arbiter_agent import ArbiterAgent
    from src.services.api_aggregator import APIAggregator

    # Initialize API aggregator
    api = APIAggregator(
              x_bearer_token=os.getenv("X_BEARER_TOKEN"),
              cielo_key=os.getenv("CIELO_API_KEY"),
              lunarcrush_key=os.getenv("LUNARCRUSH_API_KEY")
    )

    # Initialize agents
    scout = ScoutAgent()
    sentiment = SentimentAgent()
    arbiter = ArbiterAgent()

    print("\n🚀 Swarm agents initialized:")
    print("   • Scout Agent: Token discovery")
    print("   • Sentiment Agent: Social analysis")
    print("   • Arbiter Agent: Trading decisions")

    print("\n📡 Starting swarm loop...")
    print("   Press Ctrl+C to stop\n")

    try:
              while True:
                            # Scout for new tokens
                            tokens = await scout.scan_tokens()

            if tokens:
                              print(f"🔍 Found {len(tokens)} potential tokens")

                for token in tokens:
                                      # Analyze sentiment
                                      sentiment_data = await api.get_aggregated_data(
                                                                token.get("symbol", ""),
                                                                token.get("address", "")
                                      )
                                      print(f"   📊 {token.get('symbol')}: Sentiment score {sentiment_data.get('composite_score', 0):.2f}")

            # Wait before next scan
            await asyncio.sleep(30)

except KeyboardInterrupt:
        print("\n\n🛑 Swarm stopped by user")
finally:
        await api.close()


def run_dashboard():
      """Launch the Streamlit dashboard."""
    import subprocess
    print("\n🖥️  Starting dashboard on http://localhost:8501")
    subprocess.run(["streamlit", "run", "dashboard/app.py", "--server.port=8501"])


def main():
      """Main entry point."""
    print_banner()

    # Check command line arguments
    if len(sys.argv) > 1:
              command = sys.argv[1].lower()

        if command == "dashboard":
                      check_environment()
                      run_dashboard()
                      return
elif command == "help":
            print("Usage: python main.py [command]")
            print("\nCommands:")
            print("  (none)     Run the swarm trading system")
            print("  dashboard  Launch the Streamlit dashboard")
            print("  help       Show this help message")
            return

    # Default: run swarm
    mainnet = check_environment()

    if mainnet:
              confirm = input("\n⚠️  Type 'I UNDERSTAND THE RISKS' to continue: ")
        if confirm != "I UNDERSTAND THE RISKS":
                      print("❌ Confirmation failed. Exiting.")
                      sys.exit(1)

    print("\n" + "="*60)
    asyncio.run(run_swarm())


if __name__ == "__main__":
      main()
