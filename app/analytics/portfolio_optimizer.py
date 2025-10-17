import numpy as np
import pandas as pd
import yfinance as yf
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import warnings
from scipy.optimize import minimize
from scipy.stats import norm
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

warnings.filterwarnings('ignore')

class PortfolioOptimizer:
    def __init__(self, symbols: List[str], weights: Optional[List[float]] = None):
        self.symbols = symbols
        self.weights = weights if weights else [1.0/len(symbols)] * len(symbols)
        self.returns_data = None
        self.price_data = None
        self.cov_matrix = None
        self.expected_returns = None

    def fetch_data(self, period: str = "2y") -> bool:
        """Fetch historical data for all symbols"""
        try:
            tickers = yf.Tickers(' '.join(self.symbols))
            data = tickers.history(period=period)['Close']

            if data.empty:
                return False

            self.price_data = data.dropna()
            self.returns_data = self.price_data.pct_change().dropna()

            # Calculate expected returns (annualized)
            self.expected_returns = self.returns_data.mean() * 252

            # Calculate covariance matrix (annualized)
            self.cov_matrix = self.returns_data.cov() * 252

            return True
        except Exception as e:
            print(f"Error fetching data: {e}")
            return False

    def calculate_portfolio_metrics(self, weights: np.array) -> Dict[str, float]:
        """Calculate portfolio metrics for given weights"""
        if self.expected_returns is None or self.cov_matrix is None:
            return {}

        # Ensure weights sum to 1
        weights = weights / np.sum(weights)

        # Portfolio return
        portfolio_return = np.sum(weights * self.expected_returns)

        # Portfolio volatility
        portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(self.cov_matrix, weights)))

        # Sharpe ratio (assuming 3% risk-free rate)
        risk_free_rate = 0.03
        sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_volatility if portfolio_volatility > 0 else 0

        return {
            'return': portfolio_return,
            'volatility': portfolio_volatility,
            'sharpe_ratio': sharpe_ratio
        }

    def optimize_portfolio(self, objective: str = 'sharpe') -> Dict[str, Any]:
        """Optimize portfolio based on objective"""
        if not self.fetch_data():
            return {"error": "Failed to fetch data"}

        num_assets = len(self.symbols)

        # Constraints: weights sum to 1
        constraints = {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}

        # Bounds: weights between 0 and 1 (no short selling)
        bounds = tuple((0, 1) for _ in range(num_assets))

        # Initial guess: equal weights
        initial_guess = np.array([1.0/num_assets] * num_assets)

        if objective == 'sharpe':
            # Maximize Sharpe ratio (minimize negative Sharpe)
            def objective_function(weights):
                metrics = self.calculate_portfolio_metrics(weights)
                return -metrics['sharpe_ratio']

        elif objective == 'min_volatility':
            # Minimize volatility
            def objective_function(weights):
                metrics = self.calculate_portfolio_metrics(weights)
                return metrics['volatility']

        elif objective == 'max_return':
            # Maximize return (minimize negative return)
            def objective_function(weights):
                metrics = self.calculate_portfolio_metrics(weights)
                return -metrics['return']

        # Optimization
        try:
            result = minimize(objective_function, initial_guess,
                            method='SLSQP', bounds=bounds, constraints=constraints)

            if result.success:
                optimal_weights = result.x
                metrics = self.calculate_portfolio_metrics(optimal_weights)

                return {
                    'weights': dict(zip(self.symbols, optimal_weights)),
                    'metrics': metrics,
                    'objective': objective,
                    'success': True
                }
            else:
                return {"error": "Optimization failed", "success": False}

        except Exception as e:
            return {"error": f"Optimization error: {str(e)}", "success": False}

    def generate_efficient_frontier(self, num_portfolios: int = 100) -> Dict[str, List]:
        """Generate efficient frontier"""
        if not self.fetch_data():
            return {"error": "Failed to fetch data"}

        num_assets = len(self.symbols)
        results = np.zeros((3, num_portfolios))

        # Define target returns
        min_ret = self.expected_returns.min()
        max_ret = self.expected_returns.max()
        target_returns = np.linspace(min_ret, max_ret, num_portfolios)

        constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
        bounds = tuple((0, 1) for _ in range(num_assets))

        for i, target in enumerate(target_returns):
            # Add return constraint
            return_constraint = {'type': 'eq', 'fun': lambda x, target=target:
                               np.sum(x * self.expected_returns) - target}

            current_constraints = constraints + [return_constraint]

            # Minimize volatility for target return
            def objective(weights):
                return np.sqrt(np.dot(weights.T, np.dot(self.cov_matrix, weights)))

            initial_guess = np.array([1.0/num_assets] * num_assets)

            try:
                result = minimize(objective, initial_guess, method='SLSQP',
                                bounds=bounds, constraints=current_constraints)

                if result.success:
                    weights = result.x
                    metrics = self.calculate_portfolio_metrics(weights)
                    results[0, i] = metrics['return']
                    results[1, i] = metrics['volatility']
                    results[2, i] = metrics['sharpe_ratio']
                else:
                    results[:, i] = np.nan
            except:
                results[:, i] = np.nan

        # Remove NaN values
        valid_mask = ~np.isnan(results[0])

        return {
            'returns': results[0][valid_mask].tolist(),
            'volatilities': results[1][valid_mask].tolist(),
            'sharpe_ratios': results[2][valid_mask].tolist()
        }

    def monte_carlo_simulation(self, num_simulations: int = 10000) -> Dict[str, List]:
        """Run Monte Carlo simulation for random portfolios"""
        if not self.fetch_data():
            return {"error": "Failed to fetch data"}

        num_assets = len(self.symbols)
        results = np.zeros((3, num_simulations))

        for i in range(num_simulations):
            # Generate random weights
            weights = np.random.random(num_assets)
            weights /= np.sum(weights)

            metrics = self.calculate_portfolio_metrics(weights)
            results[0, i] = metrics['return']
            results[1, i] = metrics['volatility']
            results[2, i] = metrics['sharpe_ratio']

        return {
            'returns': results[0].tolist(),
            'volatilities': results[1].tolist(),
            'sharpe_ratios': results[2].tolist()
        }

    def risk_analysis(self, weights: Optional[List[float]] = None) -> Dict[str, Any]:
        """Perform comprehensive risk analysis"""
        if not self.fetch_data():
            return {"error": "Failed to fetch data"}

        weights = weights if weights else self.weights
        weights = np.array(weights)

        # Portfolio returns
        portfolio_returns = (self.returns_data * weights).sum(axis=1)

        # VaR calculation (95% and 99% confidence)
        var_95 = np.percentile(portfolio_returns, 5)
        var_99 = np.percentile(portfolio_returns, 1)

        # CVaR (Conditional VaR)
        cvar_95 = portfolio_returns[portfolio_returns <= var_95].mean()
        cvar_99 = portfolio_returns[portfolio_returns <= var_99].mean()

        # Maximum Drawdown
        portfolio_cumulative = (1 + portfolio_returns).cumprod()
        rolling_max = portfolio_cumulative.expanding().max()
        drawdown = (portfolio_cumulative - rolling_max) / rolling_max
        max_drawdown = drawdown.min()

        # Downside deviation
        downside_returns = portfolio_returns[portfolio_returns < 0]
        downside_deviation = downside_returns.std() * np.sqrt(252)

        # Sortino ratio
        metrics = self.calculate_portfolio_metrics(weights)
        sortino_ratio = (metrics['return'] - 0.03) / downside_deviation if downside_deviation > 0 else 0

        return {
            'var_95': var_95 * 100,  # Convert to percentage
            'var_99': var_99 * 100,
            'cvar_95': cvar_95 * 100,
            'cvar_99': cvar_99 * 100,
            'max_drawdown': max_drawdown * 100,
            'downside_deviation': downside_deviation * 100,
            'sortino_ratio': sortino_ratio,
            'portfolio_beta': self.calculate_portfolio_beta(weights),
            'tracking_error': self.calculate_tracking_error(weights)
        }

    def calculate_portfolio_beta(self, weights: np.array) -> float:
        """Calculate portfolio beta vs market (SPY)"""
        try:
            spy = yf.download('SPY', start=self.returns_data.index[0],
                            end=self.returns_data.index[-1])['Close']
            spy_returns = spy.pct_change().dropna()

            # Align dates
            portfolio_returns = (self.returns_data * weights).sum(axis=1)
            aligned_portfolio = portfolio_returns.reindex(spy_returns.index).dropna()
            aligned_spy = spy_returns.reindex(aligned_portfolio.index).dropna()

            if len(aligned_portfolio) > 1 and len(aligned_spy) > 1:
                covariance = np.cov(aligned_portfolio, aligned_spy)[0][1]
                market_variance = np.var(aligned_spy)
                beta = covariance / market_variance if market_variance > 0 else 0
                return beta
            else:
                return 0
        except:
            return 0

    def calculate_tracking_error(self, weights: np.array, benchmark: str = 'SPY') -> float:
        """Calculate tracking error vs benchmark"""
        try:
            benchmark_data = yf.download(benchmark, start=self.returns_data.index[0],
                                       end=self.returns_data.index[-1])['Close']
            benchmark_returns = benchmark_data.pct_change().dropna()

            portfolio_returns = (self.returns_data * weights).sum(axis=1)

            # Align dates
            aligned_portfolio = portfolio_returns.reindex(benchmark_returns.index).dropna()
            aligned_benchmark = benchmark_returns.reindex(aligned_portfolio.index).dropna()

            if len(aligned_portfolio) > 1:
                tracking_diff = aligned_portfolio - aligned_benchmark
                tracking_error = tracking_diff.std() * np.sqrt(252) * 100
                return tracking_error
            else:
                return 0
        except:
            return 0

    def performance_attribution(self, weights: Optional[List[float]] = None) -> Dict[str, Any]:
        """Perform performance attribution analysis"""
        if not self.fetch_data():
            return {"error": "Failed to fetch data"}

        weights = weights if weights else self.weights
        weights = np.array(weights)

        # Calculate individual asset contributions
        individual_returns = self.expected_returns * weights

        # Calculate total portfolio return
        total_return = np.sum(individual_returns)

        # Attribution breakdown
        attribution = {}
        for i, symbol in enumerate(self.symbols):
            attribution[symbol] = {
                'weight': weights[i],
                'return': self.expected_returns.iloc[i],
                'contribution': individual_returns.iloc[i],
                'contribution_pct': (individual_returns.iloc[i] / total_return * 100) if total_return != 0 else 0
            }

        return {
            'total_return': total_return,
            'attribution': attribution,
            'weights': dict(zip(self.symbols, weights))
        }

    def rebalancing_analysis(self, target_weights: Dict[str, float],
                           current_values: Dict[str, float]) -> Dict[str, Any]:
        """Analyze rebalancing requirements"""
        total_value = sum(current_values.values())
        current_weights = {symbol: value/total_value for symbol, value in current_values.items()}

        rebalancing = {}
        total_trades = 0

        for symbol in self.symbols:
            current_weight = current_weights.get(symbol, 0)
            target_weight = target_weights.get(symbol, 0)

            weight_diff = target_weight - current_weight
            dollar_amount = weight_diff * total_value

            rebalancing[symbol] = {
                'current_weight': current_weight,
                'target_weight': target_weight,
                'weight_difference': weight_diff,
                'dollar_amount': dollar_amount,
                'action': 'buy' if dollar_amount > 0 else 'sell' if dollar_amount < 0 else 'hold'
            }

            total_trades += abs(dollar_amount)

        return {
            'rebalancing': rebalancing,
            'total_trade_amount': total_trades,
            'total_portfolio_value': total_value,
            'rebalancing_cost_pct': (total_trades / total_value) * 100 if total_value > 0 else 0
        }

    def create_portfolio_charts(self) -> Dict[str, go.Figure]:
        """Create comprehensive portfolio visualization charts"""
        charts = {}

        # 1. Efficient Frontier Chart
        efficient_frontier = self.generate_efficient_frontier()
        monte_carlo = self.monte_carlo_simulation()

        fig_ef = go.Figure()

        # Monte Carlo points
        fig_ef.add_trace(go.Scatter(
            x=monte_carlo['volatilities'],
            y=monte_carlo['returns'],
            mode='markers',
            name='Monte Carlo Simulations',
            marker=dict(
                size=4,
                color=monte_carlo['sharpe_ratios'],
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Sharpe Ratio"),
                opacity=0.6
            )
        ))

        # Efficient Frontier
        fig_ef.add_trace(go.Scatter(
            x=efficient_frontier['volatilities'],
            y=efficient_frontier['returns'],
            mode='lines+markers',
            name='Efficient Frontier',
            line=dict(color='red', width=3),
            marker=dict(size=6, color='red')
        ))

        fig_ef.update_layout(
            title='Portfolio Efficient Frontier',
            xaxis_title='Volatility (Annual %)',
            yaxis_title='Expected Return (Annual %)',
            template='plotly_dark',
            height=500
        )

        charts['efficient_frontier'] = fig_ef

        # 2. Risk Decomposition Chart
        risk_analysis = self.risk_analysis()

        risk_metrics = ['VaR 95%', 'VaR 99%', 'CVaR 95%', 'CVaR 99%', 'Max Drawdown']
        risk_values = [
            abs(risk_analysis['var_95']),
            abs(risk_analysis['var_99']),
            abs(risk_analysis['cvar_95']),
            abs(risk_analysis['cvar_99']),
            abs(risk_analysis['max_drawdown'])
        ]

        fig_risk = go.Figure(data=[
            go.Bar(x=risk_metrics, y=risk_values,
                  marker_color=['#ff6b6b', '#ff8787', '#ffa8a8', '#ffc9c9', '#ffe0e0'])
        ])

        fig_risk.update_layout(
            title='Portfolio Risk Metrics',
            yaxis_title='Risk (%)',
            template='plotly_dark',
            height=400
        )

        charts['risk_decomposition'] = fig_risk

        # 3. Asset Allocation Pie Chart
        fig_allocation = go.Figure(data=[
            go.Pie(labels=self.symbols, values=self.weights, hole=.3)
        ])

        fig_allocation.update_layout(
            title='Portfolio Asset Allocation',
            template='plotly_dark',
            height=400
        )

        charts['asset_allocation'] = fig_allocation

        return charts

# Example usage and testing
if __name__ == "__main__":
    # Example portfolio
    symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA']

    optimizer = PortfolioOptimizer(symbols)

    # Test optimization
    print("=== PORTFOLIO OPTIMIZATION RESULTS ===")

    # Sharpe ratio optimization
    sharpe_result = optimizer.optimize_portfolio('sharpe')
    print(f"Sharpe Optimization: {sharpe_result}")

    # Min volatility optimization
    min_vol_result = optimizer.optimize_portfolio('min_volatility')
    print(f"Min Volatility Optimization: {min_vol_result}")

    # Risk analysis
    risk_analysis = optimizer.risk_analysis()
    print(f"Risk Analysis: {risk_analysis}")

    # Performance attribution
    attribution = optimizer.performance_attribution()
    print(f"Performance Attribution: {attribution}")