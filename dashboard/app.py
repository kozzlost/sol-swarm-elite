"""
SOL-SWARM Elite Dashboard
=========================
Streamlit-based monitoring dashboard for the swarm trading system.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

# Page configuration
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
            font-size: 2.5rem;
                    font-weight: bold;
                            color: #9945FF;
                                    text-align: center;
                                            margin-bottom: 1rem;
                                                }
                                                    .warning-box {
                                                            background-color: #ff4444;
                                                                    color: white;
                                                                            padding: 1rem;
                                                                                    border-radius: 0.5rem;
                                                                                            margin-bottom: 1rem;
                                                                                                }
                                                                                                    .metric-card {
                                                                                                            background-color: #1E1E1E;
                                                                                                                    padding: 1rem;
                                                                                                                            border-radius: 0.5rem;
                                                                                                                                    border: 1px solid #333;
                                                                                                                                        }
                                                                                                                                        </style>
                                                                                                                                        """, unsafe_allow_html=True)


def main():
      """Main dashboard application."""

    # Header
      st.markdown('<h1 class="main-header">🤖 SOL-SWARM Elite Dashboard</h1>', unsafe_allow_html=True)

    # Risk Warning
      st.markdown("""
      <div class="warning-box">
          ⚠️ <strong>EXTREME RISK WARNING</strong>: This is for EDUCATIONAL/RESEARCH purposes ONLY. 
          90%+ of memecoins result in complete loss. NOT financial advice. NFA/DYOR.
      </div>
      """, unsafe_allow_html=True)

    # Sidebar
      with st.sidebar:
                st.image("https://raw.githubusercontent.com/solana-labs/token-list/main/assets/mainnet/So11111111111111111111111111111111111111112/logo.png", width=80)
                st.title("Control Panel")

        # Mode indicator
                mainnet_enabled = os.getenv("MAINNET_ENABLED", "false").lower() == "true"
                if mainnet_enabled:
                              st.error("🔴 MAINNET MODE - REAL FUNDS")
else:
            st.success("🟢 Paper Trading Mode")
              paper_balance = os.getenv("PAPER_BALANCE", "25.0")
            st.metric("Paper Balance", f"{paper_balance} SOL")

        st.divider()

        # Strategy selector
        strategy = st.selectbox(
                      "Active Strategy",
                      ["MOMENTUM", "GMGN_AI", "AXIOM_MIGRATION", "WHALE_COPY", "NOVA_JITO", "PUMP_GRADUATE"]
        )

        # Risk parameters
        st.subheader("Risk Parameters")
        max_position = st.slider("Max Position (SOL)", 0.01, 0.1, 0.05, 0.01)
        max_drawdown = st.slider("Max Drawdown %", 5, 30, 15, 5)

        st.divider()

        # System status
        st.subheader("System Status")
        st.write("🤖 Scout Agent: Active")
        st.write("📊 Sentiment Agent: Active")
        st.write("⚖️ Arbiter Agent: Active")
        st.write("🎯 Sniper Agent: Standby")
        st.write("💰 Sell Agent: Standby")

    # Main content area
    col1, col2, col3, col4 = st.columns(4)

    with col1:
              st.metric(
                            label="Total PnL",
                            value="+2.45 SOL",
                            delta="+12.3%"
              )

    with col2:
              st.metric(
                            label="Win Rate",
                            value="67%",
                            delta="+5%"
              )

    with col3:
              st.metric(
                            label="Active Positions",
                            value="2/3",
                            delta=None
              )

    with col4:
              st.metric(
                            label="Tokens Scanned",
                            value="1,247",
                            delta="+89 today"
              )

    st.divider()

    # Charts section
    tab1, tab2, tab3 = st.tabs(["📈 Performance", "🔍 Token Scanner", "📋 Activity Log"])

    with tab1:
              # Sample PnL chart
              st.subheader("Portfolio Performance")

        dates = pd.date_range(start=datetime.now() - timedelta(days=7), periods=168, freq='H')
        pnl_data = pd.DataFrame({
                      'Time': dates,
                      'PnL': [0] + list(pd.Series(range(167)).apply(lambda x: (x * 0.02) + (x % 10 - 5) * 0.1))
        })

        fig = px.line(pnl_data, x='Time', y='PnL', title='Cumulative PnL (SOL)')
        fig.update_layout(
                      template='plotly_dark',
                      xaxis_title="Time",
                      yaxis_title="PnL (SOL)"
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
              st.subheader("Recent Token Discoveries")

        # Sample token data
              tokens_df = pd.DataFrame({
                            'Symbol': ['$PEPE2', '$BONK2', '$WIF2', '$DOGE2', '$SHIB2'],
                            'Price': ['$0.00001234', '$0.00000567', '$0.0234', '$0.000089', '$0.00000012'],
                            'Liquidity': ['$45,000', '$123,000', '$89,000', '$67,000', '$34,000'],
                            'Sentiment': [7.8, 6.5, 8.2, 5.4, 4.1],
                            'Rug Score': [0.12, 0.23, 0.08, 0.45, 0.67],
                            'Action': ['✅ Passed', '✅ Passed', '✅ Passed', '⚠️ Caution', '❌ Rejected']
              })

        st.dataframe(tokens_df, use_container_width=True)

    with tab3:
              st.subheader("Agent Activity Log")

        log_entries = [
                      "🔍 [Scout] Scanning DexScreener for new pairs...",
                      "📊 [Sentiment] Analyzing X posts for $PEPE2...",
                      "⚖️ [Arbiter] Token $PEPE2 passed all checks, sentiment: 7.8",
                      "🎯 [Sniper] Simulating buy for $PEPE2 @ 0.00001234",
                      "✅ [System] Paper trade executed: 0.03 SOL -> $PEPE2",
                      "🔍 [Scout] New token detected: $BONK2",
                      "🛡️ [RugCheck] Analyzing $BONK2 contract...",
                      "✅ [RugCheck] $BONK2 passed: No mint authority, LP locked",
        ]

        for entry in log_entries:
                      st.text(entry)

    # Footer
    st.divider()
    st.caption("Made with ❤️ for the Solana community | SOL-SWARM Elite v1.0.0")
    st.caption("⚠️ Remember: 90%+ of memecoins fail. Never invest more than you can afford to lose.")


if __name__ == "__main__":
      main()
