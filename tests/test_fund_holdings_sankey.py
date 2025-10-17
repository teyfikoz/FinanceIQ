"""
Unit tests for fund holdings Sankey transformations.
"""

import pytest
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.analytics.sankey_transform import fund_to_sankey, stock_to_funds_sankey
from app.analytics.sanity_checks import check_fund_holdings_balance


class TestFundHoldingsBalance:
    """Test fund holdings balance validation."""

    def test_balanced_holdings(self):
        """Test holdings that sum to ~100%."""
        holdings = [
            {'symbol': 'AAPL', 'weight': 10.0},
            {'symbol': 'MSFT', 'weight': 8.0},
            {'symbol': 'GOOGL', 'weight': 7.5},
            {'symbol': 'AMZN', 'weight': 6.5},
            {'symbol': 'Other', 'weight': 68.0}
        ]

        is_balanced, total = check_fund_holdings_balance(holdings)

        assert is_balanced is True
        assert total == 100.0

    def test_imbalanced_holdings(self):
        """Test holdings that don't sum to 100%."""
        holdings = [
            {'symbol': 'AAPL', 'weight': 10.0},
            {'symbol': 'MSFT', 'weight': 8.0}
        ]

        is_balanced, total = check_fund_holdings_balance(holdings)

        assert is_balanced is False
        assert total == 18.0

    def test_slight_imbalance_within_tolerance(self):
        """Test slight imbalance within tolerance."""
        holdings = [
            {'symbol': 'AAPL', 'weight': 10.0},
            {'symbol': 'Other', 'weight': 93.0}
        ]

        is_balanced, total = check_fund_holdings_balance(holdings)

        # 103% is within 5% tolerance
        assert is_balanced is True
        assert total == 103.0

    def test_empty_holdings(self):
        """Test empty holdings list."""
        is_balanced, total = check_fund_holdings_balance([])

        assert total == 0.0


class TestFundSankeyIntegration:
    """Integration tests for fund Sankey transformations."""

    def test_spy_simulated_holdings(self):
        """Test SPY simulated holdings transformation."""
        # Simulated SPY holdings
        holdings = [
            {'symbol': 'AAPL', 'weight': 7.1, 'name': 'Apple Inc.'},
            {'symbol': 'MSFT', 'weight': 6.8, 'name': 'Microsoft'},
            {'symbol': 'AMZN', 'weight': 3.5, 'name': 'Amazon'},
            {'symbol': 'NVDA', 'weight': 3.2, 'name': 'NVIDIA'},
            {'symbol': 'GOOGL', 'weight': 2.1, 'name': 'Alphabet'},
        ]

        result = fund_to_sankey('SPY', holdings)

        # Validate structure
        assert len(result['labels']) == 6  # SPY + 5 stocks
        assert len(result['values']) == 5  # 5 flows

        # Validate meta
        meta = result['meta']
        assert meta['fund_name'] == 'SPY'
        assert meta['holdings_count'] == 5
        assert meta['total_weight'] == pytest.approx(22.7, abs=0.1)

        # Top 3 concentration
        assert meta['top3_concentration'] == pytest.approx(17.4, abs=0.1)

    def test_stock_ownership_multiple_funds(self):
        """Test stock owned by multiple funds."""
        funds_data = [
            {'fund_symbol': 'SPY', 'weight': 7.1},
            {'fund_symbol': 'QQQ', 'weight': 8.5},
            {'fund_symbol': 'VOO', 'weight': 7.0},
            {'fund_symbol': 'VT', 'weight': 4.2}
        ]

        result = stock_to_funds_sankey('AAPL', funds_data)

        # Validate structure
        assert len(result['labels']) == 5  # AAPL + 4 funds
        assert len(result['values']) == 4  # 4 flows

        # Validate meta
        meta = result['meta']
        assert meta['stock_symbol'] == 'AAPL'
        assert meta['number_of_funds'] == 4
        assert meta['max_weight'] == 8.5
        assert meta['avg_weight'] == pytest.approx(6.7, abs=0.1)

    def test_fund_sankey_with_zero_weights(self):
        """Test fund Sankey filters out zero weights."""
        holdings = [
            {'symbol': 'AAPL', 'weight': 10.0},
            {'symbol': 'MSFT', 'weight': 0.0},  # Should be filtered
            {'symbol': 'GOOGL', 'weight': 8.0}
        ]

        result = fund_to_sankey('TEST', holdings)

        # Should only have 2 flows (MSFT filtered out)
        assert len(result['values']) == 2
        assert sum(result['values']) == 18.0

    def test_stock_sankey_sorting(self):
        """Test that stock ownership is sorted by weight."""
        funds_data = [
            {'fund_symbol': 'SPY', 'weight': 5.0},
            {'fund_symbol': 'QQQ', 'weight': 10.0},
            {'fund_symbol': 'VOO', 'weight': 7.5}
        ]

        result = stock_to_funds_sankey('TEST', funds_data)

        # Values should be in descending order
        values = result['values']
        assert values == sorted(values, reverse=True)
        assert values[0] == 10.0
        assert values[1] == 7.5
        assert values[2] == 5.0


class TestSankeyColors:
    """Test Sankey color assignments."""

    def test_fund_colors(self):
        """Test fund Sankey has proper color scheme."""
        holdings = [
            {'symbol': 'AAPL', 'weight': 10.0},
            {'symbol': 'MSFT', 'weight': 8.0}
        ]

        result = fund_to_sankey('SPY', holdings)

        assert 'colors' in result
        assert len(result['colors']) == 3  # Fund + 2 stocks

        # First color (fund) should be blue
        assert result['colors'][0] == "#2563EB"

        # Stock colors should be green
        assert result['colors'][1] == "#22C55E"
        assert result['colors'][2] == "#22C55E"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_single_holding(self):
        """Test fund with single holding."""
        holdings = [{'symbol': 'AAPL', 'weight': 100.0}]

        result = fund_to_sankey('TEST', holdings)

        assert len(result['labels']) == 2
        assert len(result['values']) == 1
        assert result['values'][0] == 100.0

    def test_large_number_of_holdings(self):
        """Test fund with many holdings."""
        holdings = [
            {'symbol': f'STOCK{i}', 'weight': 1.0}
            for i in range(100)
        ]

        result = fund_to_sankey('TEST', holdings)

        assert len(result['labels']) == 101  # Fund + 100 stocks
        assert len(result['values']) == 100
        assert sum(result['values']) == 100.0

    def test_very_small_weights(self):
        """Test handling of very small weights."""
        holdings = [
            {'symbol': 'AAPL', 'weight': 0.001},
            {'symbol': 'MSFT', 'weight': 0.002}
        ]

        result = fund_to_sankey('TEST', holdings)

        # Small weights should still be included (not zero)
        assert len(result['values']) == 2
        assert all(v > 0 for v in result['values'])

    def test_missing_weight_field(self):
        """Test handling of missing weight field."""
        holdings = [
            {'symbol': 'AAPL'},  # No weight field
            {'symbol': 'MSFT', 'weight': 10.0}
        ]

        result = fund_to_sankey('TEST', holdings)

        # Missing weight should default to 0 and be filtered
        assert len(result['values']) == 1
        assert result['values'][0] == 10.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
