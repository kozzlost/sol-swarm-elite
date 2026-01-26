"""
SOL-SWARM Elite - Main Entry Point
Streamlit Dashboard for AI-powered Solana memecoin trading.

Run with: streamlit run main.py
"""

import streamlit as st
import asyncio
import logging
from datetime import datetime, timezone
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="SOL-SWARM Elite",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load environment
from dotenv import load_dotenv
load_dotenv()

from src.command_center import get_command_center
from src.constants import PAPER_TRADING, MAINNET_ENABLED, ACTIVE_STRATEGY, RISK_WARNING


# =============================================================================
# SESSION STATE
# =============================================================================

if 'command_center' not in st.session_state:
    st.session_state.command_center = None
    st.session_state.is_running = False


def get_cc():
    """Get or create command center"""
    if st.session_state.command_center is None:
        st.session_state.command_center = get_command_center()
    return st.session_state.command_center


# =============================================================================
# HEADER
# =============================================================================

st.title("🤖 SOL-SWARM Elite")
st.caption("AI-Powered Solana Memecoin Research Lab")

# Mode indicator
mode_col1, mode_col2, mode_col3 = st.columns([1, 1, 2])

with mode_col1:
    if MAINNET_ENABLED:
        st.error("🔴 MAINNET MODE")
    else:
        st.success("📝 PAPER TRADING")

with mode_col2:
    st.info(f"📊 Strategy: {ACTIVE_STRATEGY.value.upper()}")


# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.header("⚙️ Controls")
    
    # Start/Stop buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("▶️ Start", use_container_width=True, type="primary"):
            cc = get_cc()
            asyncio.run(cc.start())
            st.session_state.is_running = True
            st.rerun()
    
    with col2:
        if st.button("⏹️ Stop", use_container_width=True):
            cc = get_cc()
            asyncio.run(cc.stop())
            st.session_state.is_running = False
            st.rerun()
    
    st.divider()
    
    # Pause/Resume
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⏸️ Pause", use_container_width=True):
            cc = get_cc()
            asyncio.run(cc.pause())
    
    with col2:
        if st.button("▶️ Resume", use_container_width=True):
            cc = get_cc()
            asyncio.run(cc.resume())
    
    st.divider()
    
    # Agent spawning
    st.subheader("🐝 Swarm Control")
    agent_count = st.slider("Agents to spawn", 5, 50, 10)
    
    if st.button("🐝 Spawn Agents", use_container_width=True):
        cc = get_cc()
        asyncio.run(cc.spawn_agents(agent_count))
        st.success(f"Spawned {agent_count} agents")
    
    st.divider()
    
    # Emergency controls
    st.subheader("🚨 Emergency")
    
    if st.button("🔴 SELL ALL", use_container_width=True, type="secondary"):
        cc = get_cc()
        asyncio.run(cc.force_sell_all())
        st.warning("Emergency sell triggered!")
    
    st.divider()
    
    # Risk warning
    if MAINNET_ENABLED:
        st.error("""
        ⚠️ **MAINNET TRADING ACTIVE**
        
        Real funds at risk!
        90%+ of memecoins fail.
        Only trade what you can lose.
        """)


# =============================================================================
# MAIN DASHBOARD
# =============================================================================

# Get dashboard data
cc = get_cc()
data = cc.get_dashboard_data()

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Overview",
    "💰 Treasury",
    "🐝 Swarm",
    "📈 Positions",
    "📜 History"
])


# -----------------------------------------------------------------------------
# TAB 1: OVERVIEW
# -----------------------------------------------------------------------------

with tab1:
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Paper Balance",
            f"{data['paper_balance']:.4f} SOL",
            delta=f"{data['stats']['trades_executed']} trades"
        )
    
    with col2:
        st.metric(
            "Active Positions",
            data['stats']['active_positions'],
            delta=f"{data['stats']['pending_signals']} pending"
        )
    
    with col3:
        st.metric(
            "Tokens Discovered",
            data['stats']['tokens_discovered'],
            delta=f"{data['stats']['discovery_cycles']} cycles"
        )
    
    with col4:
        st.metric(
            "Signals Generated",
            data['stats']['signals_generated']
        )
    
    st.divider()
    
    # System status
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔄 System Status")
        
        status_data = {
            "Mode": data['system']['mode'].upper(),
            "Running": "✅ Yes" if data['system']['is_running'] else "❌ No",
            "Paused": "⏸️ Yes" if data['system']['is_paused'] else "▶️ No",
            "Uptime": f"{int(data['system']['uptime_secs'] // 60)} minutes"
        }
        
        for key, value in status_data.items():
            st.text(f"{key}: {value}")
    
    with col2:
        st.subheader("📊 Quick Stats")
        
        if data['swarm']:
            swarm = data['swarm']
            st.text(f"Active Agents: {swarm.get('active_agents', 0)}")
            st.text(f"Total P&L: {swarm.get('total_pnl', 0):.4f} SOL")
            st.text(f"Win Rate: {swarm.get('overall_win_rate', 0):.1f}%")
            st.text(f"Best Agent: {swarm.get('best_agent', 'N/A')}")


# -----------------------------------------------------------------------------
# TAB 2: TREASURY
# -----------------------------------------------------------------------------

with tab2:
    st.subheader("💰 $AGENT Token Treasury")
    
    treasury = data['treasury']
    
    # Fee distribution chart
    col1, col2 = st.columns([2, 1])
    
    with col1:
        fig = go.Figure(data=[go.Pie(
            labels=['Bot Trading', 'Infrastructure', 'Development', 'Builder'],
            values=[
                treasury['bot_trading'],
                treasury['infrastructure'],
                treasury['development'],
                treasury['builder']
            ],
            hole=0.4,
            marker_colors=['#00D4AA', '#FF6B6B', '#4ECDC4', '#FFE66D']
        )])
        
        fig.update_layout(
            title="Fee Distribution",
            showlegend=True,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.metric("Total Fees Collected", f"{treasury['total_fees']:.6f} SOL")
        
        st.divider()
        
        st.caption("**Bucket Balances**")
        st.text(f"🤖 Bot Trading: {treasury['bot_trading']:.6f} SOL")
        st.text(f"🖥️ Infrastructure: {treasury['infrastructure']:.6f} SOL")
        st.text(f"💻 Development: {treasury['development']:.6f} SOL")
        st.text(f"👤 Builder: {treasury['builder']:.6f} SOL")
    
    # Flywheel explanation
    with st.expander("📖 How the Flywheel Works"):
        st.markdown("""
        ### $AGENT Token Fee Model
        
        Every $AGENT trade generates a **2% fee** that's split:
        
        - **25% Bot Trading** → Funds the AI trading agents
        - **25% Infrastructure** → Server costs, AI APIs
        - **25% Development** → Future improvements
        - **25% Builder** → Your income
        
        **The Flywheel:**
        ```
        More Trading → More Fees → Better Bots → Better Returns → More Users → More Trading
        ```
        """)


# -----------------------------------------------------------------------------
# TAB 3: SWARM
# -----------------------------------------------------------------------------

with tab3:
    st.subheader("🐝 Agent Swarm")
    
    swarm = data['swarm']
    
    # Swarm metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Agents", swarm.get('total_agents', 0))
    
    with col2:
        st.metric("Active", swarm.get('active_agents', 0))
    
    with col3:
        st.metric("Total P&L", f"{swarm.get('total_pnl', 0):.4f} SOL")
    
    with col4:
        st.metric("Win Rate", f"{swarm.get('overall_win_rate', 0):.1f}%")
    
    st.divider()
    
    # Leaderboard
    st.subheader("🏆 Agent Leaderboard")
    
    leaderboard = data.get('leaderboard', [])
    
    if leaderboard:
        df = pd.DataFrame(leaderboard)
        
        # Style the dataframe
        def style_pnl(val):
            color = 'green' if val > 0 else 'red' if val < 0 else 'gray'
            return f'color: {color}'
        
        st.dataframe(
            df,
            column_config={
                "rank": st.column_config.NumberColumn("Rank", width="small"),
                "name": st.column_config.TextColumn("Agent", width="medium"),
                "strategy": st.column_config.TextColumn("Strategy", width="medium"),
                "pnl": st.column_config.NumberColumn("P&L (SOL)", format="%.4f"),
                "roi": st.column_config.NumberColumn("ROI %", format="%.1f%%"),
                "win_rate": st.column_config.NumberColumn("Win Rate", format="%.1f%%"),
                "trades": st.column_config.NumberColumn("Trades", width="small"),
                "status": st.column_config.TextColumn("Status", width="small"),
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("No agents spawned yet. Use the sidebar to spawn agents.")


# -----------------------------------------------------------------------------
# TAB 4: POSITIONS
# -----------------------------------------------------------------------------

with tab4:
    st.subheader("📈 Open Positions")
    
    positions = data.get('positions', [])
    
    if positions:
        for pos in positions:
            col1, col2, col3, col4 = st.columns(4)
            
            pnl_color = "green" if pos['pnl_pct'] > 0 else "red"
            
            with col1:
                st.text(f"${pos['symbol']}")
            
            with col2:
                st.text(f"Entry: ${pos['entry']:.6f}")
            
            with col3:
                st.text(f"Current: ${pos['current']:.6f}")
            
            with col4:
                st.markdown(f"P&L: <span style='color:{pnl_color}'>{pos['pnl_pct']:.2f}%</span>", unsafe_allow_html=True)
            
            st.divider()
    else:
        st.info("No open positions")


# -----------------------------------------------------------------------------
# TAB 5: HISTORY
# -----------------------------------------------------------------------------

with tab5:
    st.subheader("📜 Recent Trades")
    
    trades = data.get('recent_trades', [])
    
    if trades:
        df = pd.DataFrame(trades)
        
        st.dataframe(
            df,
            column_config={
                "symbol": st.column_config.TextColumn("Token"),
                "action": st.column_config.TextColumn("Action"),
                "amount": st.column_config.NumberColumn("Amount (SOL)", format="%.4f"),
                "pnl": st.column_config.NumberColumn("P&L (SOL)", format="%.4f"),
                "status": st.column_config.TextColumn("Status"),
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("No trades executed yet")


# =============================================================================
# FOOTER
# =============================================================================

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.caption("SOL-SWARM Elite v1.0")

with col2:
    st.caption("$AGENT Token Powered")

with col3:
    st.caption("[GitHub](https://github.com/kozzlost/sol-swarm-elite)")


# =============================================================================
# AUTO-REFRESH
# =============================================================================

# Auto-refresh every 10 seconds when running
if st.session_state.is_running:
    import time
    time.sleep(10)
    st.rerun()
