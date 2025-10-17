"""
Fund Holdings Analytics
Fonların hisse dağılımları ve hisse-fon analizi için analitik modül
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import yfinance as yf

from .base import BaseAnalytics


class FundHoldingsAnalytics(BaseAnalytics):
    """Fund holdings analizi için sınıf."""

    def __init__(self):
        super().__init__()

    def analyze_fund_holdings(self, fund_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fund holdings verilerini analiz et."""
        try:
            if not fund_data.get("holdings"):
                return {"error": "No holdings data available"}

            holdings = fund_data["holdings"]
            df = pd.DataFrame(holdings)

            if df.empty:
                return {"error": "Empty holdings data"}

            # Temel metrikler
            total_holdings = len(holdings)
            top_holdings = df.nlargest(10, 'percent_out') if 'percent_out' in df.columns else df.head(10)

            # Konsantrasyon analizi
            if 'percent_out' in df.columns:
                top_5_concentration = df.nlargest(5, 'percent_out')['percent_out'].sum()
                top_10_concentration = df.nlargest(10, 'percent_out')['percent_out'].sum()
            else:
                top_5_concentration = 0
                top_10_concentration = 0

            analysis = {
                "fund_symbol": fund_data.get("symbol"),
                "fund_name": fund_data.get("name"),
                "metrics": {
                    "total_holdings": total_holdings,
                    "top_5_concentration": round(top_5_concentration, 2),
                    "top_10_concentration": round(top_10_concentration, 2),
                    "diversification_score": self._calculate_diversification_score(df),
                    "total_assets": fund_data.get("total_assets"),
                    "expense_ratio": fund_data.get("expense_ratio")
                },
                "top_holdings": top_holdings.to_dict('records') if not top_holdings.empty else [],
                "analysis_date": datetime.utcnow().isoformat()
            }

            return analysis

        except Exception as e:
            self.logger.error(f"Fund holdings analysis failed", error=str(e))
            return {"error": str(e)}

    def analyze_stock_in_funds(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """Bir hisse senedinin fon dağılımını analiz et."""
        try:
            if not stock_data.get("funds_containing_stock"):
                return {"error": "No fund data available for this stock"}

            funds = stock_data["funds_containing_stock"]
            df = pd.DataFrame(funds)

            if df.empty:
                return {"error": "No funds contain this stock"}

            # Temel metrikler
            fund_count = len(funds)
            max_weight = max([f.get("weight_percent", 0) for f in funds])
            avg_weight = np.mean([f.get("weight_percent", 0) for f in funds])

            # Fon tiplerini analiz et
            fund_types = self._categorize_funds([f.get("fund_symbol", "") for f in funds])

            analysis = {
                "stock_symbol": stock_data.get("stock_symbol"),
                "stock_name": stock_data.get("stock_name"),
                "metrics": {
                    "fund_count": fund_count,
                    "max_weight_percent": round(max_weight, 4),
                    "avg_weight_percent": round(avg_weight, 4),
                    "fund_types": fund_types,
                    "liquidity_score": self._calculate_liquidity_score(funds)
                },
                "fund_distribution": funds,
                "analysis_date": datetime.utcnow().isoformat()
            }

            return analysis

        except Exception as e:
            self.logger.error(f"Stock in funds analysis failed", error=str(e))
            return {"error": str(e)}

    def create_holdings_pie_chart(self, fund_data: Dict[str, Any], lang: str = "tr") -> go.Figure:
        """Fund holdings için pasta grafiği oluştur."""
        try:
            holdings = fund_data.get("holdings", [])
            if not holdings:
                return self._create_empty_chart("No holdings data available")

            df = pd.DataFrame(holdings)
            if df.empty or 'percent_out' not in df.columns:
                return self._create_empty_chart("Invalid holdings data")

            # En büyük 10 holding + diğerleri
            top_10 = df.nlargest(10, 'percent_out')
            others_sum = df[~df.index.isin(top_10.index)]['percent_out'].sum()

            if others_sum > 0:
                others_row = pd.DataFrame({
                    'holder': ['Others' if lang == 'en' else 'Diğerleri'],
                    'percent_out': [others_sum]
                })
                plot_data = pd.concat([top_10[['holder', 'percent_out']], others_row], ignore_index=True)
            else:
                plot_data = top_10[['holder', 'percent_out']]

            # Grafik oluştur
            fig = px.pie(
                plot_data,
                values='percent_out',
                names='holder',
                title=f"{fund_data.get('name', 'Fund')} Holdings Distribution" if lang == 'en' else f"{fund_data.get('name', 'Fon')} Holding Dağılımı"
            )

            fig.update_traces(
                textposition='inside',
                textinfo='percent+label',
                hovertemplate='<b>%{label}</b><br>Percent: %{value:.2f}%<extra></extra>'
            )

            fig.update_layout(
                showlegend=True,
                legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.01),
                margin=dict(l=20, r=150, t=60, b=20),
                font=dict(size=12)
            )

            return fig

        except Exception as e:
            self.logger.error(f"Holdings pie chart creation failed", error=str(e))
            return self._create_empty_chart("Chart creation failed")

    def create_stock_funds_bar_chart(self, stock_data: Dict[str, Any], lang: str = "tr") -> go.Figure:
        """Hisse senedinin fon ağırlıkları için bar grafiği."""
        try:
            funds = stock_data.get("funds_containing_stock", [])
            if not funds:
                return self._create_empty_chart("No fund data available")

            df = pd.DataFrame(funds)
            if df.empty:
                return self._create_empty_chart("No funds contain this stock")

            # Weight'e göre sırala
            df = df.sort_values('weight_percent', ascending=True)

            fig = go.Figure()

            fig.add_trace(go.Bar(
                x=df['weight_percent'],
                y=df['fund_symbol'],
                orientation='h',
                text=[f"{w:.3f}%" for w in df['weight_percent']],
                textposition='auto',
                hovertemplate='<b>%{y}</b><br>Weight: %{x:.4f}%<extra></extra>',
                marker=dict(
                    color=df['weight_percent'],
                    colorscale='Blues',
                    showscale=True,
                    colorbar=dict(title="Weight %" if lang == 'en' else "Ağırlık %")
                )
            ))

            fig.update_layout(
                title=f"{stock_data.get('stock_symbol', 'Stock')} Weight in Funds" if lang == 'en' else f"{stock_data.get('stock_symbol', 'Hisse')} Fonlardaki Ağırlığı",
                xaxis_title="Weight Percentage" if lang == 'en' else "Ağırlık Yüzdesi",
                yaxis_title="Fund Symbol" if lang == 'en' else "Fon Sembolü",
                margin=dict(l=100, r=50, t=60, b=50),
                height=max(400, len(df) * 30),
                font=dict(size=11)
            )

            return fig

        except Exception as e:
            self.logger.error(f"Stock funds bar chart creation failed", error=str(e))
            return self._create_empty_chart("Chart creation failed")

    def create_funds_comparison_chart(self, funds_performance: Dict[str, Any], lang: str = "tr") -> go.Figure:
        """Fonların performans karşılaştırma grafiği."""
        try:
            performance_data = funds_performance.get("performance_comparison", {})
            if not performance_data:
                return self._create_empty_chart("No performance data available")

            symbols = list(performance_data.keys())
            returns = [data["total_return"] for data in performance_data.values()]
            volatilities = [data["volatility"] for data in performance_data.values()]
            names = [data["name"][:30] + "..." if len(data["name"]) > 30 else data["name"]
                    for data in performance_data.values()]

            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=volatilities,
                y=returns,
                mode='markers+text',
                text=symbols,
                textposition='top center',
                marker=dict(
                    size=12,
                    color=returns,
                    colorscale='RdYlGn',
                    showscale=True,
                    colorbar=dict(title="Return %" if lang == 'en' else "Getiri %")
                ),
                hovertemplate='<b>%{text}</b><br>Return: %{y:.2f}%<br>Volatility: %{x:.2f}%<extra></extra>'
            ))

            fig.update_layout(
                title="Risk-Return Profile of Funds" if lang == 'en' else "Fonların Risk-Getiri Profili",
                xaxis_title="Volatility %" if lang == 'en' else "Volatilite %",
                yaxis_title="Return %" if lang == 'en' else "Getiri %",
                margin=dict(l=50, r=50, t=60, b=50),
                height=500,
                font=dict(size=12)
            )

            return fig

        except Exception as e:
            self.logger.error(f"Funds comparison chart creation failed", error=str(e))
            return self._create_empty_chart("Chart creation failed")

    def create_sector_allocation_chart(self, sector_data: Dict[str, Any], lang: str = "tr") -> go.Figure:
        """Sektör dağılım grafiği."""
        try:
            sectors = sector_data.get("sector_breakdown", {})
            if not sectors:
                return self._create_empty_chart("No sector data available")

            # Sektör verilerini hazırla
            sector_names = list(sectors.keys())
            sector_weights = list(sectors.values())

            fig = px.bar(
                x=sector_weights,
                y=sector_names,
                orientation='h',
                title=f"{sector_data.get('name', 'Fund')} Sector Allocation" if lang == 'en' else f"{sector_data.get('name', 'Fon')} Sektör Dağılımı"
            )

            fig.update_traces(
                text=[f"{w:.1f}%" for w in sector_weights],
                textposition='auto',
                hovertemplate='<b>%{y}</b><br>Weight: %{x:.2f}%<extra></extra>'
            )

            fig.update_layout(
                xaxis_title="Weight %" if lang == 'en' else "Ağırlık %",
                yaxis_title="Sector" if lang == 'en' else "Sektör",
                margin=dict(l=150, r=50, t=60, b=50),
                height=max(400, len(sector_names) * 25),
                font=dict(size=11)
            )

            return fig

        except Exception as e:
            self.logger.error(f"Sector allocation chart creation failed", error=str(e))
            return self._create_empty_chart("Chart creation failed")

    def _calculate_diversification_score(self, holdings_df: pd.DataFrame) -> float:
        """Diversifikasyon skoru hesapla (0-100)."""
        try:
            if holdings_df.empty or 'percent_out' not in holdings_df.columns:
                return 0

            # Herfindahl Index kullanarak konsantrasyon hesapla
            weights = holdings_df['percent_out'].values / 100
            herfindahl = np.sum(weights ** 2)

            # Diversifikasyon skoru (100 = mükemmel diversifikasyon)
            diversification = (1 - herfindahl) * 100

            return round(diversification, 2)

        except Exception:
            return 0

    def _calculate_liquidity_score(self, funds_data: List[Dict]) -> float:
        """Likidite skoru hesapla (fon sayısı ve ağırlık dağılımına göre)."""
        try:
            fund_count = len(funds_data)
            weights = [f.get("weight_percent", 0) for f in funds_data]

            # Fon sayısı skoru (max 50 puan)
            count_score = min(fund_count * 5, 50)

            # Ağırlık dağılım skoru (max 50 puan)
            if weights:
                weight_variance = np.var(weights)
                distribution_score = max(0, 50 - weight_variance)
            else:
                distribution_score = 0

            total_score = count_score + distribution_score
            return round(min(total_score, 100), 2)

        except Exception:
            return 0

    def _categorize_funds(self, fund_symbols: List[str]) -> Dict[str, int]:
        """Fonları kategorize et."""
        categories = {
            "Broad Market": 0,
            "Sector": 0,
            "International": 0,
            "Bond": 0,
            "Commodity": 0,
            "Growth": 0,
            "Other": 0
        }

        for symbol in fund_symbols:
            symbol_upper = symbol.upper()

            if symbol_upper in ["SPY", "QQQ", "VTI", "VOO", "IWM"]:
                categories["Broad Market"] += 1
            elif symbol_upper.startswith("XL"):
                categories["Sector"] += 1
            elif symbol_upper in ["EEM", "EFA", "VEA", "VWO", "FXI"]:
                categories["International"] += 1
            elif symbol_upper in ["TLT", "AGG", "LQD", "HYG"]:
                categories["Bond"] += 1
            elif symbol_upper in ["GLD", "SLV", "USO", "DBA", "DBC"]:
                categories["Commodity"] += 1
            elif symbol_upper in ["ARKK", "ARKQ", "ARKW", "VGT", "VUG"]:
                categories["Growth"] += 1
            else:
                categories["Other"] += 1

        return categories

    def _create_empty_chart(self, message: str) -> go.Figure:
        """Boş grafik oluştur."""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            xanchor='center', yanchor='middle',
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(
            showlegend=False,
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            margin=dict(l=50, r=50, t=50, b=50)
        )
        return fig