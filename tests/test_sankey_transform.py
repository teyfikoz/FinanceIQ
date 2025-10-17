"""
Unit tests for sankey_transform module.
"""

import pytest
import pandas as pd
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.analytics.sankey_transform import (
    income_to_sankey,
    fund_to_sankey,
    stock_to_funds_sankey,
    macro_to_sankey
)


class TestIncomeSankey:
    """Test income statement to Sankey transformation."""

    def test_basic_income_sankey(self):
        """Test basic income statement transformation."""
        df = pd.DataFrame([{
            'revenue': 100000,
            'cost_of_revenue': 60000,
            'gross_profit': 40000,
            'operating_income': 25000,
            'rd_expense': 5000,
            'sga_expense': 8000,
            'other_operating_expense': 2000,
            'tax_expense': 4000,
            'interest_expense': 1000,
            'net_income': 20000,
            'period_end': '2022-12-31'
        }])

        result = income_to_sankey(df, fiscal_index=0)

        assert 'labels' in result
        assert 'sources' in result
        assert 'targets' in result
        assert 'values' in result
        assert 'colors' in result
        assert 'meta' in result

        # Check structure integrity
        assert len(result['sources']) == len(result['targets']) == len(result['values'])

        # Check Revenue is first label
        assert result['labels'][0] == 'Revenue'

        # Check meta calculations
        meta = result['meta']
        assert meta['revenue'] == 100000
        assert 35 < meta['gross_margin'] < 45  # ~40%
        assert 20 < meta['op_margin'] < 30  # ~25%
        assert 15 < meta['net_margin'] < 25  # ~20%

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        df = pd.DataFrame()

        result = income_to_sankey(df)

        assert result['labels'] == ['No Data']
        assert 'error' in result['meta']

    def test_margins_calculation(self):
        """Test margin calculations."""
        df = pd.DataFrame([{
            'revenue': 1000000,
            'cost_of_revenue': 600000,
            'gross_profit': 400000,
            'operating_income': 250000,
            'rd_expense': 50000,
            'sga_expense': 80000,
            'other_operating_expense': 20000,
            'tax_expense': 40000,
            'interest_expense': 10000,
            'net_income': 200000,
            'period_end': '2022-12-31'
        }])

        result = income_to_sankey(df)
        meta = result['meta']

        assert meta['gross_margin'] == pytest.approx(40.0, abs=0.1)
        assert meta['op_margin'] == pytest.approx(25.0, abs=0.1)
        assert meta['net_margin'] == pytest.approx(20.0, abs=0.1)

    def test_no_negative_values(self):
        """Ensure no negative values in Sankey output."""
        df = pd.DataFrame([{
            'revenue': 100000,
            'cost_of_revenue': 60000,
            'gross_profit': 40000,
            'operating_income': 25000,
            'rd_expense': 5000,
            'sga_expense': 8000,
            'other_operating_expense': 2000,
            'tax_expense': 4000,
            'interest_expense': 1000,
            'net_income': 20000,
            'period_end': '2022-12-31'
        }])

        result = income_to_sankey(df)

        # All values must be non-negative
        assert all(v >= 0 for v in result['values'])


class TestFundSankey:
    """Test fund holdings to Sankey transformation."""

    def test_basic_fund_sankey(self):
        """Test basic fund holdings transformation."""
        holdings = [
            {'symbol': 'AAPL', 'weight': 10.0, 'name': 'Apple Inc.'},
            {'symbol': 'MSFT', 'weight': 8.0, 'name': 'Microsoft'},
            {'symbol': 'GOOGL', 'weight': 5.0, 'name': 'Alphabet'}
        ]

        result = fund_to_sankey('SPY', holdings)

        assert 'labels' in result
        assert 'sources' in result
        assert 'targets' in result
        assert 'values' in result
        assert 'meta' in result

        # First label should be fund name
        assert result['labels'][0] == 'SPY'

        # Should have 3 holdings
        assert len(result['values']) == 3

        # Total weight
        assert result['meta']['total_weight'] == 23.0

    def test_empty_holdings(self):
        """Test empty holdings list."""
        result = fund_to_sankey('TEST', [])

        assert result['labels'] == ['No Data']
        assert 'error' in result['meta']

    def test_holdings_sorted_by_weight(self):
        """Test that holdings are sorted by weight."""
        holdings = [
            {'symbol': 'AAPL', 'weight': 5.0},
            {'symbol': 'MSFT', 'weight': 10.0},
            {'symbol': 'GOOGL', 'weight': 7.5}
        ]

        result = fund_to_sankey('TEST', holdings)

        # Values should be sorted descending
        values = result['values']
        assert values == sorted(values, reverse=True)


class TestStockToFundsSankey:
    """Test stock to funds Sankey transformation."""

    def test_basic_stock_ownership(self):
        """Test basic stock ownership transformation."""
        funds_data = [
            {'fund_symbol': 'SPY', 'weight': 8.0},
            {'fund_symbol': 'QQQ', 'weight': 10.0},
            {'fund_symbol': 'VOO', 'weight': 7.5}
        ]

        result = stock_to_funds_sankey('AAPL', funds_data)

        assert 'labels' in result
        assert result['labels'][0] == 'AAPL'
        assert len(result['values']) == 3

        meta = result['meta']
        assert meta['number_of_funds'] == 3
        assert meta['max_weight'] == 10.0

    def test_empty_funds_data(self):
        """Test empty funds data."""
        result = stock_to_funds_sankey('AAPL', [])

        assert 'error' in result['meta']


class TestMacroSankey:
    """Test macro liquidity Sankey transformation."""

    def test_basic_macro_flow(self):
        """Test basic macro liquidity flow."""
        liquidity_sources = {
            'M2': 1000,
            'CB_Balance': 500,
            'GLI': 300
        }

        asset_allocations = {
            'Equities': 800,
            'BTC': 600,
            'Gold': 400
        }

        result = macro_to_sankey(liquidity_sources, asset_allocations)

        assert 'labels' in result
        assert 'sources' in result
        assert 'targets' in result
        assert 'values' in result

        # Should have 3 sources + 3 assets = 6 labels
        assert len(result['labels']) == 6

        # Should have 3 x 3 = 9 flows
        assert len(result['values']) == 9

    def test_empty_sources(self):
        """Test empty liquidity sources."""
        result = macro_to_sankey({}, {'Equities': 100})

        assert 'error' in result['meta']

    def test_empty_assets(self):
        """Test empty asset allocations."""
        result = macro_to_sankey({'M2': 100}, {})

        assert 'error' in result['meta']

    def test_normalized_flows(self):
        """Test that flows are normalized."""
        liquidity_sources = {'M2': 100}
        asset_allocations = {'Equities': 50, 'BTC': 50}

        result = macro_to_sankey(liquidity_sources, asset_allocations)

        # Values should sum to approximately 100 (normalized)
        total_flow = sum(result['values'])
        assert 90 < total_flow < 110  # Allow small tolerance


class TestSankeyStructureValidation:
    """Test Sankey structure validity."""

    def test_valid_indices(self):
        """Test that all indices are valid."""
        df = pd.DataFrame([{
            'revenue': 100000,
            'cost_of_revenue': 60000,
            'gross_profit': 40000,
            'operating_income': 25000,
            'rd_expense': 5000,
            'sga_expense': 8000,
            'other_operating_expense': 2000,
            'tax_expense': 4000,
            'interest_expense': 1000,
            'net_income': 20000,
            'period_end': '2022-12-31'
        }])

        result = income_to_sankey(df)

        num_labels = len(result['labels'])

        # All source and target indices must be valid
        for src, tgt in zip(result['sources'], result['targets']):
            assert 0 <= src < num_labels
            assert 0 <= tgt < num_labels

    def test_no_self_loops(self):
        """Test that there are no self-loops."""
        df = pd.DataFrame([{
            'revenue': 100000,
            'cost_of_revenue': 60000,
            'gross_profit': 40000,
            'operating_income': 25000,
            'rd_expense': 5000,
            'sga_expense': 8000,
            'other_operating_expense': 2000,
            'tax_expense': 4000,
            'interest_expense': 1000,
            'net_income': 20000,
            'period_end': '2022-12-31'
        }])

        result = income_to_sankey(df)

        # No source should equal target
        for src, tgt in zip(result['sources'], result['targets']):
            assert src != tgt


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
