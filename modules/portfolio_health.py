"""
Portfolio Health Score Module
Calculates 0-100 health score based on 8 key metrics
"""

import pandas as pd
import numpy as np
import yfinance as yf
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


class PortfolioHealthScore:
    """
    Portfolio Health Score Calculator

    Metrics (8):
    1. Diversification (20%) - Sector distribution
    2. Risk (20%) - Beta / Volatility
    3. Momentum (15%) - 3-month return trend
    4. Liquidity (10%) - Average trading volume
    5. Tax Efficiency (10%) - Estimated net return difference
    6. Balance (10%) - Weighted position distribution
    7. Duration Fit (5%) - Average holding period suitability
    8. Sector Performance (10%) - Performance vs benchmark
    """

    METRIC_WEIGHTS = {
        'diversification': 0.20,
        'risk': 0.20,
        'momentum': 0.15,
        'liquidity': 0.10,
        'tax_efficiency': 0.10,
        'balance': 0.10,
        'duration_fit': 0.05,
        'sector_performance': 0.10
    }

    # Turkish sectors mapping
    TURKISH_SECTORS = {
        'Teknoloji': ['ASELS', 'LOGO', 'KAREL', 'NETAS', 'INDES'],
        'Finans': ['GARAN', 'YKBNK', 'AKBNK', 'ISCTR', 'VAKBN'],
        'Enerji': ['TUPRS', 'PETKM', 'AKSA', 'AKENR'],
        'Sanayi': ['THYAO', 'DOAS', 'PGSUS', 'TTKOM'],
        'Tüketim': ['BIMAS', 'MGROS', 'SOKM', 'CCOLA']
    }

    def __init__(self):
        self.portfolio_data = None
        self.enriched_data = None
        self.scores = {}
        self.total_score = 0
        self.recommendations = []

    def load_portfolio(self, portfolio_df: pd.DataFrame) -> pd.DataFrame:
        """
        Load and validate portfolio data

        Required columns: Symbol, Shares, Price, Value
        Optional: Sector, Beta, Return_3M
        """
        required_cols = ['Symbol', 'Shares', 'Price', 'Value']

        for col in required_cols:
            if col not in portfolio_df.columns:
                raise ValueError(f"Missing required column: {col}")

        self.portfolio_data = portfolio_df.copy()

        # Calculate weights
        total_value = self.portfolio_data['Value'].sum()
        self.portfolio_data['Weight'] = self.portfolio_data['Value'] / total_value

        return self.portfolio_data

    def enrich_portfolio_data(self) -> pd.DataFrame:
        """
        Enrich portfolio with market data from yfinance
        Adds: Sector, Beta, Volatility, Volume, MarketCap
        """
        if self.portfolio_data is None:
            raise ValueError("Portfolio not loaded. Call load_portfolio() first.")

        enriched = self.portfolio_data.copy()

        # Initialize columns
        enriched['Sector'] = ''
        enriched['Beta'] = np.nan
        enriched['Volatility'] = np.nan
        enriched['Avg_Volume'] = np.nan
        enriched['Market_Cap'] = np.nan
        enriched['Return_3M'] = np.nan
        enriched['RSI'] = np.nan

        for idx, row in enriched.iterrows():
            symbol = row['Symbol']

            # Try Turkish stocks first (add .IS suffix)
            ticker_symbol = symbol if '.' in symbol else f"{symbol}.IS"

            try:
                ticker = yf.Ticker(ticker_symbol)
                info = ticker.info
                hist = ticker.history(period="6mo")

                # Basic info
                enriched.at[idx, 'Sector'] = info.get('sector', self._guess_turkish_sector(symbol))
                enriched.at[idx, 'Beta'] = info.get('beta', 1.0)
                enriched.at[idx, 'Market_Cap'] = info.get('marketCap', 0)
                enriched.at[idx, 'Avg_Volume'] = info.get('averageVolume', 0)

                # Calculate volatility
                if len(hist) > 30:
                    returns = hist['Close'].pct_change().dropna()
                    enriched.at[idx, 'Volatility'] = returns.std() * np.sqrt(252)  # Annualized

                # Calculate 3-month return
                if len(hist) >= 60:
                    price_3m_ago = hist['Close'].iloc[-60]
                    current_price = hist['Close'].iloc[-1]
                    enriched.at[idx, 'Return_3M'] = ((current_price - price_3m_ago) / price_3m_ago) * 100

                # Calculate RSI (14-day)
                if len(hist) >= 14:
                    enriched.at[idx, 'RSI'] = self._calculate_rsi(hist['Close'], period=14)

            except Exception as e:
                print(f"Warning: Could not fetch data for {symbol}: {e}")
                # Use defaults
                enriched.at[idx, 'Sector'] = self._guess_turkish_sector(symbol)
                enriched.at[idx, 'Beta'] = 1.0
                enriched.at[idx, 'Volatility'] = 0.25

        self.enriched_data = enriched
        return enriched

    def _guess_turkish_sector(self, symbol: str) -> str:
        """Guess sector for Turkish stocks based on symbol"""
        for sector, stocks in self.TURKISH_SECTORS.items():
            if symbol.upper() in stocks:
                return sector
        return 'Diğer'

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]

    def calculate_all_metrics(self) -> Dict[str, float]:
        """Calculate all 8 health metrics"""
        if self.enriched_data is None:
            raise ValueError("Portfolio data not enriched. Call enrich_portfolio_data() first.")

        self.scores = {
            'diversification': self._calculate_diversification_score(),
            'risk': self._calculate_risk_score(),
            'momentum': self._calculate_momentum_score(),
            'liquidity': self._calculate_liquidity_score(),
            'tax_efficiency': self._calculate_tax_efficiency_score(),
            'balance': self._calculate_balance_score(),
            'duration_fit': self._calculate_duration_fit_score(),
            'sector_performance': self._calculate_sector_performance_score()
        }

        # Calculate total weighted score
        self.total_score = sum(
            self.scores[metric] * weight
            for metric, weight in self.METRIC_WEIGHTS.items()
        )

        # Generate recommendations
        self._generate_recommendations()

        return self.scores

    def _calculate_diversification_score(self) -> float:
        """
        Score: 0-100
        Perfect: 10+ stocks, well-distributed sectors
        """
        df = self.enriched_data
        num_stocks = len(df)

        # Stock count component (50%)
        if num_stocks >= 15:
            stock_score = 100
        elif num_stocks >= 10:
            stock_score = 90
        elif num_stocks >= 7:
            stock_score = 75
        elif num_stocks >= 5:
            stock_score = 60
        elif num_stocks >= 3:
            stock_score = 40
        else:
            stock_score = 20

        # Sector distribution component (50%)
        sector_weights = df.groupby('Sector')['Weight'].sum()
        max_sector_weight = sector_weights.max()

        if max_sector_weight <= 0.25:  # No sector > 25%
            sector_score = 100
        elif max_sector_weight <= 0.35:
            sector_score = 80
        elif max_sector_weight <= 0.50:
            sector_score = 60
        elif max_sector_weight <= 0.70:
            sector_score = 40
        else:
            sector_score = 20

        return (stock_score * 0.5 + sector_score * 0.5)

    def _calculate_risk_score(self) -> float:
        """
        Score: 0-100
        Perfect: Portfolio beta 0.8-1.2, moderate volatility
        """
        df = self.enriched_data

        # Weighted average beta
        avg_beta = (df['Beta'] * df['Weight']).sum()

        # Weighted average volatility
        avg_vol = (df['Volatility'] * df['Weight']).sum()

        # Beta score (50%)
        if 0.8 <= avg_beta <= 1.2:
            beta_score = 100
        elif 0.6 <= avg_beta <= 1.5:
            beta_score = 80
        elif 0.4 <= avg_beta <= 1.8:
            beta_score = 60
        else:
            beta_score = 40

        # Volatility score (50%)
        # Ideal volatility: 15-25% annualized
        if 0.15 <= avg_vol <= 0.25:
            vol_score = 100
        elif 0.10 <= avg_vol <= 0.35:
            vol_score = 80
        elif 0.05 <= avg_vol <= 0.50:
            vol_score = 60
        else:
            vol_score = 40

        return (beta_score * 0.5 + vol_score * 0.5)

    def _calculate_momentum_score(self) -> float:
        """
        Score: 0-100
        Perfect: 70%+ stocks with positive 3M momentum
        """
        df = self.enriched_data

        # Filter valid return data
        valid_returns = df['Return_3M'].dropna()

        if len(valid_returns) == 0:
            return 50  # Neutral if no data

        positive_returns = (valid_returns > 0).sum()
        positive_pct = positive_returns / len(valid_returns)

        # Weighted average return
        avg_return = (df['Return_3M'] * df['Weight']).sum()

        # Positive ratio score (60%)
        if positive_pct >= 0.75:
            ratio_score = 100
        elif positive_pct >= 0.60:
            ratio_score = 85
        elif positive_pct >= 0.50:
            ratio_score = 70
        elif positive_pct >= 0.40:
            ratio_score = 55
        else:
            ratio_score = 40

        # Average return score (40%)
        if avg_return >= 10:
            return_score = 100
        elif avg_return >= 5:
            return_score = 85
        elif avg_return >= 0:
            return_score = 70
        elif avg_return >= -5:
            return_score = 50
        else:
            return_score = 30

        return (ratio_score * 0.6 + return_score * 0.4)

    def _calculate_liquidity_score(self) -> float:
        """
        Score: 0-100
        Perfect: All stocks with daily volume > $1M equivalent
        """
        df = self.enriched_data

        # Calculate average volume in dollars (approximate)
        df['Volume_USD'] = df['Avg_Volume'] * df['Price']

        # Threshold: 1M for large cap, 100K for mid/small
        high_liquidity = (df['Volume_USD'] >= 1_000_000).sum()
        medium_liquidity = ((df['Volume_USD'] >= 100_000) & (df['Volume_USD'] < 1_000_000)).sum()
        low_liquidity = (df['Volume_USD'] < 100_000).sum()

        total_stocks = len(df)

        score = (
            (high_liquidity / total_stocks) * 100 +
            (medium_liquidity / total_stocks) * 60 +
            (low_liquidity / total_stocks) * 20
        )

        return min(score, 100)

    def _calculate_tax_efficiency_score(self) -> float:
        """
        Score: 0-100
        Turkish tax optimization (stopaj, holding period)

        Note: This is simplified. Real implementation needs holding dates.
        """
        # Placeholder: Assume we have holding period data
        # For MVP, use proxy: dividend yield stocks lose to tax

        df = self.enriched_data

        # Simple heuristic: Prefer growth over dividend for tax efficiency
        # Growth stocks (low dividend) score higher

        # For MVP, give neutral-positive score
        return 75  # TODO: Implement real tax calculation when holding dates available

    def _calculate_balance_score(self) -> float:
        """
        Score: 0-100
        Perfect: No single position > 15%, top 3 positions < 40%
        """
        df = self.enriched_data.sort_values('Weight', ascending=False)

        max_position = df['Weight'].max()
        top3_weight = df['Weight'].head(3).sum()

        # Max position score (60%)
        if max_position <= 0.10:
            max_score = 100
        elif max_position <= 0.15:
            max_score = 85
        elif max_position <= 0.20:
            max_score = 70
        elif max_position <= 0.30:
            max_score = 50
        else:
            max_score = 30

        # Top 3 concentration score (40%)
        if top3_weight <= 0.35:
            top3_score = 100
        elif top3_weight <= 0.45:
            top3_score = 80
        elif top3_weight <= 0.60:
            top3_score = 60
        else:
            top3_score = 40

        return (max_score * 0.6 + top3_score * 0.4)

    def _calculate_duration_fit_score(self) -> float:
        """
        Score: 0-100
        Placeholder for holding period analysis
        """
        # TODO: Implement when we have transaction history
        return 70  # Neutral score for MVP

    def _calculate_sector_performance_score(self) -> float:
        """
        Score: 0-100
        Portfolio performance vs benchmark (e.g., BIST100 or S&P500)
        """
        df = self.enriched_data

        # Weighted 3M return
        portfolio_return = (df['Return_3M'] * df['Weight']).sum()

        # Compare to benchmark (assume 5% as neutral)
        benchmark_return = 5.0

        outperformance = portfolio_return - benchmark_return

        if outperformance >= 5:
            return 100
        elif outperformance >= 2:
            return 85
        elif outperformance >= 0:
            return 70
        elif outperformance >= -3:
            return 55
        else:
            return 40

    def _generate_recommendations(self):
        """Generate actionable recommendations based on weak scores"""
        self.recommendations = []

        for metric, score in self.scores.items():
            if score < 60:  # Weak score
                rec = self._get_recommendation_for_metric(metric, score)
                if rec:
                    self.recommendations.append(rec)

    def _get_recommendation_for_metric(self, metric: str, score: float) -> str:
        """Get specific recommendation for each metric"""
        df = self.enriched_data

        recommendations_map = {
            'diversification': self._recommend_diversification(df),
            'risk': self._recommend_risk_management(df),
            'momentum': self._recommend_momentum_improvement(df),
            'liquidity': self._recommend_liquidity_improvement(df),
            'balance': self._recommend_balance_improvement(df),
            'sector_performance': self._recommend_sector_changes(df)
        }

        return recommendations_map.get(metric, '')

    def _recommend_diversification(self, df: pd.DataFrame) -> str:
        """Recommend diversification improvements"""
        num_stocks = len(df)
        sector_weights = df.groupby('Sector')['Weight'].sum().sort_values(ascending=False)
        max_sector = sector_weights.index[0]
        max_weight = sector_weights.iloc[0]

        if num_stocks < 7:
            return f"⚠️ Portföyde sadece {num_stocks} hisse var. En az 7-10 hisseye çıkarmayı düşünün."

        if max_weight > 0.40:
            return f"⚠️ {max_sector} sektörü portföyün %{max_weight*100:.0f}'ini oluşturuyor. Diğer sektörlere ağırlık verin."

        return ""

    def _recommend_risk_management(self, df: pd.DataFrame) -> str:
        """Recommend risk improvements"""
        avg_beta = (df['Beta'] * df['Weight']).sum()
        avg_vol = (df['Volatility'] * df['Weight']).sum()

        if avg_beta > 1.5:
            return f"⚠️ Portföy betası yüksek ({avg_beta:.2f}). Defansif hisseler (beta < 1) eklemeyi düşünün."
        elif avg_beta < 0.6:
            return f"⚠️ Portföy betası düşük ({avg_beta:.2f}). Daha agresif büyüme hisseleri ekleyebilirsiniz."

        if avg_vol > 0.40:
            return f"⚠️ Portföy volatilitesi yüksek (%{avg_vol*100:.0f}). Blue-chip hisseler ile dengeyin."

        return ""

    def _recommend_momentum_improvement(self, df: pd.DataFrame) -> str:
        """Recommend momentum improvements"""
        negative_stocks = df[df['Return_3M'] < -5]

        if len(negative_stocks) > 0:
            worst = negative_stocks.nsmallest(3, 'Return_3M')
            symbols = ', '.join(worst['Symbol'].tolist())
            return f"⚠️ Zayıf momentum: {symbols} hisseleri son 3 ayda düşüşte. Gözden geçirin."

        return ""

    def _recommend_liquidity_improvement(self, df: pd.DataFrame) -> str:
        """Recommend liquidity improvements"""
        df['Volume_USD'] = df['Avg_Volume'] * df['Price']
        low_liquidity = df[df['Volume_USD'] < 100_000]

        if len(low_liquidity) > 0:
            symbols = ', '.join(low_liquidity['Symbol'].tolist())
            return f"⚠️ Düşük likidite: {symbols} hisselerinin işlem hacmi düşük. Çıkış zorluğu olabilir."

        return ""

    def _recommend_balance_improvement(self, df: pd.DataFrame) -> str:
        """Recommend balance improvements"""
        max_position = df.loc[df['Weight'].idxmax()]

        if max_position['Weight'] > 0.25:
            return f"⚠️ {max_position['Symbol']} portföyün %{max_position['Weight']*100:.0f}'ini oluşturuyor. Pozisyonu azaltın."

        return ""

    def _recommend_sector_changes(self, df: pd.DataFrame) -> str:
        """Recommend sector allocation changes"""
        sector_returns = df.groupby('Sector').apply(
            lambda x: (x['Return_3M'] * x['Weight']).sum() / x['Weight'].sum()
        ).sort_values()

        if len(sector_returns) > 0:
            worst_sector = sector_returns.index[0]
            worst_return = sector_returns.iloc[0]

            if worst_return < -5:
                return f"⚠️ {worst_sector} sektörü zayıf performans gösteriyor (%{worst_return:.1f}). Ağırlığı azaltın."

        return ""

    def get_summary(self) -> Dict:
        """Get complete health score summary"""
        return {
            'total_score': round(self.total_score, 1),
            'grade': self._get_grade(self.total_score),
            'metric_scores': {k: round(v, 1) for k, v in self.scores.items()},
            'recommendations': self.recommendations,
            'portfolio_stats': {
                'num_stocks': len(self.enriched_data),
                'total_value': self.enriched_data['Value'].sum(),
                'avg_return_3m': (self.enriched_data['Return_3M'] * self.enriched_data['Weight']).sum(),
                'avg_beta': (self.enriched_data['Beta'] * self.enriched_data['Weight']).sum(),
                'num_sectors': self.enriched_data['Sector'].nunique()
            }
        }

    def _get_grade(self, score: float) -> str:
        """Convert score to letter grade"""
        if score >= 90:
            return '🏆 Mükemmel'
        elif score >= 80:
            return '✅ Çok İyi'
        elif score >= 70:
            return '👍 İyi'
        elif score >= 60:
            return '⚠️ Orta'
        else:
            return '❌ Zayıf'
