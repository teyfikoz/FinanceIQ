"""
Fund Flow Radar - Track money flows into/out of funds and sectors
Analyzes institutional investor behavior through fund flow patterns
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px


class FundFlowRadar:
    """
    Track and analyze fund flows for Turkish and US markets

    Key Features:
    - TEFAS (Turkish funds) flow tracking
    - ETF flow analysis (US markets)
    - Sector-level aggregation
    - Flow anomaly detection
    - Sankey diagrams for flow visualization
    """

    # Turkish fund categories mapped to sectors
    TEFAS_CATEGORIES = {
        'Hisse Senedi Fonları': ['Teknoloji', 'Finans', 'Sanayi', 'Tüketim'],
        'Değişken Fonlar': ['Mixed'],
        'Tahvil Bono Fonları': ['Bonds'],
        'Para Piyasası Fonları': ['Money Market'],
        'Altın ve Diğer Kıymetli Madenler': ['Gold'],
        'Fonlar Fonu': ['Fund of Funds']
    }

    # Major Turkish funds to track
    MAJOR_TEFAS_FUNDS = [
        'AAV', 'AEH', 'AFT', 'AHE', 'AHU', 'AJZ', 'AKU', 'YAT',
        'GAH', 'GBH', 'GYH', 'GPD', 'GVF', 'GYE', 'IAH', 'IAS',
        'KAY', 'TGY', 'ZPX', 'ZRH'
    ]

    def __init__(self):
        """Initialize Fund Flow Radar"""
        self.flow_data = None
        self.sector_flows = None

    def fetch_tefas_fund_data(
        self,
        fund_code: str,
        start_date: str,
        end_date: str
    ) -> Optional[pd.DataFrame]:
        """
        Fetch TEFAS fund historical data

        Args:
            fund_code: TEFAS fund code (e.g., 'AAV')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with columns: date, price, total_value, num_shares
        """
        try:
            # TEFAS API endpoint (simplified - in production use official API)
            # Note: This is a placeholder - actual implementation would use TEFAS API
            # For now, return synthetic data for demonstration

            dates = pd.date_range(start=start_date, end=end_date, freq='D')

            # Synthetic fund data (replace with actual API call)
            np.random.seed(hash(fund_code) % 2**32)

            data = {
                'date': dates,
                'price': 100 + np.cumsum(np.random.randn(len(dates)) * 0.5),
                'total_value': 1_000_000_000 + np.cumsum(np.random.randn(len(dates)) * 10_000_000),
                'num_shares': None  # Will calculate
            }

            df = pd.DataFrame(data)
            df['num_shares'] = df['total_value'] / df['price']

            return df

        except Exception as e:
            print(f"Error fetching TEFAS data for {fund_code}: {str(e)}")
            return None

    def calculate_net_flows(
        self,
        fund_data: pd.DataFrame,
        price_col: str = 'price',
        aum_col: str = 'total_value'
    ) -> pd.DataFrame:
        """
        Calculate net flows (money in/out excluding market performance)

        Formula:
        Net Flow = AUM_t - AUM_{t-1} - (Return_{t-1} * AUM_{t-1})

        Where:
        - AUM_t = Assets Under Management at time t
        - Return_{t-1} = (Price_t - Price_{t-1}) / Price_{t-1}

        Args:
            fund_data: DataFrame with price and AUM data
            price_col: Name of price column
            aum_col: Name of AUM column

        Returns:
            DataFrame with net_flow column added
        """
        df = fund_data.copy()

        # Calculate returns
        df['return_pct'] = df[price_col].pct_change() * 100

        # Calculate expected AUM based on performance
        df['expected_aum'] = df[aum_col].shift(1) * (1 + df['return_pct'] / 100)

        # Net flow = Actual AUM - Expected AUM
        df['net_flow'] = df[aum_col] - df['expected_aum']

        # First row will be NaN, fill with 0
        df['net_flow'] = df['net_flow'].fillna(0)

        return df

    def aggregate_flows_by_period(
        self,
        flow_data: pd.DataFrame,
        period: str = '7d'
    ) -> pd.DataFrame:
        """
        Aggregate flows by time period

        Args:
            flow_data: DataFrame with net_flow column
            period: '7d', '30d', '90d', 'ytd'

        Returns:
            DataFrame with aggregated flows
        """
        df = flow_data.copy()
        df['date'] = pd.to_datetime(df['date'])

        # Calculate period start date
        end_date = df['date'].max()

        if period == '7d':
            start_date = end_date - timedelta(days=7)
        elif period == '30d':
            start_date = end_date - timedelta(days=30)
        elif period == '90d':
            start_date = end_date - timedelta(days=90)
        elif period == 'ytd':
            start_date = datetime(end_date.year, 1, 1)
        else:
            start_date = end_date - timedelta(days=30)

        # Filter to period
        period_data = df[df['date'] >= start_date].copy()

        # Aggregate
        agg_data = {
            'total_flow': period_data['net_flow'].sum(),
            'avg_daily_flow': period_data['net_flow'].mean(),
            'flow_volatility': period_data['net_flow'].std(),
            'days_inflow': (period_data['net_flow'] > 0).sum(),
            'days_outflow': (period_data['net_flow'] < 0).sum(),
            'largest_inflow': period_data['net_flow'].max(),
            'largest_outflow': period_data['net_flow'].min()
        }

        return pd.DataFrame([agg_data])

    def fetch_multiple_funds(
        self,
        fund_codes: List[str],
        start_date: str,
        end_date: str
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for multiple funds

        Args:
            fund_codes: List of TEFAS fund codes
            start_date: Start date
            end_date: End date

        Returns:
            Dict mapping fund_code to DataFrame
        """
        results = {}

        for fund_code in fund_codes:
            data = self.fetch_tefas_fund_data(fund_code, start_date, end_date)

            if data is not None:
                # Calculate net flows
                data = self.calculate_net_flows(data)
                results[fund_code] = data

        return results

    def aggregate_sector_flows(
        self,
        fund_flows: Dict[str, pd.DataFrame],
        fund_sectors: Dict[str, str],
        period: str = '7d'
    ) -> pd.DataFrame:
        """
        Aggregate flows by sector

        Args:
            fund_flows: Dict of fund_code -> flow DataFrame
            fund_sectors: Dict of fund_code -> sector
            period: Aggregation period

        Returns:
            DataFrame with sector-level flows
        """
        sector_data = []

        for fund_code, flow_df in fund_flows.items():
            sector = fund_sectors.get(fund_code, 'Unknown')

            # Aggregate this fund's flows
            agg = self.aggregate_flows_by_period(flow_df, period)
            agg['fund_code'] = fund_code
            agg['sector'] = sector

            sector_data.append(agg)

        # Combine all funds
        all_funds_df = pd.concat(sector_data, ignore_index=True)

        # Aggregate by sector
        sector_agg = all_funds_df.groupby('sector').agg({
            'total_flow': 'sum',
            'avg_daily_flow': 'mean',
            'flow_volatility': 'mean',
            'fund_code': 'count'  # Number of funds
        }).reset_index()

        sector_agg.columns = ['sector', 'net_flow', 'avg_daily_flow', 'volatility', 'num_funds']

        # Sort by net flow
        sector_agg = sector_agg.sort_values('net_flow', ascending=False)

        return sector_agg

    def detect_flow_anomalies(
        self,
        flow_data: pd.DataFrame,
        threshold_std: float = 2.0
    ) -> List[Dict]:
        """
        Detect unusual flow patterns (outliers)

        Args:
            flow_data: DataFrame with net_flow column
            threshold_std: Number of standard deviations for anomaly

        Returns:
            List of anomaly dicts
        """
        df = flow_data.copy()

        # Calculate statistics
        mean_flow = df['net_flow'].mean()
        std_flow = df['net_flow'].std()

        # Z-score
        df['z_score'] = (df['net_flow'] - mean_flow) / std_flow

        # Detect anomalies
        anomalies = df[abs(df['z_score']) > threshold_std].copy()

        results = []
        for _, row in anomalies.iterrows():
            results.append({
                'date': row['date'],
                'net_flow': row['net_flow'],
                'z_score': row['z_score'],
                'type': 'massive_inflow' if row['z_score'] > 0 else 'massive_outflow',
                'magnitude': abs(row['z_score'])
            })

        return results

    def create_flow_sankey(
        self,
        sector_flows: pd.DataFrame,
        min_flow_threshold: float = 0
    ) -> go.Figure:
        """
        Create Sankey diagram for fund flows

        Flow: Investors → Sectors → Individual Funds

        Args:
            sector_flows: DataFrame with sector-level flows
            min_flow_threshold: Minimum flow to show

        Returns:
            Plotly Sankey figure
        """
        # Filter significant flows
        significant_flows = sector_flows[
            abs(sector_flows['net_flow']) >= min_flow_threshold
        ].copy()

        # Separate inflows and outflows
        inflows = significant_flows[significant_flows['net_flow'] > 0].copy()
        outflows = significant_flows[significant_flows['net_flow'] < 0].copy()

        # Build nodes
        nodes = ['Yatırımcılar (Giriş)', 'Yatırımcılar (Çıkış)']
        node_colors = ['green', 'red']

        # Add sector nodes
        for sector in significant_flows['sector'].unique():
            nodes.append(sector)
            # Color based on net flow
            net = significant_flows[significant_flows['sector'] == sector]['net_flow'].sum()
            node_colors.append('lightgreen' if net > 0 else 'lightcoral')

        # Build links
        sources = []
        targets = []
        values = []
        link_colors = []

        # Inflows: Investors → Sectors
        for _, row in inflows.iterrows():
            sources.append(0)  # Investors (Inflow)
            targets.append(nodes.index(row['sector']))
            values.append(row['net_flow'])
            link_colors.append('rgba(0, 200, 0, 0.3)')

        # Outflows: Sectors → Investors
        for _, row in outflows.iterrows():
            sources.append(nodes.index(row['sector']))
            targets.append(1)  # Investors (Outflow)
            values.append(abs(row['net_flow']))
            link_colors.append('rgba(200, 0, 0, 0.3)')

        # Create Sankey
        fig = go.Figure(go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color='black', width=0.5),
                label=nodes,
                color=node_colors
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values,
                color=link_colors
            )
        ))

        fig.update_layout(
            title="Fon Akış Haritası (Para Girişi ← → Para Çıkışı)",
            font=dict(size=12),
            height=500
        )

        return fig

    def create_flow_heatmap(
        self,
        fund_flows: Dict[str, pd.DataFrame],
        fund_sectors: Dict[str, str]
    ) -> go.Figure:
        """
        Create heatmap of flows over time by sector

        Args:
            fund_flows: Dict of fund_code -> flow DataFrame
            fund_sectors: Dict of fund_code -> sector

        Returns:
            Plotly heatmap figure
        """
        # Aggregate daily flows by sector
        daily_sector_flows = []

        for fund_code, flow_df in fund_flows.items():
            sector = fund_sectors.get(fund_code, 'Unknown')
            temp = flow_df[['date', 'net_flow']].copy()
            temp['sector'] = sector
            daily_sector_flows.append(temp)

        # Combine
        all_flows = pd.concat(daily_sector_flows, ignore_index=True)

        # Pivot
        pivot = all_flows.pivot_table(
            values='net_flow',
            index='sector',
            columns='date',
            aggfunc='sum',
            fill_value=0
        )

        # Create heatmap
        fig = go.Figure(go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            colorscale='RdYlGn',
            zmid=0,
            colorbar=dict(title='Net Flow (₺)')
        ))

        fig.update_layout(
            title='Sektörel Para Akışı - Isı Haritası',
            xaxis_title='Tarih',
            yaxis_title='Sektör',
            height=400
        )

        return fig

    def calculate_flow_momentum(
        self,
        flow_data: pd.DataFrame,
        window: int = 7
    ) -> pd.DataFrame:
        """
        Calculate flow momentum (moving average)

        Args:
            flow_data: DataFrame with net_flow
            window: Moving average window

        Returns:
            DataFrame with flow_momentum column
        """
        df = flow_data.copy()
        df['flow_momentum'] = df['net_flow'].rolling(window=window).mean()
        df['flow_acceleration'] = df['flow_momentum'].diff()

        return df

    def generate_flow_signals(
        self,
        sector_flows: pd.DataFrame,
        threshold_pct: float = 10
    ) -> List[Dict]:
        """
        Generate investment signals based on flows

        Args:
            sector_flows: Sector-level flow data
            threshold_pct: Minimum flow % for signal

        Returns:
            List of signal dicts
        """
        signals = []

        # Calculate total flow
        total_flow = sector_flows['net_flow'].sum()

        for _, row in sector_flows.iterrows():
            flow_pct = (row['net_flow'] / total_flow * 100) if total_flow != 0 else 0

            if abs(flow_pct) >= threshold_pct:
                signal_type = 'BULLISH' if row['net_flow'] > 0 else 'BEARISH'
                strength = 'STRONG' if abs(flow_pct) >= 20 else 'MODERATE'

                signals.append({
                    'sector': row['sector'],
                    'signal': signal_type,
                    'strength': strength,
                    'flow_amount': row['net_flow'],
                    'flow_pct': flow_pct,
                    'num_funds': row.get('num_funds', 0)
                })

        return signals


def quick_flow_analysis(
    fund_codes: List[str],
    period: str = '30d'
) -> Dict:
    """
    Quick convenience function for flow analysis

    Args:
        fund_codes: List of TEFAS fund codes
        period: Analysis period

    Returns:
        Dict with analysis results
    """
    radar = FundFlowRadar()

    # Calculate date range
    end_date = datetime.now()
    if period == '7d':
        start_date = end_date - timedelta(days=7)
    elif period == '30d':
        start_date = end_date - timedelta(days=30)
    elif period == '90d':
        start_date = end_date - timedelta(days=90)
    else:
        start_date = end_date - timedelta(days=30)

    # Fetch data
    fund_flows = radar.fetch_multiple_funds(
        fund_codes,
        start_date.strftime('%Y-%m-%d'),
        end_date.strftime('%Y-%m-%d')
    )

    # Mock sector mapping (in production, use actual categorization)
    fund_sectors = {code: 'Hisse Senedi' if i % 3 == 0 else 'Tahvil' if i % 3 == 1 else 'Karma'
                    for i, code in enumerate(fund_codes)}

    # Aggregate by sector
    sector_flows = radar.aggregate_sector_flows(fund_flows, fund_sectors, period)

    # Generate signals
    signals = radar.generate_flow_signals(sector_flows)

    return {
        'sector_flows': sector_flows,
        'signals': signals,
        'fund_flows': fund_flows
    }
