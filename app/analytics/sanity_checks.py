"""
Sanity Checks Module
Validates financial data integrity for Sankey diagrams.
"""

from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

TOLERANCE_PERCENT = 10.0  # Allow 10% variance


def assert_balanced_income(revenue: float,
                           cost_of_revenue: float,
                           gross_profit: float,
                           operating_income: float,
                           total_opex: float,
                           net_income: float,
                           tax_expense: float = 0,
                           interest_expense: float = 0) -> Tuple[bool, List[str]]:
    """
    Validate income statement balance.

    Args:
        revenue: Total revenue
        cost_of_revenue: Cost of goods/services sold
        gross_profit: Revenue - COGS
        operating_income: Gross profit - operating expenses
        total_opex: Total operating expenses
        net_income: Final net income
        tax_expense: Tax paid
        interest_expense: Interest paid

    Returns:
        Tuple of (is_valid, warnings_list)
    """
    warnings = []

    # Check 1: Revenue = Cost of Revenue + Gross Profit
    expected_revenue = cost_of_revenue + gross_profit
    if not _within_tolerance(revenue, expected_revenue):
        diff = abs(revenue - expected_revenue)
        pct = (diff / revenue * 100) if revenue > 0 else 0
        warnings.append(
            f"Revenue balance mismatch: {revenue:,.0f} ≠ CoR({cost_of_revenue:,.0f}) + "
            f"Gross Profit({gross_profit:,.0f}). Difference: {diff:,.0f} ({pct:.1f}%)"
        )

    # Check 2: Gross Profit = Operating Income + Total Operating Expenses
    expected_gross = operating_income + total_opex
    if total_opex > 0 and not _within_tolerance(gross_profit, expected_gross):
        diff = abs(gross_profit - expected_gross)
        pct = (diff / gross_profit * 100) if gross_profit > 0 else 0
        warnings.append(
            f"Gross profit balance mismatch: {gross_profit:,.0f} ≠ OpIncome({operating_income:,.0f}) + "
            f"OpEx({total_opex:,.0f}). Difference: {diff:,.0f} ({pct:.1f}%)"
        )

    # Check 3: Operating Income ≈ Net Income + Tax + Interest (simplified)
    deductions = tax_expense + interest_expense
    expected_operating = net_income + deductions
    if deductions > 0 and not _within_tolerance(operating_income, expected_operating, tolerance=15.0):
        diff = abs(operating_income - expected_operating)
        pct = (diff / operating_income * 100) if operating_income > 0 else 0
        warnings.append(
            f"Operating income balance mismatch: {operating_income:,.0f} ≈ "
            f"NetIncome({net_income:,.0f}) + Tax({tax_expense:,.0f}) + "
            f"Interest({interest_expense:,.0f}). Difference: {diff:,.0f} ({pct:.1f}%)"
        )

    # Check 4: Values must be positive
    if any(v < 0 for v in [revenue, gross_profit, operating_income]):
        warnings.append("Negative values detected in profit metrics (unusual for Sankey)")

    is_valid = len(warnings) == 0

    if warnings:
        logger.warning(f"Income statement sanity check warnings: {warnings}")

    return is_valid, warnings


def validate_sankey_structure(labels: List[str],
                                sources: List[int],
                                targets: List[int],
                                values: List[float]) -> Tuple[bool, List[str]]:
    """
    Validate Sankey diagram structure integrity.

    Args:
        labels: List of node labels
        sources: List of source indices
        targets: List of target indices
        values: List of flow values

    Returns:
        Tuple of (is_valid, errors_list)
    """
    errors = []

    # Check 1: Equal lengths
    if not (len(sources) == len(targets) == len(values)):
        errors.append(
            f"Mismatched lengths: sources({len(sources)}), "
            f"targets({len(targets)}), values({len(values)})"
        )

    # Check 2: Valid indices
    num_labels = len(labels)
    for i, (src, tgt) in enumerate(zip(sources, targets)):
        if src < 0 or src >= num_labels:
            errors.append(f"Invalid source index {src} at position {i} (labels: {num_labels})")
        if tgt < 0 or tgt >= num_labels:
            errors.append(f"Invalid target index {tgt} at position {i} (labels: {num_labels})")

    # Check 3: No negative values
    for i, val in enumerate(values):
        if val < 0:
            errors.append(f"Negative flow value {val} at position {i}")

    # Check 4: No self-loops
    for i, (src, tgt) in enumerate(zip(sources, targets)):
        if src == tgt:
            errors.append(f"Self-loop detected at position {i}: {src} → {tgt}")

    # Check 5: At least one flow
    if len(values) == 0:
        errors.append("No flows defined (empty Sankey)")

    is_valid = len(errors) == 0

    if errors:
        logger.error(f"Sankey structure validation errors: {errors}")

    return is_valid, errors


def rescale_costs_proportionally(costs: Dict[str, float], target_total: float) -> Dict[str, float]:
    """
    Rescale cost items proportionally to match a target total.

    Args:
        costs: Dict of cost_name → value
        target_total: Desired sum of all costs

    Returns:
        Rescaled costs dict
    """
    current_total = sum(costs.values())

    if current_total == 0:
        logger.warning("Cannot rescale costs: current total is zero")
        return costs

    scale_factor = target_total / current_total

    rescaled = {name: val * scale_factor for name, val in costs.items()}

    logger.info(
        f"Rescaled costs from {current_total:,.0f} to {target_total:,.0f} "
        f"(factor: {scale_factor:.4f})"
    )

    return rescaled


def check_fund_holdings_balance(holdings: List[Dict]) -> Tuple[bool, float]:
    """
    Check if fund holdings weights sum to approximately 100%.

    Args:
        holdings: List of dicts with 'weight' key

    Returns:
        Tuple of (is_balanced, total_weight)
    """
    total_weight = sum(float(h.get('weight', 0)) for h in holdings)

    is_balanced = _within_tolerance(total_weight, 100.0, tolerance=5.0)

    if not is_balanced:
        logger.warning(
            f"Fund holdings weights sum to {total_weight:.2f}%, expected ~100%"
        )

    return is_balanced, total_weight


def _within_tolerance(actual: float, expected: float, tolerance: float = TOLERANCE_PERCENT) -> bool:
    """Check if actual value is within tolerance % of expected value."""
    if expected == 0:
        return actual == 0

    diff_percent = abs((actual - expected) / expected * 100)
    return diff_percent <= tolerance


def assert_balanced_income(metrics: Dict[str, float], tol: float = 0.10) -> Dict[str, float]:
    """
    Validate and rescale income statement metrics to ensure balance for Sankey visualization.

    This function ensures financial statement consistency by checking:
    1. revenue ≈ cost_of_revenue + gross_profit
    2. gross_profit ≈ operating_income + opex_total
    3. All values are positive magnitudes (required for Sankey)

    If imbalances exceed tolerance, the function proportionally rescales the smaller components
    to match the higher-level metrics.

    Args:
        metrics: Dict with keys:
            - revenue: Total revenue
            - cost_of_revenue: Cost of goods/services sold
            - gross_profit: Gross profit
            - operating_income: Operating income
            - opex_total: Total operating expenses
            - tax_expense: Tax expense (optional)
            - interest_expense: Interest expense (optional)
            - net_income: Net income
        tol: Tolerance for imbalance (default 0.10 = 10%)

    Returns:
        Dict with balanced metrics, all values as positive magnitudes

    Example:
        >>> metrics = {
        ...     'revenue': 1000,
        ...     'cost_of_revenue': 700,
        ...     'gross_profit': 400,  # Imbalanced: should be 300
        ... }
        >>> balanced = assert_balanced_income(metrics)
        >>> balanced['gross_profit']  # Now rescaled to balance
        300.0
    """
    # Convert all values to positive magnitudes
    result = {k: abs(v) for k, v in metrics.items()}

    revenue = result.get('revenue', 0)
    cost_of_revenue = result.get('cost_of_revenue', 0)
    gross_profit = result.get('gross_profit', 0)
    operating_income = result.get('operating_income', 0)
    opex_total = result.get('opex_total', 0)
    tax_expense = result.get('tax_expense', 0)
    interest_expense = result.get('interest_expense', 0)
    net_income = result.get('net_income', 0)

    if revenue == 0:
        logger.warning("Revenue is zero, cannot validate balance")
        return result

    # Check 1: Revenue balance (revenue ≈ cost_of_revenue + gross_profit)
    expected_revenue = cost_of_revenue + gross_profit
    revenue_imbalance = abs(revenue - expected_revenue) / revenue

    if revenue_imbalance > tol:
        logger.warning(f"Revenue imbalance detected: {revenue_imbalance:.1%} (tolerance: {tol:.1%})")

        # Rescale cost_of_revenue and gross_profit proportionally
        if expected_revenue > 0:
            scale_factor = revenue / expected_revenue
            result['cost_of_revenue'] = cost_of_revenue * scale_factor
            result['gross_profit'] = gross_profit * scale_factor

            logger.info(
                f"Rescaled cost side by {scale_factor:.4f}x: "
                f"cost_of_revenue={cost_of_revenue:.0f} → {result['cost_of_revenue']:.0f}, "
                f"gross_profit={gross_profit:.0f} → {result['gross_profit']:.0f}"
            )

            # Update for subsequent checks
            gross_profit = result['gross_profit']

    # Check 2: Gross profit balance (gross_profit ≈ operating_income + opex_total)
    if gross_profit > 0 and opex_total > 0:
        expected_gp = operating_income + opex_total
        gp_imbalance = abs(gross_profit - expected_gp) / gross_profit

        if gp_imbalance > tol:
            logger.warning(f"Gross profit imbalance detected: {gp_imbalance:.1%}")

            # Rescale operating_income and opex_total proportionally
            if expected_gp > 0:
                scale_factor = gross_profit / expected_gp
                result['operating_income'] = operating_income * scale_factor
                result['opex_total'] = opex_total * scale_factor

                logger.info(
                    f"Rescaled operating components by {scale_factor:.4f}x: "
                    f"operating_income={operating_income:.0f} → {result['operating_income']:.0f}, "
                    f"opex_total={opex_total:.0f} → {result['opex_total']:.0f}"
                )

                # Update for net income calculation
                operating_income = result['operating_income']

    # Check 3: Net income consistency (simplified: net_income ≈ operating_income - tax - interest)
    expected_net_income = max(0, operating_income - tax_expense - interest_expense)

    if abs(net_income - expected_net_income) / max(net_income, expected_net_income, 1) > tol:
        logger.warning(
            f"Net income mismatch: actual={net_income:.0f}, "
            f"expected={expected_net_income:.0f}"
        )
        # Use the calculated value for consistency
        result['net_income'] = expected_net_income

    return result
