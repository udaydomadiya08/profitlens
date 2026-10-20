"""
Unit tests for financial calculations and metric edge cases.
Uses hand-calculated synthetic fixtures with known mathematical results.
"""

import pytest
import pandas as pd
from src.metrics import calculate_financial_summary, compare_periods, safe_divide, FinancialSummary


@pytest.fixture
def hand_crafted_df():
    """
    Hand-calculated fixture:
    Row 1: qty=2, unit_price=100, unit_cost=40, discount=10, mktg=5, ship=10, returned=0
      - Gross: 2 * 100 = 200
      - Discount: 2 * 10 = 20
      - Net: 180
      - COGS: 2 * 40 = 80
      - Contribution: 180 - 80 = 100
      - OpEx: 5 + 10 = 15
      - Profit: 100 - 15 = 85

    Row 2: qty=1, unit_price=50, unit_cost=20, discount=0, mktg=3, ship=5, returned=1
      - Gross: 1 * 50 = 50
      - Discount: 0
      - Net: 50
      - COGS: 1 * 20 = 20
      - Contribution: 50 - 20 = 30
      - OpEx: 3 + 5 = 8
      - Profit: 30 - 8 = 22

    Totals:
      - Orders: 2 (ORD-1, ORD-2)
      - Units: 3
      - Gross Rev: 250
      - Discount: 20
      - Net Rev: 230
      - COGS: 100
      - Product Contribution: 130
      - OpEx: 23 (mktg=8, ship=15)
      - Estimated Profit: 107
      - Contribution Margin: 130 / 230 = 56.5217%
      - Profit Margin: 107 / 230 = 46.5217%
      - AOV: 230 / 2 = 115.00
      - Units / Order: 3 / 2 = 1.5
      - Returned Gross: 50
      - Return Rate (Rev %): 50 / 250 = 20.0%
      - Returned Units: 1
      - Return Rate (Units %): 1 / 3 = 33.333%
    """
    data = {
        "order_id": ["ORD-1", "ORD-2"],
        "line_item_id": ["L-1", "L-2"],
        "order_date": ["2024-01-01", "2024-01-02"],
        "quantity": [2, 1],
        "unit_price": [100.0, 50.0],
        "unit_cost": [40.0, 20.0],
        "discount": [10.0, 0.0],
        "marketing_cost": [5.0, 3.0],
        "shipping_cost": [10.0, 5.0],
        "returned": [0, 1],
    }
    return pd.DataFrame(data)


def test_hand_calculated_financials(hand_crafted_df):
    """Verify exact hand-calculated math against calculate_financial_summary."""
    summary = calculate_financial_summary(hand_crafted_df)

    assert summary.total_orders == 2
    assert summary.total_units == 3
    assert pytest.approx(summary.gross_revenue, 0.01) == 250.00
    assert pytest.approx(summary.total_discount, 0.01) == 20.00
    assert pytest.approx(summary.net_billed_revenue, 0.01) == 230.00
    assert pytest.approx(summary.product_cost, 0.01) == 100.00
    assert pytest.approx(summary.product_contribution, 0.01) == 130.00
    assert pytest.approx(summary.operating_expenses, 0.01) == 23.00
    assert pytest.approx(summary.estimated_profit, 0.01) == 107.00
    assert pytest.approx(summary.contribution_margin_pct, 0.01) == 56.52
    assert pytest.approx(summary.profit_margin_pct, 0.01) == 46.52
    assert pytest.approx(summary.average_order_value, 0.01) == 115.00
    assert pytest.approx(summary.average_units_per_order, 0.01) == 1.50
    assert summary.returned_units == 1
    assert pytest.approx(summary.returned_gross_revenue, 0.01) == 50.00
    assert pytest.approx(summary.return_rate_revenue_pct, 0.01) == 20.00
    assert pytest.approx(summary.return_rate_unit_pct, 0.01) == 33.33


def test_empty_dataframe_financials():
    """Verify empty DataFrame safely returns zeroed summary without crashing."""
    summary = calculate_financial_summary(pd.DataFrame())
    assert summary.total_orders == 0
    assert summary.gross_revenue == 0.0
    assert summary.contribution_margin_pct == 0.0
    assert summary.profit_margin_pct == 0.0


def test_safe_divide():
    """Verify safe_divide prevents ZeroDivisionError and NaN/inf."""
    assert safe_divide(10, 2) == 5.0
    assert safe_divide(10, 0) == 0.0
    assert safe_divide(10, 0, default=-1.0) == -1.0
    assert safe_divide(0, 100) == 0.0
    assert safe_divide(float("nan"), 10) == 0.0


def test_period_comparison():
    """Verify period-over-period comparisons compute correct deltas and percentages."""
    p1 = FinancialSummary(
        total_orders=100,
        total_line_items=120,
        total_units=200,
        gross_revenue=10000.0,
        total_discount=1000.0,
        net_billed_revenue=9000.0,
        product_cost=4000.0,
        product_contribution=5000.0,
        marketing_cost=500.0,
        shipping_cost=500.0,
        operating_expenses=1000.0,
        estimated_profit=4000.0,
        contribution_margin_pct=55.56,
        profit_margin_pct=44.44,
        average_order_value=90.0,
        average_units_per_order=2.0,
        returned_units=10,
        returned_gross_revenue=500.0,
        return_rate_revenue_pct=5.0,
        return_rate_unit_pct=5.0,
    )

    p2 = FinancialSummary(
        total_orders=120,
        total_line_items=150,
        total_units=240,
        gross_revenue=12000.0,
        total_discount=1500.0,
        net_billed_revenue=10500.0,
        product_cost=5000.0,
        product_contribution=5500.0,
        marketing_cost=600.0,
        shipping_cost=700.0,
        operating_expenses=1300.0,
        estimated_profit=4200.0,
        contribution_margin_pct=52.38,
        profit_margin_pct=40.00,
        average_order_value=87.5,
        average_units_per_order=2.0,
        returned_units=15,
        returned_gross_revenue=750.0,
        return_rate_revenue_pct=6.25,
        return_rate_unit_pct=6.25,
    )

    cmp = compare_periods(p1, p2)
    assert cmp["Gross Revenue"].absolute_change == 2000.0
    assert pytest.approx(cmp["Gross Revenue"].percentage_change, 0.01) == 20.0
    assert cmp["Estimated Profit"].absolute_change == 200.0
    assert pytest.approx(cmp["Estimated Profit"].percentage_change, 0.01) == 5.0
    assert cmp["Orders"].absolute_change == 20.0
