import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class ComprehensiveFundAnalyzer:
    def __init__(self, fund_symbol: str):
        self.fund_symbol = fund_symbol.upper()
        self.fund_data = None
        self.fund_info = None
        self.holdings_data = None
        self.performance_data = None

    def fetch_fund_data(self) -> bool:
        try:
            ticker = yf.Ticker(self.fund_symbol)
            self.fund_info = ticker.info

            # Get 5 years of data for comprehensive analysis
            end_date = datetime.now()
            start_date = end_date - timedelta(days=5*365)

            self.fund_data = ticker.history(start=start_date, end=end_date)

            # Get holdings if available
            try:
                self.holdings_data = ticker.get_holdings()
            except:
                self.holdings_data = None

            return True

        except Exception as e:
            print(f"Error fetching data for {self.fund_symbol}: {e}")
            return False

    def get_basic_info(self) -> Dict[str, Any]:
        if not self.fund_info:
            return {}

        return {
            "fund_name": self.fund_info.get('longName', 'N/A'),
            "fund_family": self.fund_info.get('fundFamily', 'N/A'),
            "category": self.fund_info.get('category', 'N/A'),
            "total_assets": self.fund_info.get('totalAssets', 0),
            "expense_ratio": self.fund_info.get('annualReportExpenseRatio', 0),
            "minimum_investment": self.fund_info.get('minInvestment', 0),
            "inception_date": self.fund_info.get('fundInceptionDate', 'N/A'),
            "nav": self.fund_info.get('navPrice', 0),
            "yield": self.fund_info.get('yield', 0),
            "beta": self.fund_info.get('beta3Year', 0),
            "morningstar_rating": self.fund_info.get('morningStarOverallRating', 0),
            "morningstar_risk_rating": self.fund_info.get('morningStarRiskRating', 0)
        }

    def calculate_performance_metrics(self) -> Dict[str, Any]:
        if self.fund_data is None or self.fund_data.empty:
            return {}

        prices = self.fund_data['Close']
        returns = prices.pct_change().dropna()

        # Calculate various time period returns
        periods = {
            "1M": 30,
            "3M": 90,
            "6M": 180,
            "1Y": 252,
            "3Y": 252*3,
            "5Y": 252*5
        }

        period_returns = {}
        for period_name, days in periods.items():
            if len(prices) >= days:
                period_return = (prices.iloc[-1] / prices.iloc[-days] - 1) * 100
                period_returns[f"return_{period_name}"] = round(period_return, 2)
            else:
                period_returns[f"return_{period_name}"] = None

        # Risk metrics
        annual_volatility = returns.std() * np.sqrt(252) * 100

        # Sharpe ratio (assuming 2% risk-free rate)
        risk_free_rate = 0.02
        annual_return = returns.mean() * 252
        sharpe_ratio = (annual_return - risk_free_rate) / (annual_volatility / 100) if annual_volatility > 0 else 0

        # Maximum drawdown
        cumulative_returns = (1 + returns).cumprod()
        rolling_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - rolling_max) / rolling_max
        max_drawdown = drawdown.min() * 100

        # Value at Risk (95% confidence)
        var_95 = np.percentile(returns, 5) * 100

        # Calmar ratio
        calmar_ratio = (annual_return * 100) / abs(max_drawdown) if max_drawdown != 0 else 0

        return {
            **period_returns,
            "annual_volatility": round(annual_volatility, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "max_drawdown": round(max_drawdown, 2),
            "var_95": round(var_95, 2),
            "calmar_ratio": round(calmar_ratio, 2),
            "current_price": round(prices.iloc[-1], 2) if not prices.empty else 0
        }

    def analyze_holdings(self) -> Dict[str, Any]:
        if not self.holdings_data:
            return {"top_holdings": [], "sector_allocation": {}, "geographic_allocation": {}}

        holdings_analysis = {
            "top_holdings": [],
            "sector_allocation": {},
            "geographic_allocation": {},
            "holdings_count": 0,
            "top_10_concentration": 0
        }

        try:
            if hasattr(self.holdings_data, 'top_holdings'):
                top_holdings = self.holdings_data.top_holdings
                if top_holdings is not None and not top_holdings.empty:
                    holdings_analysis["top_holdings"] = top_holdings.head(10).to_dict('records')
                    holdings_analysis["holdings_count"] = len(top_holdings)
                    holdings_analysis["top_10_concentration"] = top_holdings.head(10)['weight'].sum() if 'weight' in top_holdings.columns else 0

            if hasattr(self.holdings_data, 'sector_weightings'):
                sector_data = self.holdings_data.sector_weightings
                if sector_data is not None and not sector_data.empty:
                    holdings_analysis["sector_allocation"] = sector_data.to_dict()

            if hasattr(self.holdings_data, 'country_weightings'):
                country_data = self.holdings_data.country_weightings
                if country_data is not None and not country_data.empty:
                    holdings_analysis["geographic_allocation"] = country_data.to_dict()

        except Exception as e:
            print(f"Error analyzing holdings: {e}")

        return holdings_analysis

    def calculate_risk_metrics(self) -> Dict[str, Any]:
        if self.fund_data is None or self.fund_data.empty:
            return {}

        returns = self.fund_data['Close'].pct_change().dropna()

        # Downside deviation
        downside_returns = returns[returns < 0]
        downside_deviation = downside_returns.std() * np.sqrt(252) * 100

        # Sortino ratio
        annual_return = returns.mean() * 252
        risk_free_rate = 0.02
        sortino_ratio = (annual_return - risk_free_rate) / (downside_deviation / 100) if downside_deviation > 0 else 0

        # Skewness and Kurtosis
        skewness = returns.skew()
        kurtosis = returns.kurtosis()

        # Beta calculation (using SPY as benchmark)
        try:
            spy = yf.download('SPY', start=self.fund_data.index[0], end=self.fund_data.index[-1])['Close']
            spy_returns = spy.pct_change().dropna()

            # Align dates
            aligned_returns = returns.reindex(spy_returns.index).dropna()
            aligned_spy = spy_returns.reindex(aligned_returns.index).dropna()

            if len(aligned_returns) > 1 and len(aligned_spy) > 1:
                beta = np.cov(aligned_returns, aligned_spy)[0][1] / np.var(aligned_spy)
                alpha = aligned_returns.mean() - beta * aligned_spy.mean()
                correlation = np.corrcoef(aligned_returns, aligned_spy)[0][1]
            else:
                beta = alpha = correlation = 0

        except:
            beta = alpha = correlation = 0

        return {
            "downside_deviation": round(downside_deviation, 2),
            "sortino_ratio": round(sortino_ratio, 2),
            "skewness": round(skewness, 2),
            "kurtosis": round(kurtosis, 2),
            "beta": round(beta, 2),
            "alpha": round(alpha * 252 * 100, 2),  # Annualized alpha in %
            "correlation_spy": round(correlation, 2)
        }

    def calculate_fund_rating(self) -> Dict[str, Any]:
        performance = self.calculate_performance_metrics()
        risk_metrics = self.calculate_risk_metrics()
        basic_info = self.get_basic_info()

        # Rating components (0-10 scale)
        ratings = {}

        # Performance rating based on Sharpe ratio
        sharpe = performance.get('sharpe_ratio', 0)
        if sharpe >= 1.5:
            ratings['performance'] = 9
        elif sharpe >= 1.0:
            ratings['performance'] = 7
        elif sharpe >= 0.5:
            ratings['performance'] = 5
        elif sharpe >= 0:
            ratings['performance'] = 3
        else:
            ratings['performance'] = 1

        # Risk rating (inverse of volatility)
        volatility = performance.get('annual_volatility', 50)
        if volatility <= 10:
            ratings['risk'] = 9
        elif volatility <= 15:
            ratings['risk'] = 7
        elif volatility <= 20:
            ratings['risk'] = 5
        elif volatility <= 30:
            ratings['risk'] = 3
        else:
            ratings['risk'] = 1

        # Cost rating (inverse of expense ratio)
        expense_ratio = basic_info.get('expense_ratio', 2)
        if expense_ratio <= 0.2:
            ratings['cost'] = 9
        elif expense_ratio <= 0.5:
            ratings['cost'] = 7
        elif expense_ratio <= 1.0:
            ratings['cost'] = 5
        elif expense_ratio <= 1.5:
            ratings['cost'] = 3
        else:
            ratings['cost'] = 1

        # Overall rating
        overall_rating = (ratings['performance'] * 0.4 +
                         ratings['risk'] * 0.3 +
                         ratings['cost'] * 0.3)

        return {
            "performance_rating": ratings['performance'],
            "risk_rating": ratings['risk'],
            "cost_rating": ratings['cost'],
            "overall_rating": round(overall_rating, 1),
            "rating_explanation": self._get_rating_explanation(overall_rating)
        }

    def _get_rating_explanation(self, rating: float) -> str:
        if rating >= 8:
            return "Excellent - Outstanding performance with low risk and costs"
        elif rating >= 6:
            return "Good - Strong performance with reasonable risk and costs"
        elif rating >= 4:
            return "Average - Moderate performance with acceptable risk and costs"
        elif rating >= 2:
            return "Below Average - Weak performance or high risk/costs"
        else:
            return "Poor - Significant concerns with performance, risk, or costs"

    def get_comprehensive_analysis(self) -> Dict[str, Any]:
        if not self.fetch_fund_data():
            return {"error": f"Could not fetch data for {self.fund_symbol}"}

        analysis = {
            "fund_symbol": self.fund_symbol,
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "basic_info": self.get_basic_info(),
            "performance_metrics": self.calculate_performance_metrics(),
            "risk_metrics": self.calculate_risk_metrics(),
            "holdings_analysis": self.analyze_holdings(),
            "fund_rating": self.calculate_fund_rating()
        }

        return analysis

    def compare_with_benchmark(self, benchmark_symbol: str = 'SPY') -> Dict[str, Any]:
        try:
            benchmark_analyzer = ComprehensiveFundAnalyzer(benchmark_symbol)
            benchmark_analysis = benchmark_analyzer.get_comprehensive_analysis()

            fund_performance = self.calculate_performance_metrics()
            benchmark_performance = benchmark_analysis.get('performance_metrics', {})

            comparison = {}
            for metric in ['return_1Y', 'return_3Y', 'return_5Y', 'annual_volatility', 'sharpe_ratio', 'max_drawdown']:
                fund_value = fund_performance.get(metric, 0)
                benchmark_value = benchmark_performance.get(metric, 0)

                if benchmark_value != 0:
                    comparison[f"{metric}_vs_benchmark"] = round(fund_value - benchmark_value, 2)
                else:
                    comparison[f"{metric}_vs_benchmark"] = None

            return {
                "benchmark_symbol": benchmark_symbol,
                "comparison_metrics": comparison,
                "outperformance_score": self._calculate_outperformance_score(comparison)
            }

        except Exception as e:
            return {"error": f"Could not compare with benchmark: {e}"}

    def _calculate_outperformance_score(self, comparison: Dict[str, float]) -> int:
        score = 0
        metrics_count = 0

        # Positive indicators
        for metric in ['return_1Y_vs_benchmark', 'return_3Y_vs_benchmark', 'return_5Y_vs_benchmark', 'sharpe_ratio_vs_benchmark']:
            if comparison.get(metric) is not None:
                if comparison[metric] > 0:
                    score += 1
                metrics_count += 1

        # Negative indicators (lower is better)
        for metric in ['annual_volatility_vs_benchmark', 'max_drawdown_vs_benchmark']:
            if comparison.get(metric) is not None:
                if comparison[metric] < 0:
                    score += 1
                metrics_count += 1

        return round((score / metrics_count) * 10) if metrics_count > 0 else 5

def analyze_fund_universe(fund_symbols: List[str]) -> pd.DataFrame:
    results = []

    for symbol in fund_symbols:
        print(f"Analyzing {symbol}...")
        analyzer = ComprehensiveFundAnalyzer(symbol)
        analysis = analyzer.get_comprehensive_analysis()

        if 'error' not in analysis:
            fund_data = {
                'Symbol': symbol,
                'Name': analysis['basic_info'].get('fund_name', 'N/A'),
                'Category': analysis['basic_info'].get('category', 'N/A'),
                'Total_Assets': analysis['basic_info'].get('total_assets', 0),
                'Expense_Ratio': analysis['basic_info'].get('expense_ratio', 0),
                'Return_1Y': analysis['performance_metrics'].get('return_1Y', 0),
                'Return_3Y': analysis['performance_metrics'].get('return_3Y', 0),
                'Annual_Volatility': analysis['performance_metrics'].get('annual_volatility', 0),
                'Sharpe_Ratio': analysis['performance_metrics'].get('sharpe_ratio', 0),
                'Max_Drawdown': analysis['performance_metrics'].get('max_drawdown', 0),
                'Overall_Rating': analysis['fund_rating'].get('overall_rating', 0),
                'Morningstar_Rating': analysis['basic_info'].get('morningstar_rating', 0)
            }
            results.append(fund_data)

    return pd.DataFrame(results)

# Popular fund symbols for testing
POPULAR_FUNDS = [
    'SPY', 'QQQ', 'VTI', 'VXUS', 'BND', 'VEA', 'VWO', 'VTEB',
    'VUG', 'VTV', 'VOO', 'VB', 'VTIAX', 'VTSAX', 'VTISX', 'VTSMX',
    'IVV', 'IEMG', 'AGG', 'ITOT', 'IXUS', 'IEFA', 'IJH', 'IJR',
    'SCHB', 'SCHA', 'SCHF', 'SCHE', 'SCHZ', 'VGT', 'VHT', 'VFH'
]

if __name__ == "__main__":
    # Example usage
    analyzer = ComprehensiveFundAnalyzer('SPY')
    analysis = analyzer.get_comprehensive_analysis()

    print("=== COMPREHENSIVE FUND ANALYSIS ===")
    print(f"Fund: {analysis['fund_symbol']}")
    print(f"Analysis Date: {analysis['analysis_date']}")
    print(f"Overall Rating: {analysis['fund_rating']['overall_rating']}/10")
    print(f"Rating Explanation: {analysis['fund_rating']['rating_explanation']}")