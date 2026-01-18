"""Swarm state management"""
from typing import TypedDict, List, Optional, Dict, Any
class AgentMessage(TypedDict):
    agent: str
    content: str
