#!/usr/bin/env python3
"""
💼 Portfolio Analytics Platform
Advanced portfolio optimization and risk management tools
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="💼 Portfolio Analytics Platform",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import our portfolio optimizer
try:
    from app.analytics.portfolio_optimizer import PortfolioOptimizer
except ImportError:
    st.error("Please ensure the portfolio optimizer module is available")

# Enhanced CSS for Professional Interface
st.markdown("""
<style>
    .main { padding: 0rem 0.5rem; }
    .block-container { padding-top: 1rem; padding-bottom: 0rem; max-width: none; }

    /* Professional Color Palette */
    :root {
        --primary-blue: #667eea;
        --primary-purple: #764ba2;
        --success-green: #00ff88;
        --error-red: #ff6b6b;
        --warning-yellow: #ffd93d;
        --dark-bg: #0f1419;
        --dark-secondary: #1a1f25;
        --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }

    /* Enhanced Cards */
    .analysis-card {
        background: linear-gradient(135deg, #1a1f25 0%, #252d38 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border: 1px solid #333;
        margin-bottom: 1rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }

    .metric-card {
        background: var(--gradient-primary);
        padding: 1.2rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
    }

    .card-header {
        font-size: 1.1rem;
        font-weight: bold;
        color: #667eea;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #667eea;
    }

    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: white;
        line-height: 1;
    }

    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
        margin-top: 0.5rem;
    }

    /* Success/Error Indicators */
    .positive { color: #00ff88 !important; }
    .negative { color: #ff6b6b !important; }
    .neutral { color: #ffd93d !important; }

    /* Professional Headers */
    .platform-header {
        background: var(--gradient-primary);
        padding: 2rem;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 15px 35px rgba(102, 126, 234, 0.4);
    }

    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #667eea;
        margin: 1.5rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #667eea;
    }

    /* Optimization Results */
    .optimization-result {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        margin: 1rem 0;
    }

    /* Risk Indicators */
    .risk-low { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
    .risk-medium { background: linear-gradient(135deg, #ffd93d 0%, #ff8a00 100%); }
    .risk-high { background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%); }

    /* Portfolio Stats */
    .portfolio-stats {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1.5rem 0;
    }

    /* Charts Container */
    .chart-container {
        background: #1a1f25;
        padding: 1.5rem;
        border-radius: 15px;
        border: 1px solid #333;
        margin: 1rem 0;
    }

    /* Interactive Elements */
    .stButton > button {
        background: var(--gradient-primary);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }

    /* Sidebar Styling */
    .css-1d391kg { background-color: #0f1419; }
    .css-1d391kg .css-1vq4p4l { color: white; }
</style>
""", unsafe_allow_html=True)

def create_platform_header():
    """Create professional platform header"""
    st.markdown("""
    <div class="platform-header">
        <h1>💼 Portfolio Analytics Platform</h1>
        <p>Advanced Portfolio Optimization • Risk Management • Performance Analytics</p>
        <p><strong>Institutional-Grade Tools for Professional Investors</strong></p>
    </div>
    """, unsafe_allow_html=True)

def portfolio_input_section():
    """Portfolio input and configuration section"""
    st.markdown('<div class="section-header">🎯 Portfolio Configuration</div>', unsafe_allow_html=True)

    with st.expander("📊 Portfolio Setup", expanded=True):
        col1, col2 = st.columns([2, 1])

        with col1:
            symbols_input = st.text_area(
                "Enter Stock/ETF Symbols (comma-separated)",
                value="AAPL, GOOGL, MSFT, AMZN, TSLA, SPY, QQQ, VTI",
                help="Enter symbols separated by commas (e.g., AAPL, GOOGL, MSFT)"
            )

            symbols = [s.strip().upper() for s in symbols_input.split(',') if s.strip()]

        with col2:
            optimization_objective = st.selectbox(
                "Optimization Objective",
                ["sharpe", "min_volatility", "max_return"],
                format_func=lambda x: {
                    "sharpe": "🎯 Maximum Sharpe Ratio",
                    "min_volatility": "🛡️ Minimum Volatility",
                    "max_return": "📈 Maximum Return"
                }[x]
            )

            rebalancing_frequency = st.selectbox(
                "Rebalancing Frequency",
                ["Monthly", "Quarterly", "Semi-Annual", "Annual"]
            )

    return symbols, optimization_objective, rebalancing_frequency

def display_portfolio_metrics(optimizer, weights_dict):
    """Display portfolio metrics in cards"""
    st.markdown('<div class="section-header">📊 Portfolio Metrics</div>', unsafe_allow_html=True)

    weights = np.array([weights_dict.get(symbol, 0) for symbol in optimizer.symbols])
    metrics = optimizer.calculate_portfolio_metrics(weights)
    risk_analysis = optimizer.risk_analysis(weights.tolist())

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        return_color = "positive" if metrics['return'] > 0 else "negative"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value {return_color}">{metrics['return']:.2%}</div>
            <div class="metric-label">Expected Annual Return</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        vol_color = "neutral" if metrics['volatility'] < 0.2 else "negative"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value {vol_color}">{metrics['volatility']:.2%}</div>
            <div class="metric-label">Annual Volatility</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        sharpe_color = "positive" if metrics['sharpe_ratio'] > 1 else "neutral" if metrics['sharpe_ratio'] > 0.5 else "negative"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value {sharpe_color}">{metrics['sharpe_ratio']:.2f}</div>
            <div class="metric-label">Sharpe Ratio</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        beta_color = "neutral" if 0.8 <= risk_analysis['portfolio_beta'] <= 1.2 else "negative"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value {beta_color}">{risk_analysis['portfolio_beta']:.2f}</div>
            <div class="metric-label">Portfolio Beta</div>
        </div>
        """, unsafe_allow_html=True)

    # Risk Metrics Row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="analysis-card">
            <div class="card-header">📉 Value at Risk</div>
            <p><strong>VaR (95%):</strong> <span class="negative">{risk_analysis['var_95']:.2f}%</span></p>
            <p><strong>VaR (99%):</strong> <span class="negative">{risk_analysis['var_99']:.2f}%</span></p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="analysis-card">
            <div class="card-header">📊 Drawdown Analysis</div>
            <p><strong>Max Drawdown:</strong> <span class="negative">{risk_analysis['max_drawdown']:.2f}%</span></p>
            <p><strong>Downside Dev:</strong> <span class="neutral">{risk_analysis['downside_deviation']:.2f}%</span></p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="analysis-card">
            <div class="card-header">🎯 Risk-Adjusted</div>
            <p><strong>Sortino Ratio:</strong> <span class="positive">{risk_analysis['sortino_ratio']:.2f}</span></p>
            <p><strong>Tracking Error:</strong> <span class="neutral">{risk_analysis['tracking_error']:.2f}%</span></p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="analysis-card">
            <div class="card-header">🔄 Correlation</div>
            <p><strong>Market Correlation:</strong> <span class="neutral">{risk_analysis['portfolio_beta']:.2f}</span></p>
            <p><strong>Diversification:</strong> <span class="positive">Good</span></p>
        </div>
        """, unsafe_allow_html=True)

def display_optimization_results(optimization_result):
    """Display optimization results"""
    st.markdown('<div class="section-header">🎯 Optimization Results</div>', unsafe_allow_html=True)

    if optimization_result.get('success'):
        weights = optimization_result['weights']
        metrics = optimization_result['metrics']

        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown(f"""
            <div class="optimization-result">
                <h3>✅ Optimization Successful</h3>
                <p><strong>Objective:</strong> {optimization_result['objective'].replace('_', ' ').title()}</p>
                <p><strong>Expected Return:</strong> {metrics['return']:.2%}</p>
                <p><strong>Volatility:</strong> {metrics['volatility']:.2%}</p>
                <p><strong>Sharpe Ratio:</strong> {metrics['sharpe_ratio']:.3f}</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            # Allocation pie chart
            fig_pie = go.Figure(data=[
                go.Pie(
                    labels=list(weights.keys()),
                    values=list(weights.values()),
                    hole=.4,
                    marker_colors=px.colors.qualitative.Set3
                )
            ])

            fig_pie.update_layout(
                title="Optimal Portfolio Allocation",
                template="plotly_dark",
                height=300,
                showlegend=True
            )

            st.plotly_chart(fig_pie, use_container_width=True)

        # Detailed allocation table
        st.markdown("#### 📋 Detailed Allocation")
        allocation_df = pd.DataFrame([
            {"Symbol": symbol, "Weight": f"{weight:.2%}", "Weight_Decimal": weight}
            for symbol, weight in weights.items()
        ]).sort_values("Weight_Decimal", ascending=False)

        st.dataframe(allocation_df[["Symbol", "Weight"]], use_container_width=True)

        return weights
    else:
        st.error(f"❌ Optimization failed: {optimization_result.get('error', 'Unknown error')}")
        return None

def display_efficient_frontier(optimizer):
    """Display efficient frontier visualization"""
    st.markdown('<div class="section-header">📈 Efficient Frontier Analysis</div>', unsafe_allow_html=True)

    with st.spinner("Generating efficient frontier..."):
        efficient_frontier = optimizer.generate_efficient_frontier(50)
        monte_carlo = optimizer.monte_carlo_simulation(5000)

        if 'error' not in efficient_frontier:
            fig = go.Figure()

            # Monte Carlo simulations
            fig.add_trace(go.Scatter(
                x=monte_carlo['volatilities'],
                y=monte_carlo['returns'],
                mode='markers',
                name='Random Portfolios',
                marker=dict(
                    size=4,
                    color=monte_carlo['sharpe_ratios'],
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="Sharpe Ratio", x=1.02),
                    opacity=0.6
                ),
                hovertemplate="Return: %{y:.2%}<br>Volatility: %{x:.2%}<br>Sharpe: %{marker.color:.2f}<extra></extra>"
            ))

            # Efficient frontier
            fig.add_trace(go.Scatter(
                x=efficient_frontier['volatilities'],
                y=efficient_frontier['returns'],
                mode='lines+markers',
                name='Efficient Frontier',
                line=dict(color='#ff6b6b', width=4),
                marker=dict(size=8, color='#ff6b6b'),
                hovertemplate="Return: %{y:.2%}<br>Volatility: %{x:.2%}<extra></extra>"
            ))

            # Current portfolio point
            current_metrics = optimizer.calculate_portfolio_metrics(np.array(optimizer.weights))
            fig.add_trace(go.Scatter(
                x=[current_metrics['volatility']],
                y=[current_metrics['return']],
                mode='markers',
                name='Current Portfolio',
                marker=dict(size=15, color='#00ff88', symbol='star'),
                hovertemplate="Current Portfolio<br>Return: %{y:.2%}<br>Volatility: %{x:.2%}<extra></extra>"
            ))

            fig.update_layout(
                title='Portfolio Efficient Frontier',
                xaxis_title='Annual Volatility',
                yaxis_title='Annual Expected Return',
                template='plotly_dark',
                height=500,
                hovermode='closest'
            )

            # Format axes as percentages
            fig.update_xaxis(tickformat='.1%')
            fig.update_yaxis(tickformat='.1%')

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("Could not generate efficient frontier")

def display_performance_attribution(optimizer, weights_dict):
    """Display performance attribution analysis"""
    st.markdown('<div class="section-header">🔍 Performance Attribution</div>', unsafe_allow_html=True)

    weights = [weights_dict.get(symbol, 0) for symbol in optimizer.symbols]
    attribution = optimizer.performance_attribution(weights)

    if 'error' not in attribution:
        # Create attribution chart
        symbols = list(attribution['attribution'].keys())
        contributions = [attribution['attribution'][symbol]['contribution'] for symbol in symbols]
        weights_list = [attribution['attribution'][symbol]['weight'] for symbol in symbols]

        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Contribution to Return', 'Weight Allocation'),
            specs=[[{"type": "bar"}, {"type": "pie"}]]
        )

        # Contribution bar chart
        colors = ['#00ff88' if x > 0 else '#ff6b6b' for x in contributions]
        fig.add_trace(
            go.Bar(x=symbols, y=contributions, marker_color=colors, name="Contribution"),
            row=1, col=1
        )

        # Weight pie chart
        fig.add_trace(
            go.Pie(labels=symbols, values=weights_list, name="Weights"),
            row=1, col=2
        )

        fig.update_layout(
            title="Portfolio Performance Attribution",
            template="plotly_dark",
            height=400,
            showlegend=False
        )

        fig.update_yaxes(title_text="Contribution (%)", tickformat='.2%', row=1, col=1)

        st.plotly_chart(fig, use_container_width=True)

        # Attribution table
        attribution_df = pd.DataFrame([
            {
                "Symbol": symbol,
                "Weight": f"{data['weight']:.2%}",
                "Return": f"{data['return']:.2%}",
                "Contribution": f"{data['contribution']:.2%}",
                "Contribution %": f"{data['contribution_pct']:.1f}%"
            }
            for symbol, data in attribution['attribution'].items()
        ]).sort_values("Contribution", ascending=False)

        st.dataframe(attribution_df, use_container_width=True)

def rebalancing_analysis_section(optimizer, optimal_weights):
    """Rebalancing analysis section"""
    st.markdown('<div class="section-header">🔄 Rebalancing Analysis</div>', unsafe_allow_html=True)

    with st.expander("💰 Current Portfolio Values", expanded=False):
        st.markdown("Enter your current portfolio values for rebalancing analysis:")

        current_values = {}
        cols = st.columns(min(4, len(optimizer.symbols)))

        for i, symbol in enumerate(optimizer.symbols):
            with cols[i % 4]:
                current_values[symbol] = st.number_input(
                    f"{symbol} Value ($)",
                    min_value=0.0,
                    value=10000.0,
                    step=100.0,
                    key=f"current_{symbol}"
                )

        if st.button("📊 Analyze Rebalancing", type="primary"):
            rebalancing = optimizer.rebalancing_analysis(optimal_weights, current_values)

            # Rebalancing summary
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">${rebalancing['total_portfolio_value']:,.0f}</div>
                    <div class="metric-label">Total Portfolio Value</div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">${rebalancing['total_trade_amount']:,.0f}</div>
                    <div class="metric-label">Total Trading Required</div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{rebalancing['rebalancing_cost_pct']:.2f}%</div>
                    <div class="metric-label">Rebalancing Cost %</div>
                </div>
                """, unsafe_allow_html=True)

            # Detailed rebalancing table
            rebalancing_df = pd.DataFrame([
                {
                    "Symbol": symbol,
                    "Current Weight": f"{data['current_weight']:.2%}",
                    "Target Weight": f"{data['target_weight']:.2%}",
                    "Difference": f"{data['weight_difference']:+.2%}",
                    "Dollar Amount": f"${data['dollar_amount']:+,.0f}",
                    "Action": data['action'].title()
                }
                for symbol, data in rebalancing['rebalancing'].items()
            ])

            st.markdown("#### 📋 Rebalancing Actions Required")
            st.dataframe(rebalancing_df, use_container_width=True)

def main():
    """Main application"""
    create_platform_header()

    # Sidebar configuration
    with st.sidebar:
        st.markdown("### ⚙️ Platform Settings")

        data_period = st.selectbox(
            "Historical Data Period",
            ["1y", "2y", "3y", "5y"],
            index=1,
            help="Period for historical data analysis"
        )

        risk_free_rate = st.number_input(
            "Risk-Free Rate (%)",
            min_value=0.0,
            max_value=10.0,
            value=3.0,
            step=0.1,
            help="Annual risk-free rate for Sharpe ratio calculation"
        ) / 100

        st.markdown("---")
        st.markdown("### 📚 Quick Guide")
        st.markdown("""
        1. **Configure Portfolio**: Enter stock/ETF symbols
        2. **Select Objective**: Choose optimization goal
        3. **Run Optimization**: Click optimize button
        4. **Analyze Results**: Review metrics and charts
        5. **Rebalance**: Use rebalancing analysis
        """)

    # Main content
    symbols, objective, rebalancing_freq = portfolio_input_section()

    if len(symbols) >= 2:
        if st.button("🚀 Optimize Portfolio", type="primary"):
            with st.spinner("Optimizing portfolio..."):
                optimizer = PortfolioOptimizer(symbols)

                # Run optimization
                optimization_result = optimizer.optimize_portfolio(objective)

                if optimization_result.get('success'):
                    # Store results in session state
                    st.session_state.optimizer = optimizer
                    st.session_state.optimization_result = optimization_result
                    st.session_state.optimal_weights = optimization_result['weights']

                    st.success("✅ Portfolio optimization completed successfully!")
                else:
                    st.error(f"❌ Optimization failed: {optimization_result.get('error')}")

        # Display results if available
        if hasattr(st.session_state, 'optimization_result') and st.session_state.optimization_result.get('success'):
            optimizer = st.session_state.optimizer
            optimization_result = st.session_state.optimization_result
            optimal_weights = st.session_state.optimal_weights

            # Create tabs for different analyses
            tab1, tab2, tab3, tab4 = st.tabs([
                "📊 Portfolio Metrics",
                "📈 Efficient Frontier",
                "🔍 Attribution Analysis",
                "🔄 Rebalancing"
            ])

            with tab1:
                display_optimization_results(optimization_result)
                display_portfolio_metrics(optimizer, optimal_weights)

            with tab2:
                display_efficient_frontier(optimizer)

            with tab3:
                display_performance_attribution(optimizer, optimal_weights)

            with tab4:
                rebalancing_analysis_section(optimizer, optimal_weights)

    else:
        st.warning("⚠️ Please enter at least 2 symbols to create a portfolio")

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        <p>💼 <strong>Portfolio Analytics Platform</strong> | Professional Investment Tools</p>
        <p>Modern Portfolio Theory • Risk Management • Performance Analytics</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()