"""
Export utilities for Global Liquidity Dashboard
PDF reports, Excel exports, and data downloads
"""

import pandas as pd
import io
from datetime import datetime
from typing import Dict, List, Optional
import plotly.graph_objects as go
import plotly.io as pio

class ExportManager:
    """Manages data export functionality"""

    def __init__(self):
        """Initialize export manager"""
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    def export_portfolio_to_excel(self, portfolio_data: Dict, portfolio_name: str, transactions: list = None) -> bytes:
        """Export portfolio data to Excel file with transactions"""
        output = io.BytesIO()

        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Summary sheet
            summary_data = {
                'Metric': [
                    'Total Value',
                    'Total Cost',
                    'Total P&L',
                    'Total P&L %',
                    'Last Updated'
                ],
                'Value': [
                    f"${portfolio_data['total_value']:,.2f}",
                    f"${portfolio_data['total_cost']:,.2f}",
                    f"${portfolio_data['total_pnl']:,.2f}",
                    f"{portfolio_data['total_pnl_pct']:.2f}%",
                    portfolio_data['last_updated']
                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)

            # Holdings sheet
            if portfolio_data['holdings']:
                holdings_df = pd.DataFrame(portfolio_data['holdings'])
                holdings_df.to_excel(writer, sheet_name='Holdings', index=False)

                # Format the holdings sheet
                workbook = writer.book
                worksheet = writer.sheets['Holdings']

                # Add currency format
                money_fmt = workbook.add_format({'num_format': '$#,##0.00'})
                percent_fmt = workbook.add_format({'num_format': '0.00%'})

                # Apply formatting
                worksheet.set_column('D:H', 15, money_fmt)

            # Transactions sheet
            if transactions:
                trans_df = pd.DataFrame(transactions)
                if not trans_df.empty:
                    # Reorder columns for better readability
                    column_order = ['date', 'symbol', 'transaction_type', 'quantity', 'price', 'notes']
                    trans_df = trans_df[[col for col in column_order if col in trans_df.columns]]
                    trans_df.to_excel(writer, sheet_name='Transactions', index=False)

                    # Format transactions sheet
                    worksheet = writer.sheets['Transactions']
                    money_fmt = workbook.add_format({'num_format': '$#,##0.00'})
                    worksheet.set_column('E:E', 15, money_fmt)  # Price column

        output.seek(0)
        return output.getvalue()

    def export_market_data_to_excel(self, market_data: Dict) -> bytes:
        """Export market data to Excel"""
        output = io.BytesIO()

        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            for market_name, data in market_data.items():
                if isinstance(data, pd.DataFrame):
                    data.to_excel(writer, sheet_name=market_name[:31])  # Excel limit
                elif isinstance(data, dict):
                    pd.DataFrame([data]).to_excel(writer, sheet_name=market_name[:31])

        output.seek(0)
        return output.getvalue()

    def export_watchlist_to_csv(self, watchlist_data: List[Dict]) -> bytes:
        """Export watchlist to CSV"""
        df = pd.DataFrame(watchlist_data)
        output = io.BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return output.getvalue()

    def create_portfolio_report_html(self, portfolio_data: Dict,
                                     performance_data: Dict,
                                     metrics: Dict,
                                     portfolio_name: str) -> str:
        """Create HTML portfolio report"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Portfolio Report - {portfolio_name}</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Arial, sans-serif;
                    margin: 40px;
                    background: #f5f5f5;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px;
                    margin-bottom: 30px;
                }}
                .section {{
                    background: white;
                    padding: 25px;
                    margin-bottom: 20px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 15px;
                }}
                th, td {{
                    padding: 12px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }}
                th {{
                    background: #f8f9fa;
                    font-weight: 600;
                }}
                .positive {{ color: #28a745; }}
                .negative {{ color: #dc3545; }}
                .metric-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin-top: 20px;
                }}
                .metric-card {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    text-align: center;
                }}
                .metric-value {{
                    font-size: 24px;
                    font-weight: bold;
                    margin-top: 10px;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 40px;
                    color: #6c757d;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 Portfolio Report: {portfolio_name}</h1>
                <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            </div>

            <div class="section">
                <h2>Portfolio Summary</h2>
                <div class="metric-grid">
                    <div class="metric-card">
                        <div>Total Value</div>
                        <div class="metric-value">${portfolio_data['total_value']:,.2f}</div>
                    </div>
                    <div class="metric-card">
                        <div>Total Cost</div>
                        <div class="metric-value">${portfolio_data['total_cost']:,.2f}</div>
                    </div>
                    <div class="metric-card">
                        <div>Total P&L</div>
                        <div class="metric-value {'positive' if portfolio_data['total_pnl'] >= 0 else 'negative'}">
                            ${portfolio_data['total_pnl']:,.2f}
                        </div>
                    </div>
                    <div class="metric-card">
                        <div>Return %</div>
                        <div class="metric-value {'positive' if portfolio_data['total_pnl_pct'] >= 0 else 'negative'}">
                            {portfolio_data['total_pnl_pct']:.2f}%
                        </div>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>Holdings</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Symbol</th>
                            <th>Quantity</th>
                            <th>Purchase Price</th>
                            <th>Current Price</th>
                            <th>Cost Basis</th>
                            <th>Current Value</th>
                            <th>P&L</th>
                            <th>P&L %</th>
                        </tr>
                    </thead>
                    <tbody>
        """

        for holding in portfolio_data['holdings']:
            pnl_class = 'positive' if holding['pnl'] >= 0 else 'negative'
            html += f"""
                        <tr>
                            <td><strong>{holding['symbol']}</strong></td>
                            <td>{holding['quantity']}</td>
                            <td>${holding['purchase_price']:,.2f}</td>
                            <td>${holding['current_price']:,.2f}</td>
                            <td>${holding['cost_basis']:,.2f}</td>
                            <td>${holding['current_value']:,.2f}</td>
                            <td class="{pnl_class}">${holding['pnl']:,.2f}</td>
                            <td class="{pnl_class}">{holding['pnl_pct']:.2f}%</td>
                        </tr>
            """

        html += """
                    </tbody>
                </table>
            </div>
        """

        if metrics:
            html += f"""
            <div class="section">
                <h2>Performance Metrics</h2>
                <div class="metric-grid">
                    <div class="metric-card">
                        <div>Sharpe Ratio</div>
                        <div class="metric-value">{metrics.get('sharpe_ratio', 0):.2f}</div>
                    </div>
                    <div class="metric-card">
                        <div>Volatility</div>
                        <div class="metric-value">{metrics.get('volatility', 0):.2f}%</div>
                    </div>
                    <div class="metric-card">
                        <div>Max Drawdown</div>
                        <div class="metric-value negative">{metrics.get('max_drawdown', 0):.2f}%</div>
                    </div>
                    <div class="metric-card">
                        <div>Avg Daily Return</div>
                        <div class="metric-value">{metrics.get('avg_daily_return', 0):.2f}%</div>
                    </div>
                </div>
            </div>
            """

        html += """
            <div class="footer">
                <p>Global Liquidity Dashboard - Professional Financial Platform</p>
                <p>This report is for informational purposes only. Not financial advice.</p>
            </div>
        </body>
        </html>
        """

        return html

    def export_chart_to_image(self, fig: go.Figure, format: str = 'png') -> bytes:
        """Export plotly chart to image"""
        img_bytes = pio.to_image(fig, format=format, width=1200, height=600)
        return img_bytes

    def create_market_summary_csv(self, market_data: Dict) -> bytes:
        """Create CSV summary of market data"""
        rows = []
        for symbol, data in market_data.items():
            if isinstance(data, dict):
                rows.append({
                    'Symbol': symbol,
                    'Price': data.get('price', 0),
                    'Change %': data.get('change', 0),
                    'Volume': data.get('volume', 0),
                    'Status': data.get('status', 'Unknown')
                })

        df = pd.DataFrame(rows)
        output = io.BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return output.getvalue()

    def get_filename(self, prefix: str, extension: str) -> str:
        """Generate filename with timestamp"""
        return f"{prefix}_{self.timestamp}.{extension}"

# Global export manager instance
_export_manager = None

def get_export_manager() -> ExportManager:
    """Get global export manager instance"""
    global _export_manager
    if _export_manager is None:
        _export_manager = ExportManager()
    return _export_manager
