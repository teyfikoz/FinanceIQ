"""
Test income statement sanity checks and balance validation.
"""

import pytest
from app.analytics.sanity_checks import assert_balanced_income, rescale_costs_proportionally


def test_balanced_income_no_changes_needed():
    """Test that balanced income statement requires no changes."""
    metrics = {
        'revenue': 1000.0,
        'cost_of_revenue': 600.0,
        'gross_profit': 400.0,
        'operating_income': 250.0,
        'opex_total': 150.0,
        'tax_expense': 50.0,
        'interest_expense': 20.0,
        'net_income': 180.0
    }

    result = assert_balanced_income(metrics, tol=0.10)

    # Values should remain roughly the same (within tolerance)
    assert abs(result['revenue'] - 1000.0) < 10.0
    assert abs(result['cost_of_revenue'] - 600.0) < 10.0
    assert abs(result['gross_profit'] - 400.0) < 10.0


def test_revenue_imbalance_rescaling():
    """Test that revenue imbalance triggers rescaling."""
    metrics = {
        'revenue': 1000.0,
        'cost_of_revenue': 700.0,
        'gross_profit': 400.0,  # Should be 300 to balance
        'operating_income': 250.0,
        'opex_total': 150.0,
        'tax_expense': 0.0,
        'interest_expense': 0.0,
        'net_income': 250.0
    }

    result = assert_balanced_income(metrics, tol=0.05)  # Use 5% tolerance to trigger rescaling

    # Check that cost_of_revenue + gross_profit ≈ revenue
    assert abs(result['cost_of_revenue'] + result['gross_profit'] - result['revenue']) < 1.0

    # Proportional rescaling: scale_factor = 1000 / (700 + 400) ≈ 0.909
    # cost_of_revenue should be ~636, gross_profit should be ~364
    assert abs(result['cost_of_revenue'] - 636.4) < 10.0
    assert abs(result['gross_profit'] - 363.6) < 10.0


def test_gross_profit_imbalance_rescaling():
    """Test that gross profit imbalance triggers rescaling."""
    metrics = {
        'revenue': 1000.0,
        'cost_of_revenue': 600.0,
        'gross_profit': 400.0,
        'operating_income': 150.0,
        'opex_total': 300.0,  # Should be 250 to balance (400 - 150)
        'tax_expense': 30.0,
        'interest_expense': 20.0,
        'net_income': 100.0
    }

    result = assert_balanced_income(metrics, tol=0.10)

    # Check that operating_income + opex_total ≈ gross_profit
    gp_balance = abs(result['operating_income'] + result['opex_total'] - result['gross_profit'])
    assert gp_balance < 1.0

    # Scale factor = 400 / (150 + 300) ≈ 0.889
    # operating_income should be ~133, opex_total should be ~267
    assert abs(result['operating_income'] - 133.3) < 10.0
    assert abs(result['opex_total'] - 266.7) < 10.0


def test_negative_values_converted_to_positive():
    """Test that negative values are converted to positive magnitudes."""
    metrics = {
        'revenue': 1000.0,
        'cost_of_revenue': -600.0,  # Negative
        'gross_profit': 400.0,
        'operating_income': -250.0,  # Negative
        'opex_total': 150.0,
        'tax_expense': 0.0,
        'interest_expense': 0.0,
        'net_income': 100.0
    }

    result = assert_balanced_income(metrics, tol=0.10)

    # All values should be positive
    assert all(v >= 0 for v in result.values())

    # Check specific conversions
    assert result['cost_of_revenue'] > 0
    assert result['operating_income'] > 0


def test_zero_revenue():
    """Test handling of zero revenue."""
    metrics = {
        'revenue': 0.0,
        'cost_of_revenue': 100.0,
        'gross_profit': 0.0,
        'operating_income': 0.0,
        'opex_total': 0.0,
        'tax_expense': 0.0,
        'interest_expense': 0.0,
        'net_income': 0.0
    }

    result = assert_balanced_income(metrics, tol=0.10)

    # Should return as-is without crashing
    assert result['revenue'] == 0.0


def test_net_income_consistency():
    """Test net income consistency check."""
    metrics = {
        'revenue': 1000.0,
        'cost_of_revenue': 600.0,
        'gross_profit': 400.0,
        'operating_income': 250.0,
        'opex_total': 150.0,
        'tax_expense': 50.0,
        'interest_expense': 20.0,
        'net_income': 250.0  # Should be ~180 (250 - 50 - 20)
    }

    result = assert_balanced_income(metrics, tol=0.10)

    # Net income should be adjusted to match operating_income - tax - interest
    expected_net = result['operating_income'] - result['tax_expense'] - result['interest_expense']
    assert abs(result['net_income'] - expected_net) < 1.0


def test_small_imbalance_within_tolerance():
    """Test that small imbalances within tolerance are not rescaled."""
    metrics = {
        'revenue': 1000.0,
        'cost_of_revenue': 600.0,
        'gross_profit': 398.0,  # 0.2% imbalance (within 10% tolerance)
        'operating_income': 250.0,
        'opex_total': 148.0,
        'tax_expense': 0.0,
        'interest_expense': 0.0,
        'net_income': 250.0
    }

    result = assert_balanced_income(metrics, tol=0.10)

    # Should not rescale since within tolerance - values stay same
    assert abs(result['cost_of_revenue'] - 600.0) < 1.0
    assert abs(result['gross_profit'] - 398.0) < 1.0


def test_rescale_costs_proportionally():
    """Test proportional cost rescaling utility function."""
    costs = {
        'R&D': 100.0,
        'Marketing': 80.0,
        'Operations': 120.0
    }  # Total: 300

    target_total = 450.0

    rescaled = rescale_costs_proportionally(costs, target_total)

    # Check new total
    new_total = sum(rescaled.values())
    assert abs(new_total - 450.0) < 0.1

    # Check proportions maintained
    # R&D should be: 100 * (450/300) = 150
    assert abs(rescaled['R&D'] - 150.0) < 0.1
    assert abs(rescaled['Marketing'] - 120.0) < 0.1
    assert abs(rescaled['Operations'] - 180.0) < 0.1


def test_rescale_costs_zero_total():
    """Test rescaling when current total is zero."""
    costs = {
        'R&D': 0.0,
        'Marketing': 0.0,
        'Operations': 0.0
    }

    target_total = 100.0

    rescaled = rescale_costs_proportionally(costs, target_total)

    # Should return original (cannot rescale from zero)
    assert rescaled == costs


def test_large_imbalance():
    """Test handling of very large imbalances."""
    metrics = {
        'revenue': 1000.0,
        'cost_of_revenue': 1500.0,  # Exceeds revenue!
        'gross_profit': 500.0,
        'operating_income': 100.0,
        'opex_total': 400.0,
        'tax_expense': 0.0,
        'interest_expense': 0.0,
        'net_income': 100.0
    }

    result = assert_balanced_income(metrics, tol=0.10)

    # Should still enforce balance despite large imbalance
    assert abs(result['cost_of_revenue'] + result['gross_profit'] - result['revenue']) < 1.0

    # All values should be positive
    assert all(v >= 0 for v in result.values())


def test_real_world_apple_fy22():
    """Test with realistic Apple FY2022 data."""
    metrics = {
        'revenue': 394328000000,
        'cost_of_revenue': 223546000000,
        'gross_profit': 170782000000,
        'operating_income': 119437000000,
        'opex_total': 51345000000,
        'tax_expense': 19300000000,
        'interest_expense': 2931000000,
        'net_income': 99803000000
    }

    result = assert_balanced_income(metrics, tol=0.10)

    # Should maintain approximate values (within 10% tolerance)
    assert abs(result['revenue'] - 394328000000) / 394328000000 < 0.10
    assert abs(result['net_income'] - 99803000000) / 99803000000 < 0.15

    # Check balance
    revenue_balance = abs(
        result['cost_of_revenue'] + result['gross_profit'] - result['revenue']
    )
    assert revenue_balance / result['revenue'] < 0.01  # Within 1%
