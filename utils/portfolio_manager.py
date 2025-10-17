"""
Portfolio Management System for Global Liquidity Dashboard
Real-time portfolio tracking, P&L calculations, and performance analytics
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import yfinance as yf
from utils.database import get_db

class PortfolioManager:
    """Manages user portfolios and performance tracking"""

    def __init__(self, user_id: int):
        """Initialize portfolio manager for user"""
        self.user_id = user_id
        self.db = get_db()

    def create_portfolio(self, name: str, description: str = "") -> int:
        """Create a new portfolio"""
        return self.db.create_portfolio(self.user_id, name, description)

    def add_position(self, portfolio_id: int, symbol: str, quantity: float,
                    purchase_price: float, purchase_date: str, notes: str = ""):
        """Add a position to portfolio"""
        self.db.add_holding(
            portfolio_id, symbol, quantity, purchase_price, purchase_date, notes
        )

    def get_portfolio_summary(self, portfolio_id: int) -> Dict:
        """Get comprehensive portfolio summary with current values"""
        holdings = self.db.get_portfolio_holdings(portfolio_id)

        if not holdings:
            return {
                'total_value': 0,
                'total_cost': 0,
                'total_pnl': 0,
                'total_pnl_pct': 0,
                'holdings': []
            }

        # Fetch current prices
        symbols = [h['symbol'] for h in holdings]
        current_prices = self._get_current_prices(symbols)

        enriched_holdings = []
        total_value = 0
        total_cost = 0

        for holding in holdings:
            symbol = holding['symbol']
            quantity = holding['quantity']
            purchase_price = holding['purchase_price']
            current_price = current_prices.get(symbol, purchase_price)

            cost_basis = quantity * purchase_price
            current_value = quantity * current_price
            pnl = current_value - cost_basis
            pnl_pct = (pnl / cost_basis * 100) if cost_basis > 0 else 0

            enriched_holdings.append({
                'id': holding['id'],
                'symbol': symbol,
                'quantity': quantity,
                'purchase_price': purchase_price,
                'current_price': current_price,
                'cost_basis': cost_basis,
                'current_value': current_value,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'purchase_date': holding['purchase_date'],
                'notes': holding['notes']
            })

            total_value += current_value
            total_cost += cost_basis

        total_pnl = total_value - total_cost
        total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0

        return {
            'total_value': total_value,
            'total_cost': total_cost,
            'total_pnl': total_pnl,
            'total_pnl_pct': total_pnl_pct,
            'holdings': enriched_holdings,
            'last_updated': datetime.now().isoformat()
        }

    def get_portfolio_allocation(self, portfolio_id: int) -> Dict:
        """Get portfolio allocation breakdown"""
        summary = self.get_portfolio_summary(portfolio_id)
        holdings = summary['holdings']

        if not holdings:
            return {'symbols': [], 'values': [], 'percentages': []}

        symbols = []
        values = []
        percentages = []
        total_value = summary['total_value']

        for holding in holdings:
            symbols.append(holding['symbol'])
            values.append(holding['current_value'])
            pct = (holding['current_value'] / total_value * 100) if total_value > 0 else 0
            percentages.append(pct)

        return {
            'symbols': symbols,
            'values': values,
            'percentages': percentages
        }

    def get_portfolio_performance(self, portfolio_id: int, period: str = '1mo') -> Dict:
        """Calculate portfolio performance over time"""
        holdings = self.db.get_portfolio_holdings(portfolio_id)

        if not holdings:
            return {'dates': [], 'values': [], 'returns': []}

        symbols = [h['symbol'] for h in holdings]
        quantities = {h['symbol']: h['quantity'] for h in holdings}

        # Fetch historical data
        historical_data = self._get_historical_data(symbols, period)

        if historical_data.empty:
            return {'dates': [], 'values': [], 'returns': []}

        # Calculate portfolio value over time
        dates = []
        values = []

        for date in historical_data.index:
            portfolio_value = 0
            for symbol in symbols:
                if symbol in historical_data.columns:
                    price = historical_data.loc[date, symbol]
                    if not pd.isna(price):
                        portfolio_value += price * quantities[symbol]

            dates.append(date.strftime('%Y-%m-%d'))
            values.append(portfolio_value)

        # Calculate returns
        returns = []
        for i in range(len(values)):
            if i == 0:
                returns.append(0)
            else:
                ret = ((values[i] - values[i-1]) / values[i-1] * 100) if values[i-1] > 0 else 0
                returns.append(ret)

        return {
            'dates': dates,
            'values': values,
            'returns': returns
        }

    def get_portfolio_metrics(self, portfolio_id: int) -> Dict:
        """Calculate advanced portfolio metrics"""
        performance = self.get_portfolio_performance(portfolio_id, period='1y')
        summary = self.get_portfolio_summary(portfolio_id)

        if not performance['values']:
            return {}

        values = performance['values']
        returns = performance['returns']

        # Calculate metrics
        total_return = ((values[-1] - values[0]) / values[0] * 100) if values[0] > 0 else 0
        avg_daily_return = np.mean(returns) if returns else 0
        volatility = np.std(returns) if len(returns) > 1 else 0
        sharpe_ratio = (avg_daily_return / volatility * np.sqrt(252)) if volatility > 0 else 0

        max_value = max(values)
        min_value = min(values)
        max_drawdown = ((min_value - max_value) / max_value * 100) if max_value > 0 else 0

        return {
            'total_return': total_return,
            'avg_daily_return': avg_daily_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'current_value': summary['total_value'],
            'total_pnl': summary['total_pnl'],
            'total_pnl_pct': summary['total_pnl_pct']
        }

    def get_risk_analysis(self, portfolio_id: int) -> Dict:
        """Analyze portfolio risk"""
        holdings = self.db.get_portfolio_holdings(portfolio_id)

        if not holdings:
            return {}

        symbols = [h['symbol'] for h in holdings]

        # Get beta values (using market as proxy)
        betas = {}
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                betas[symbol] = info.get('beta', 1.0)
            except:
                betas[symbol] = 1.0

        # Calculate weighted portfolio beta
        summary = self.get_portfolio_summary(portfolio_id)
        total_value = summary['total_value']

        weighted_beta = 0
        for holding in summary['holdings']:
            weight = holding['current_value'] / total_value if total_value > 0 else 0
            weighted_beta += betas.get(holding['symbol'], 1.0) * weight

        # Concentration risk
        allocation = self.get_portfolio_allocation(portfolio_id)
        max_concentration = max(allocation['percentages']) if allocation['percentages'] else 0

        risk_level = 'LOW'
        if weighted_beta > 1.5 or max_concentration > 50:
            risk_level = 'HIGH'
        elif weighted_beta > 1.2 or max_concentration > 30:
            risk_level = 'MEDIUM'

        return {
            'portfolio_beta': weighted_beta,
            'max_concentration': max_concentration,
            'risk_level': risk_level,
            'diversification_score': 100 - max_concentration,
            'position_count': len(holdings)
        }

    def _get_current_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Get current prices for symbols"""
        prices = {}
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='5d')
                if not hist.empty:
                    prices[symbol] = hist['Close'].iloc[-1]
                else:
                    # Fallback to info if history fails
                    info = ticker.info
                    prices[symbol] = info.get('currentPrice', info.get('regularMarketPrice', 0))
            except Exception as e:
                # Default to 0 if all else fails
                prices[symbol] = 0
        return prices

    def _get_historical_data(self, symbols: List[str], period: str) -> pd.DataFrame:
        """Get historical data for symbols"""
        try:
            data = yf.download(symbols, period=period, progress=False)
            if 'Close' in data.columns:
                if len(symbols) == 1:
                    return pd.DataFrame({symbols[0]: data['Close']})
                return data['Close']
            return pd.DataFrame()
        except:
            return pd.DataFrame()

    def compare_to_benchmark(self, portfolio_id: int, benchmark: str = '^GSPC') -> Dict:
        """Compare portfolio performance to benchmark"""
        portfolio_perf = self.get_portfolio_performance(portfolio_id, period='1y')

        if not portfolio_perf['values']:
            return {}

        # Get benchmark data
        try:
            benchmark_data = yf.download(benchmark, period='1y', progress=False)
            if benchmark_data.empty:
                return {}

            benchmark_prices = benchmark_data['Close'].values
            benchmark_returns = []

            for i in range(len(benchmark_prices)):
                if i == 0:
                    benchmark_returns.append(0)
                else:
                    ret = ((benchmark_prices[i] - benchmark_prices[i-1]) / benchmark_prices[i-1] * 100)
                    benchmark_returns.append(ret)

            portfolio_total_return = ((portfolio_perf['values'][-1] - portfolio_perf['values'][0]) /
                                     portfolio_perf['values'][0] * 100)
            benchmark_total_return = ((benchmark_prices[-1] - benchmark_prices[0]) /
                                     benchmark_prices[0] * 100)

            outperformance = portfolio_total_return - benchmark_total_return

            return {
                'portfolio_return': portfolio_total_return,
                'benchmark_return': benchmark_total_return,
                'outperformance': outperformance,
                'benchmark_symbol': benchmark,
                'dates': portfolio_perf['dates'],
                'portfolio_values': portfolio_perf['values'],
                'benchmark_values': benchmark_prices.tolist()
            }
        except:
            return {}
