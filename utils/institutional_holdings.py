"""Institutional Holdings Analysis using yfinance"""
import yfinance as yf
import pandas as pd
import streamlit as st
from typing import Dict, Optional, List


class InstitutionalHoldingsAnalyzer:
    """Analyze institutional holdings for stocks"""

    def __init__(self, symbol: str):
        self.symbol = symbol
        self.ticker = yf.Ticker(symbol)

    def get_institutional_holders(self) -> Optional[pd.DataFrame]:
        """Get top institutional holders

        Returns:
            DataFrame with institutional holders or None
        """
        try:
            holders = self.ticker.institutional_holders
            if holders is not None and not holders.empty:
                return holders
            return None
        except Exception as e:
            print(f"Error fetching institutional holders: {str(e)}")
            return None

    def get_mutual_fund_holders(self) -> Optional[pd.DataFrame]:
        """Get top mutual fund holders

        Returns:
            DataFrame with mutual fund holders or None
        """
        try:
            holders = self.ticker.mutualfund_holders
            if holders is not None and not holders.empty:
                return holders
            return None
        except Exception as e:
            print(f"Error fetching mutual fund holders: {str(e)}")
            return None

    def get_major_holders(self) -> Optional[pd.DataFrame]:
        """Get major holders summary

        Returns:
            DataFrame with major holders summary or None
        """
        try:
            holders = self.ticker.major_holders
            if holders is not None and not holders.empty:
                return holders
            return None
        except Exception as e:
            print(f"Error fetching major holders: {str(e)}")
            return None

    def get_holdings_analysis(self) -> Dict:
        """Get comprehensive holdings analysis

        Returns:
            Dictionary with holdings data
        """
        try:
            institutional = self.get_institutional_holders()
            mutual_funds = self.get_mutual_fund_holders()
            major = self.get_major_holders()

            analysis = {
                'has_data': False,
                'institutional_holders': None,
                'mutual_fund_holders': None,
                'major_holders': None,
                'summary': {}
            }

            if institutional is not None and not institutional.empty:
                analysis['has_data'] = True
                analysis['institutional_holders'] = institutional

                # Calculate summary stats
                total_shares = institutional['Shares'].sum()
                avg_pct = institutional['% Out'].str.rstrip('%').astype(float).mean()

                analysis['summary']['institutional'] = {
                    'total_holders': len(institutional),
                    'total_shares': total_shares,
                    'avg_ownership_pct': avg_pct
                }

            if mutual_funds is not None and not mutual_funds.empty:
                analysis['has_data'] = True
                analysis['mutual_fund_holders'] = mutual_funds

                # Calculate summary stats
                total_shares = mutual_funds['Shares'].sum()
                avg_pct = mutual_funds['% Out'].str.rstrip('%').astype(float).mean()

                analysis['summary']['mutual_funds'] = {
                    'total_holders': len(mutual_funds),
                    'total_shares': total_shares,
                    'avg_ownership_pct': avg_pct
                }

            if major is not None and not major.empty:
                analysis['has_data'] = True
                analysis['major_holders'] = major

            return analysis

        except Exception as e:
            return {
                'has_data': False,
                'error': str(e)
            }

    def format_holdings_for_display(self, holders_df: pd.DataFrame, holder_type: str = "Institutional") -> pd.DataFrame:
        """Format holdings dataframe for display

        Args:
            holders_df: Raw holders dataframe
            holder_type: Type of holder (Institutional, Mutual Fund)

        Returns:
            Formatted dataframe
        """
        if holders_df is None or holders_df.empty:
            return pd.DataFrame()

        try:
            df = holders_df.copy()

            # Format columns
            if 'Shares' in df.columns:
                df['Shares'] = df['Shares'].apply(lambda x: f"{x:,.0f}")

            if 'Value' in df.columns:
                df['Value'] = df['Value'].apply(lambda x: f"${x:,.0f}")

            # Rename columns for clarity
            df = df.rename(columns={
                'Holder': f'{holder_type} Holder',
                '% Out': 'Ownership %',
                'Date Reported': 'Report Date'
            })

            return df

        except Exception as e:
            print(f"Error formatting holdings: {str(e)}")
            return holders_df


def display_institutional_holdings(symbol: str):
    """Display institutional holdings analysis in Streamlit

    Args:
        symbol: Stock symbol
    """
    analyzer = InstitutionalHoldingsAnalyzer(symbol)
    analysis = analyzer.get_holdings_analysis()

    if not analysis['has_data']:
        st.info("📊 Institutional holdings data not available for this stock.")
        return

    st.subheader("🏦 Institutional & Fund Holdings")

    # Major holders summary
    if analysis['major_holders'] is not None:
        st.markdown("### 📈 Ownership Summary")
        major = analysis['major_holders']

        col1, col2 = st.columns(2)
        with col1:
            for idx in range(0, len(major), 2):
                st.metric(
                    major.iloc[idx, 1],
                    major.iloc[idx, 0]
                )
        with col2:
            for idx in range(1, len(major), 2):
                st.metric(
                    major.iloc[idx, 1],
                    major.iloc[idx, 0]
                )

    # Institutional holders
    if analysis['institutional_holders'] is not None:
        st.markdown("### 🏛️ Top Institutional Holders")

        summary = analysis['summary'].get('institutional', {})
        if summary:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Institutions", f"{summary['total_holders']}")
            with col2:
                st.metric("Total Shares Held", f"{summary['total_shares']:,.0f}")
            with col3:
                st.metric("Avg Ownership", f"{summary['avg_ownership_pct']:.2f}%")

        formatted_df = analyzer.format_holdings_for_display(
            analysis['institutional_holders'],
            "Institutional"
        )
        st.dataframe(formatted_df, use_container_width=True, hide_index=True)

    # Mutual fund holders
    if analysis['mutual_fund_holders'] is not None:
        st.markdown("### 🏢 Top Mutual Fund Holders")

        summary = analysis['summary'].get('mutual_funds', {})
        if summary:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Funds", f"{summary['total_holders']}")
            with col2:
                st.metric("Total Shares Held", f"{summary['total_shares']:,.0f}")
            with col3:
                st.metric("Avg Ownership", f"{summary['avg_ownership_pct']:.2f}%")

        formatted_df = analyzer.format_holdings_for_display(
            analysis['mutual_fund_holders'],
            "Mutual Fund"
        )
        st.dataframe(formatted_df, use_container_width=True, hide_index=True)
