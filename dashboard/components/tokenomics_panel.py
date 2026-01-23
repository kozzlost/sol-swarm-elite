"""
$AGENT Tokenomics Dashboard Component
Displays fee distribution, treasury status, and flywheel metrics
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional

# Import our tokenomics modules
import sys
sys.path.insert(0, '..')
from src.tokenomics.agent_token import get_token_manager, TokenomicsConfig, configure_token_manager
from src.agents.treasury_agent import get_treasury_agent


def render_tokenomics_header():
    """Render the $AGENT token header section"""
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h1 style="color: white; margin: 0;">🪙 $AGENT Token Dashboard</h1>
        <p style="color: rgba(255,255,255,0.8); margin: 5px 0 0 0;">
            Fee-powered flywheel funding 100 AI trading agents
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_fee_distribution_chart():
    """Render the 25/25/25/25 fee distribution pie chart"""
    token_manager = get_token_manager()
    treasury = token_manager.get_treasury_status()
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("💰 Fee Distribution (25/25/25/25)")
        
        labels = ['Bot Trading', 'Infrastructure', 'Development', 'Builder Income']
        values = [
            treasury['buckets']['bot_trading']['balance'],
            treasury['buckets']['infrastructure']['balance'],
            treasury['buckets']['development']['balance'],
            treasury['buckets']['builder']['balance']
        ]
        colors = ['#00D4AA', '#FF6B6B', '#4ECDC4', '#FFE66D']
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values if sum(values) > 0 else [25, 25, 25, 25],
            hole=0.6,
            marker_colors=colors,
            textinfo='label+percent',
            textposition='outside'
        )])
        
        fig.update_layout(
            showlegend=False,
            annotations=[dict(
                text=f"{sum(values):.4f}<br>SOL",
                x=0.5, y=0.5,
                font_size=20,
                showarrow=False
            )],
            margin=dict(t=0, b=0, l=0, r=0),
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📊 Bucket Breakdown")
        
        for bucket_name, bucket_data in treasury['buckets'].items():
            with st.container():
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.markdown(f"**{bucket_name.replace('_', ' ').title()}**")
                    st.caption(bucket_data['purpose'])
                with col_b:
                    st.metric(
                        label="Balance",
                        value=f"{bucket_data['balance']:.4f} SOL"
                    )
                st.divider()


def render_treasury_metrics():
    """Render treasury agent performance metrics"""
    treasury_agent = get_treasury_agent()
    report = treasury_agent.get_status_report()
    
    st.subheader("🏦 Treasury Status")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Capital",
            f"{report['summary']['total_capital']:.4f} SOL",
            delta=f"{report['summary']['total_pnl']:.4f}" if report['summary']['total_pnl'] != 0 else None
        )
    
    with col2:
        st.metric(
            "Utilization",
            f"{report['summary']['utilization_pct']:.1f}%",
        )
    
    with col3:
        st.metric(
            "Active Agents",
            f"{report['agent_count']} / {report['max_agents']}",
        )
    
    with col4:
        roi_color = "normal" if report['summary']['total_roi_pct'] >= 0 else "inverse"
        st.metric(
            "Total ROI",
            f"{report['summary']['total_roi_pct']:.2f}%",
            delta_color=roi_color
        )


def render_agent_allocations_table():
    """Render table of all agent allocations"""
    treasury_agent = get_treasury_agent()
    report = treasury_agent.get_status_report()
    
    if not report['allocations']:
        st.info("No agents allocated yet. Fees will fund new agent deployments.")
        return
    
    st.subheader("🤖 Agent Allocations")
    
    df = pd.DataFrame(report['allocations'])
    
    # Format columns
    df['allocated_sol'] = df['allocated_sol'].apply(lambda x: f"{x:.4f}")
    df['current_value'] = df['current_value'].apply(lambda x: f"{x:.4f}")
    df['pnl'] = df['pnl'].apply(lambda x: f"{x:+.4f}")
    df['roi_pct'] = df['roi_pct'].apply(lambda x: f"{x:+.2f}%")
    df['win_rate'] = df['win_rate'].apply(lambda x: f"{x*100:.1f}%")
    
    # Color code ROI
    st.dataframe(
        df[['agent_id', 'agent_type', 'allocated_sol', 'pnl', 'roi_pct', 'trades', 'win_rate']],
        use_container_width=True,
        hide_index=True
    )


def render_flywheel_visualization():
    """Render the flywheel effect visualization"""
    token_manager = get_token_manager()
    flywheel = token_manager.get_flywheel_metrics()
    
    st.subheader("🔄 Flywheel Effect")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Flywheel diagram using Sankey
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=[
                    "$AGENT Trading",
                    "Transaction Fees",
                    "Bot Capital",
                    "Infrastructure",
                    "Development",
                    "Builder",
                    "More Trades",
                    "Better Agents",
                    "More Users"
                ],
                color=[
                    "#667eea", "#764ba2",
                    "#00D4AA", "#FF6B6B", "#4ECDC4", "#FFE66D",
                    "#00D4AA", "#4ECDC4", "#764ba2"
                ]
            ),
            link=dict(
                source=[0, 1, 1, 1, 1, 2, 3, 4, 6, 7, 8],
                target=[1, 2, 3, 4, 5, 6, 7, 8, 0, 0, 0],
                value=[100, 25, 25, 25, 25, 25, 25, 25, 20, 15, 10]
            )
        )])
        
        fig.update_layout(
            title_text="Fee → Capital → Growth Flywheel",
            font_size=12,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### Flywheel Metrics")
        
        st.metric(
            "Bot Trading Capital",
            f"{flywheel['bot_trading_capital']:.4f} SOL"
        )
        
        st.metric(
            "Additional Trades Enabled",
            f"{flywheel['additional_trades_enabled']:,}"
        )
        
        st.metric(
            "Potential Recursive Fees",
            f"{flywheel['potential_recursive_fees']:.6f} SOL"
        )
        
        st.metric(
            "Infrastructure Runway",
            f"{flywheel['infrastructure_runway_days']:.1f} days"
        )
        
        st.metric(
            "Dev Hours Funded",
            f"{flywheel['development_hours_funded']:.1f} hrs"
        )


def render_fee_history_chart():
    """Render fee collection history over time"""
    token_manager = get_token_manager()
    
    if not token_manager.fee_history:
        st.info("No fee history yet. Fees will appear after trading activity.")
        return
    
    st.subheader("📈 Fee Collection History")
    
    # Convert to DataFrame
    df = pd.DataFrame([
        {
            'timestamp': f.timestamp,
            'total_fee': f.total_fee,
            'bot_trading': f.bot_trading,
            'infrastructure': f.infrastructure,
            'development': f.development,
            'builder': f.builder
        }
        for f in token_manager.fee_history
    ])
    
    # Cumulative sum
    df['cumulative_total'] = df['total_fee'].cumsum()
    df['cumulative_bot'] = df['bot_trading'].cumsum()
    df['cumulative_infra'] = df['infrastructure'].cumsum()
    df['cumulative_dev'] = df['development'].cumsum()
    df['cumulative_builder'] = df['builder'].cumsum()
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['cumulative_bot'],
        name='Bot Trading',
        stackgroup='one',
        fillcolor='rgba(0, 212, 170, 0.5)'
    ))
    
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['cumulative_infra'],
        name='Infrastructure',
        stackgroup='one',
        fillcolor='rgba(255, 107, 107, 0.5)'
    ))
    
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['cumulative_dev'],
        name='Development',
        stackgroup='one',
        fillcolor='rgba(78, 205, 196, 0.5)'
    ))
    
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['cumulative_builder'],
        name='Builder',
        stackgroup='one',
        fillcolor='rgba(255, 230, 109, 0.5)'
    ))
    
    fig.update_layout(
        title='Cumulative Fee Distribution Over Time',
        xaxis_title='Time',
        yaxis_title='SOL',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_agent_performance_by_type():
    """Render performance breakdown by agent type"""
    treasury_agent = get_treasury_agent()
    report = treasury_agent.get_status_report()
    
    if not report['performance_by_type']:
        return
    
    st.subheader("📊 Performance by Agent Type")
    
    df = pd.DataFrame([
        {
            'Agent Type': agent_type,
            'Total PnL': data['total_pnl'],
            'Total Trades': data['total_trades'],
            'Win Rate': data['total_wins'] / max(data['total_trades'], 1) * 100
        }
        for agent_type, data in report['performance_by_type'].items()
    ])
    
    fig = make_subplots(rows=1, cols=2, specs=[[{"type": "bar"}, {"type": "bar"}]])
    
    fig.add_trace(
        go.Bar(x=df['Agent Type'], y=df['Total PnL'], name='PnL (SOL)'),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(x=df['Agent Type'], y=df['Win Rate'], name='Win Rate %'),
        row=1, col=2
    )
    
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)


def render_wallet_config():
    """Render wallet configuration panel"""
    st.subheader("⚙️ Wallet Configuration")
    
    token_manager = get_token_manager()
    config = token_manager.config
    
    with st.expander("Configure Fee Wallets", expanded=False):
        st.warning("⚠️ Set your Solana wallet addresses for fee distribution")
        
        col1, col2 = st.columns(2)
        
        with col1:
            bot_wallet = st.text_input(
                "Bot Trading Wallet",
                value=config.bot_trading_wallet,
                placeholder="Your Solana wallet address"
            )
            
            infra_wallet = st.text_input(
                "Infrastructure Wallet",
                value=config.infrastructure_wallet,
                placeholder="For server/API costs"
            )
        
        with col2:
            dev_wallet = st.text_input(
                "Development Wallet",
                value=config.development_wallet,
                placeholder="For freelance devs"
            )
            
            builder_wallet = st.text_input(
                "Builder Wallet (You)",
                value=config.builder_wallet,
                placeholder="Your income wallet"
            )
        
        if st.button("Save Wallet Configuration"):
            new_config = TokenomicsConfig(
                bot_trading_wallet=bot_wallet,
                infrastructure_wallet=infra_wallet,
                development_wallet=dev_wallet,
                builder_wallet=builder_wallet
            )
            configure_token_manager(new_config)
            st.success("Wallets configured!")


def render_tokenomics_dashboard():
    """Main entry point - render the full tokenomics dashboard"""
    render_tokenomics_header()
    
    # Top metrics row
    render_treasury_metrics()
    
    st.divider()
    
    # Fee distribution and breakdown
    render_fee_distribution_chart()
    
    st.divider()
    
    # Flywheel visualization
    render_flywheel_visualization()
    
    st.divider()
    
    # Agent allocations
    render_agent_allocations_table()
    
    # Performance by type
    render_agent_performance_by_type()
    
    st.divider()
    
    # Fee history
    render_fee_history_chart()
    
    st.divider()
    
    # Configuration
    render_wallet_config()


# For direct execution/testing
if __name__ == "__main__":
    st.set_page_config(
        page_title="$AGENT Tokenomics",
        page_icon="🪙",
        layout="wide"
    )
    render_tokenomics_dashboard()
