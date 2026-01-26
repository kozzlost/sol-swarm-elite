"""
SOL-SWARM Elite - AI-Powered Solana Memecoin Trading System
"""

__version__ = "1.0.0"
__author__ = "kozzlost"

from src.constants import PAPER_TRADING, MAINNET_ENABLED, ACTIVE_STRATEGY
from src.command_center import CommandCenter, get_command_center

__all__ = [
    "CommandCenter",
    "get_command_center",
    "PAPER_TRADING",
    "MAINNET_ENABLED",
    "ACTIVE_STRATEGY",
]
