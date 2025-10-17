"""UI Components for AI Stock Predictions"""
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List
from utils.ai_predictions import StockPredictionEngine


def create_prediction_chart(
    symbol: str,
    predictions: Dict[str, Dict],
    historical_data: pd.DataFrame
) -> go.Figure:
    """Create interactive chart comparing all prediction models

    Args:
        symbol: Stock symbol
        predictions: Dictionary of prediction results from all models
        historical_data: Historical price data

    Returns:
        Plotly figure
    """
    fig = go.Figure()

    # Add historical data
    fig.add_trace(go.Scatter(
        x=historical_data.index,
        y=historical_data['Close'],
        mode='lines',
        name='Historical Price',
        line=dict(color='#2E86AB', width=2),
        hovertemplate='<b>Historical</b><br>Date: %{x}<br>Price: $%{y:.2f}<extra></extra>'
    ))

    # Color palette for models
    colors = {
        'Linear Regression': '#06D6A0',
        'Random Forest': '#EF476F',
        'Gradient Boosting': '#FFD166',
        'ARIMA': '#118AB2',
        'Prophet': '#F78C6B',
        'Monte Carlo': '#9B59B6'
    }

    # Add predictions for each model
    for model_name, result in predictions.items():
        color = colors.get(model_name, '#95A5A6')

        # Main prediction line
        fig.add_trace(go.Scatter(
            x=result['dates'],
            y=result['predictions'],
            mode='lines+markers',
            name=model_name,
            line=dict(color=color, width=2, dash='dot'),
            marker=dict(size=6),
            hovertemplate=f'<b>{model_name}</b><br>Date: %{{x}}<br>Price: $%{{y:.2f}}<extra></extra>'
        ))

        # Add confidence intervals for Prophet
        if model_name == 'Prophet' and 'upper_bound' in result:
            fig.add_trace(go.Scatter(
                x=result['dates'],
                y=result['upper_bound'],
                mode='lines',
                name=f'{model_name} Upper',
                line=dict(width=0),
                showlegend=False,
                hoverinfo='skip'
            ))
            fig.add_trace(go.Scatter(
                x=result['dates'],
                y=result['lower_bound'],
                mode='lines',
                name=f'{model_name} Lower',
                line=dict(width=0),
                fillcolor=f'rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.2)',
                fill='tonexty',
                showlegend=False,
                hoverinfo='skip'
            ))

        # Add Monte Carlo percentiles
        if model_name.startswith('Monte Carlo') and 'percentile_95' in result:
            fig.add_trace(go.Scatter(
                x=result['dates'],
                y=result['percentile_95'],
                mode='lines',
                name='MC 95th %ile',
                line=dict(width=1, dash='dash', color='rgba(155, 89, 182, 0.3)'),
                showlegend=False,
                hoverinfo='skip'
            ))
            fig.add_trace(go.Scatter(
                x=result['dates'],
                y=result['percentile_5'],
                mode='lines',
                name='MC 5th %ile',
                line=dict(width=1, dash='dash', color='rgba(155, 89, 182, 0.3)'),
                fillcolor='rgba(155, 89, 182, 0.1)',
                fill='tonexty',
                showlegend=False,
                hoverinfo='skip'
            ))

    # Update layout
    fig.update_layout(
        title=f'{symbol} Price Predictions - Model Comparison',
        xaxis_title='Date',
        yaxis_title='Price ($)',
        hovermode='x unified',
        height=600,
        template='plotly_white',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    return fig


def display_model_metrics(predictions: Dict[str, Dict]):
    """Display metrics comparison table for all models

    Args:
        predictions: Dictionary of prediction results
    """
    st.markdown("### 📊 Model Performance Metrics")

    metrics_data = []

    for model_name, result in predictions.items():
        if 'metrics' in result:
            metrics = result['metrics']
            row = {
                'Model': model_name,
                'RMSE': f"{metrics.get('RMSE', 'N/A'):.2f}" if isinstance(metrics.get('RMSE'), (int, float)) else 'N/A',
                'MAE': f"{metrics.get('MAE', 'N/A'):.2f}" if isinstance(metrics.get('MAE'), (int, float)) else 'N/A',
                'R²': f"{metrics.get('R²', 'N/A'):.4f}" if isinstance(metrics.get('R²'), (int, float)) else 'N/A',
            }

            # Add model-specific metrics
            if 'AIC' in metrics:
                row['AIC'] = f"{metrics['AIC']:.2f}"
            if 'BIC' in metrics:
                row['BIC'] = f"{metrics['BIC']:.2f}"

            metrics_data.append(row)

    if metrics_data:
        df_metrics = pd.DataFrame(metrics_data)
        st.dataframe(df_metrics, use_container_width=True, hide_index=True)

        # Explanation
        with st.expander("ℹ️ Understanding Metrics"):
            st.markdown("""
            **RMSE (Root Mean Square Error)**: Lower is better. Measures average prediction error.

            **MAE (Mean Absolute Error)**: Lower is better. Average absolute difference between predicted and actual values.

            **R² (R-squared)**: Higher is better (0 to 1). Indicates how well the model fits the data.

            **AIC/BIC**: Lower is better. Model quality indicators (ARIMA models only).
            """)


def display_prediction_summary(predictions: Dict[str, Dict]):
    """Display prediction summary cards

    Args:
        predictions: Dictionary of prediction results
    """
    st.markdown("### 🎯 Prediction Summary (30 Days)")

    if not predictions:
        st.warning("No predictions available")
        return

    # Calculate average prediction and consensus
    all_final_predictions = [
        result['predictions'][-1]
        for result in predictions.values()
        if 'predictions' in result
    ]

    if not all_final_predictions:
        return

    avg_prediction = np.mean(all_final_predictions)
    min_prediction = np.min(all_final_predictions)
    max_prediction = np.max(all_final_predictions)
    std_prediction = np.std(all_final_predictions)

    # Display metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Average Prediction",
            f"${avg_prediction:.2f}",
            help="Mean of all model predictions for 30 days out"
        )

    with col2:
        st.metric(
            "Prediction Range",
            f"${min_prediction:.2f} - ${max_prediction:.2f}",
            help="Range across all models"
        )

    with col3:
        st.metric(
            "Std Deviation",
            f"${std_prediction:.2f}",
            help="Model disagreement (lower = more consensus)"
        )

    with col4:
        # Model consensus strength
        consensus_strength = max(0, 100 - (std_prediction / avg_prediction * 100))
        st.metric(
            "Consensus Strength",
            f"{consensus_strength:.0f}%",
            help="How much models agree (higher = stronger consensus)"
        )

    # Individual model predictions
    st.markdown("#### Individual Model Predictions (30-Day Target)")

    cols = st.columns(min(len(predictions), 3))

    for idx, (model_name, result) in enumerate(predictions.items()):
        if 'predictions' in result:
            final_pred = result['predictions'][-1]
            with cols[idx % 3]:
                st.metric(
                    model_name,
                    f"${final_pred:.2f}"
                )


def display_feature_importance(predictions: Dict[str, Dict]):
    """Display feature importance for tree-based models

    Args:
        predictions: Dictionary of prediction results
    """
    for model_name, result in predictions.items():
        if 'feature_importance' in result:
            st.markdown(f"### 📈 {model_name} - Feature Importance")

            importance = result['feature_importance']
            df_importance = pd.DataFrame({
                'Feature': list(importance.keys()),
                'Importance': list(importance.values())
            }).sort_values('Importance', ascending=False)

            fig = go.Figure(go.Bar(
                x=df_importance['Importance'],
                y=df_importance['Feature'],
                orientation='h',
                marker=dict(color=df_importance['Importance'], colorscale='Viridis')
            ))

            fig.update_layout(
                title='Technical Indicator Importance',
                xaxis_title='Importance Score',
                yaxis_title='Feature',
                height=300,
                template='plotly_white'
            )

            st.plotly_chart(fig, use_container_width=True)


def display_ai_predictions(symbol: str):
    """Main UI function for AI predictions

    Args:
        symbol: Stock symbol
    """
    st.markdown("## 🤖 AI Price Predictions")

    st.markdown("""
    Advanced machine learning models analyze historical data and technical indicators to predict future prices.
    Multiple algorithms provide different perspectives for comprehensive analysis.
    """)

    # User controls
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        prediction_days = st.slider(
            "Prediction Horizon (Days)",
            min_value=7,
            max_value=90,
            value=30,
            help="Number of days to predict into the future"
        )

    with col2:
        data_period = st.selectbox(
            "Historical Data Period",
            options=['1y', '2y', '5y', 'max'],
            index=1,
            help="How much historical data to use for training"
        )

    with col3:
        run_prediction = st.button("🚀 Run Predictions", type="primary", use_container_width=True)

    if run_prediction or f'predictions_{symbol}' in st.session_state:
        with st.spinner("Running AI models... This may take a minute."):
            # Initialize prediction engine
            engine = StockPredictionEngine(symbol, period=data_period)

            # Get all predictions
            predictions = engine.get_all_predictions(days=prediction_days)

            if not predictions:
                st.error("❌ Unable to generate predictions. Please check the stock symbol and try again.")
                return

            # Store in session state
            st.session_state[f'predictions_{symbol}'] = predictions
            st.session_state[f'historical_data_{symbol}'] = engine.data

        predictions = st.session_state[f'predictions_{symbol}']
        historical_data = st.session_state[f'historical_data_{symbol}']

        # Display results
        st.success(f"✅ Generated predictions using {len(predictions)} models")

        # Prediction summary
        display_prediction_summary(predictions)

        st.markdown("---")

        # Main prediction chart
        fig = create_prediction_chart(symbol, predictions, historical_data)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # Model metrics comparison
        display_model_metrics(predictions)

        st.markdown("---")

        # Feature importance for applicable models
        display_feature_importance(predictions)

        # Download predictions
        st.markdown("### 💾 Export Predictions")

        export_data = []
        for model_name, result in predictions.items():
            if 'dates' in result and 'predictions' in result:
                for date, price in zip(result['dates'], result['predictions']):
                    export_data.append({
                        'Date': date,
                        'Model': model_name,
                        'Predicted Price': price
                    })

        if export_data:
            df_export = pd.DataFrame(export_data)
            csv = df_export.to_csv(index=False)

            st.download_button(
                label="📥 Download Predictions (CSV)",
                data=csv,
                file_name=f"{symbol}_predictions_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

        # Model information
        with st.expander("📚 About the Models"):
            st.markdown("""
            **Linear Regression**: Simple trend-based prediction using historical price movement.

            **Random Forest**: Ensemble method using multiple decision trees with technical indicators.

            **Gradient Boosting**: Advanced ensemble method that builds trees sequentially to correct errors.

            **ARIMA**: Time series model that captures autocorrelation and seasonality patterns.

            **Prophet**: Facebook's forecasting tool designed for daily observations with seasonal patterns.

            **Monte Carlo**: Probabilistic simulation generating thousands of possible price paths.

            **Note**: These are statistical models and should not be used as the sole basis for investment decisions.
            Always combine with fundamental analysis and risk management.
            """)
