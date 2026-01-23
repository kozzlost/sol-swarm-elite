#!/usr/bin/env python3
"""
SOL-SWARM Elite - Main Entry Point
Launches the Streamlit dashboard with full $AGENT tokenomics integration.
"""

import streamlit as st
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="SOL-SWARM Elite",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        color: white;
    }
    .warning-banner {
        background: #ff6b6b;
        color: white;
        padding: 10px;
        border-radius: 5px;
        text-align: center;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

from src.agents.agent_spawner import get_agent_spawner, AgentStrategy
from src.tokenomics.agent_token import get_token_manager
from src.tokenomics.fee_collector import get_fee_collector
from src.agents.treasury_agent import get_treasury_agent

# Header
st.markdown("""
<div class="main-header">
    <h1>🤖 SOL-SWARM Elite Command Center</h1>
    <p>AI-Powered Memecoin Research Lab | $AGENT Token Funded | 100 Agent Swarm</p>
</div>
<div class="warning-banner">
    ⚠️ RESEARCH/EDUCATIONAL USE ONLY - 90%+ rug probability - NFA/DYOR
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("🎮 Control Panel")
    
    mainnet = st.toggle(
        "🔴 MAINNET MODE",
        value=os.getenv("MAINNET_ENABLED", "false").lower() == "true"
    )
    
    if mainnet:
        st.error("⚠️ REAL FUNDS AT RISK")
    else:
        st.success("✅ Paper Trading Mode")
    
    st.divider()
    
    st.subheader("Spawn Agent")
    strategy = st.selectbox("Strategy", [s.value for s in AgentStrategy])
    capital = st.number_input("Capital (SOL)", min_value=0.01, value=0.05, step=0.01)
    
    if st.button("➕ Spawn Agent", use_container_width=True):
        spawner = get_agent_spawner()
        agent = asyncio.run(spawner.spawn_agent(AgentStrategy(strategy), capital))
        if agent:
            st.success(f"Spawned {agent.name}!")
        else:
            st.error("Failed to spawn")

# Main metrics
spawner = get_agent_spawner()
token_manager = get_token_manager()
fee_collector = get_fee_collector()
treasury = get_treasury_agent()

swarm = spawner.get_swarm_status()
fees = token_manager.get_treasury_status()
flywheel = token_manager.get_flywheel_metrics()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("🤖 Agents", f"{swarm['active_agents']}/{swarm['max_agents']}")
col2.metric("💰 Capital", f"{swarm['total_capital']:.4f} SOL")
col3.metric("📈 PnL", f"{swarm['total_pnl']:+.4f} SOL")
col4.metric("💸 Fees Collected", f"{fees['total_fees_collected']:.6f} SOL")
col5.metric("🔄 Trades Today", f"{swarm['total_trades_today']}")

st.divider()

# Tabs for different views
tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "🪙 $AGENT Tokenomics", "🤖 Agent Swarm", "📜 Trade Log"])

with tab1:
    st.subheader("Fee Distribution (25/25/25/25)")
    
    import plotly.graph_objects as go
    
    labels = ['Bot Trading', 'Infrastructure', 'Development', 'Builder']
    values = [
        fees['buckets']['bot_trading']['balance'],
        fees['buckets']['infrastructure']['balance'],
        fees['buckets']['development']['balance'],
        fees['buckets']['builder']['balance']
    ]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values if sum(values) > 0 else [25, 25, 25, 25],
        hole=0.6,
        marker_colors=['#00D4AA', '#FF6B6B', '#4ECDC4', '#FFE66D']
    )])
    fig.update_layout(height=300, margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True)
    
    # Flywheel metrics
    st.subheader("🔄 Flywheel Effect")
    fc1, fc2, fc3, fc4 = st.columns(4)
    fc1.metric("Bot Capital", f"{flywheel['bot_trading_capital']:.4f} SOL")
    fc2.metric("Trades Enabled", f"{flywheel['additional_trades_enabled']}")
    fc3.metric("Infra Runway", f"{flywheel['infrastructure_runway_days']:.0f} days")
    fc4.metric("Dev Hours", f"{flywheel['development_hours_funded']:.1f} hrs")

with tab2:
    st.subheader("$AGENT Token Configuration")
    
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Token Mint", value=token_manager.config.token_mint or "Not deployed yet")
        st.number_input("Fee Rate (bps)", value=token_manager.config.transaction_fee_bps, disabled=True)
    
    with col2:
        st.text_input("Bot Wallet", value=token_manager.config.bot_trading_wallet or "Not set")
        st.text_input("Builder Wallet", value=token_manager.config.builder_wallet or "Not set")
    
    st.divider()
    
    st.subheader("Treasury Status")
    report = treasury.get_status_report()
    
    tcol1, tcol2, tcol3 = st.columns(3)
    tcol1.metric("Available", f"{report['summary']['available_capital']:.4f} SOL")
    tcol2.metric("Allocated", f"{report['summary']['allocated_capital']:.4f} SOL")
    tcol3.metric("Utilization", f"{report['summary']['utilization_pct']:.1f}%")

with tab3:
    st.subheader("Agent Swarm Status")
    
    if swarm['top_performers']:
        import pandas as pd
        df = pd.DataFrame(swarm['top_performers'])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No agents spawned yet. Use the sidebar to spawn your first agent!")
    
    st.divider()
    
    st.subheader("Strategy Distribution")
    strategy_data = []
    for strat, data in swarm['strategy_breakdown'].items():
        strategy_data.append({
            'Strategy': strat,
            'Count': data['count'],
            'Target': data['target'],
            'Capital': f"{data['total_capital']:.4f}",
            'PnL': f"{data['total_pnl']:+.4f}"
        })
    
    if strategy_data:
        st.dataframe(pd.DataFrame(strategy_data), use_container_width=True, hide_index=True)

with tab4:
    st.subheader("Recent Trades")
    
    trades = fee_collector.get_recent_trades(50)
    if trades:
        import pandas as pd
        df = pd.DataFrame(trades)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No trades recorded yet.")

# Footer
st.divider()
st.caption("SOL-SWARM Elite v1.0 | $AGENT Token Powered | MIT License | github.com/kozzlost/sol-swarm-elite")
