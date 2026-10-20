"""
Pure mathematical financial and operational metrics calculations for ProfitLens.
Independent of UI presentation layers.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
import numpy as np
import pandas as pd


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safe division preventing ZeroDivisionError or NaN/inf outputs."""
    if denominator is None or denominator == 0 or np.isnan(denominator) or np.isinf(denominator):
        return default
    if numerator is None or np.isnan(numerator) or np.isinf(numerator):
        return default
    return float(numerator / denominator)


@dataclass
class FinancialSummary:
    """Consolidated financial summary across an order-line dataset."""
    total_orders: int
    total_line_items: int
    total_units: int
    gross_revenue: float
    total_discount: float
    net_billed_revenue: float
    product_cost: float
    product_contribution: float
    marketing_cost: float
    shipping_cost: float
    operating_expenses: float
    estimated_profit: float
    contribution_margin_pct: float
    profit_margin_pct: float
    average_order_value: float
    average_units_per_order: float
    returned_units: int
    returned_gross_revenue: float
    return_rate_revenue_pct: float
    return_rate_unit_pct: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_orders": self.total_orders,
            "total_line_items": self.total_line_items,
            "total_units": self.total_units,
            "gross_revenue": round(self.gross_revenue, 2),
            "total_discount": round(self.total_discount, 2),
            "net_billed_revenue": round(self.net_billed_revenue, 2),
            "product_cost": round(self.product_cost, 2),
            "product_contribution": round(self.product_contribution, 2),
            "marketing_cost": round(self.marketing_cost, 2),
            "shipping_cost": round(self.shipping_cost, 2),
            "operating_expenses": round(self.operating_expenses, 2),
            "estimated_profit": round(self.estimated_profit, 2),
            "contribution_margin_pct": round(self.contribution_margin_pct, 2),
            "profit_margin_pct": round(self.profit_margin_pct, 2),
            "average_order_value": round(self.average_order_value, 2),
            "average_units_per_order": round(self.average_units_per_order, 2),
            "returned_units": self.returned_units,
            "returned_gross_revenue": round(self.returned_gross_revenue, 2),
            "return_rate_revenue_pct": round(self.return_rate_revenue_pct, 2),
            "return_rate_unit_pct": round(self.return_rate_unit_pct, 2),
        }


def calculate_financial_summary(df: Optional[pd.DataFrame]) -> FinancialSummary:
    """
    Calculate comprehensive financial and operational summary metrics for a given dataset slice.
    Respects order-line granularity rules and explicit definitions.
    """
    if df is None or df.empty:
        return FinancialSummary(
            total_orders=0,
            total_line_items=0,
            total_units=0,
            gross_revenue=0.0,
            total_discount=0.0,
            net_billed_revenue=0.0,
            product_cost=0.0,
            product_contribution=0.0,
            marketing_cost=0.0,
            shipping_cost=0.0,
            operating_expenses=0.0,
            estimated_profit=0.0,
            contribution_margin_pct=0.0,
            profit_margin_pct=0.0,
            average_order_value=0.0,
            average_units_per_order=0.0,
            returned_units=0,
            returned_gross_revenue=0.0,
            return_rate_revenue_pct=0.0,
            return_rate_unit_pct=0.0,
        )

    # Line item level products
    qty = df["quantity"].to_numpy()
    unit_price = df["unit_price"].to_numpy()
    unit_cost = df["unit_cost"].to_numpy()
    discount_unit = df["discount"].to_numpy()

    gross_rev_arr = qty * unit_price
    discount_arr = qty * discount_unit
    net_rev_arr = gross_rev_arr - discount_arr
    cogs_arr = qty * unit_cost
    contrib_arr = net_rev_arr - cogs_arr

    mktg_arr = df["marketing_cost"].fillna(0.0).to_numpy() if "marketing_cost" in df.columns else np.zeros(len(df))
    ship_arr = df["shipping_cost"].fillna(0.0).to_numpy() if "shipping_cost" in df.columns else np.zeros(len(df))
    op_exp_arr = mktg_arr + ship_arr
    profit_arr = contrib_arr - op_exp_arr

    # Returns
    returned_mask = (df["returned"] == 1).to_numpy() if "returned" in df.columns else np.zeros(len(df), dtype=bool)

    # Aggregations
    total_orders = int(df["order_id"].nunique()) if "order_id" in df.columns else len(df)
    total_lines = len(df)
    total_units = int(np.sum(qty))

    gross_rev = float(np.sum(gross_rev_arr))
    tot_disc = float(np.sum(discount_arr))
    net_rev = float(np.sum(net_rev_arr))
    tot_cogs = float(np.sum(cogs_arr))
    tot_contrib = float(np.sum(contrib_arr))
    tot_mktg = float(np.sum(mktg_arr))
    tot_ship = float(np.sum(ship_arr))
    tot_op_exp = float(np.sum(op_exp_arr))
    tot_profit = float(np.sum(profit_arr))

    # Margins (relative to Net Billed Revenue)
    contrib_margin_pct = safe_divide(tot_contrib, net_rev) * 100.0
    profit_margin_pct = safe_divide(tot_profit, net_rev) * 100.0

    # Order metrics
    aov = safe_divide(net_rev, total_orders)
    avg_units_order = safe_divide(total_units, total_orders)

    # Return metrics
    ret_units = int(np.sum(qty[returned_mask]))
    ret_gross = float(np.sum(gross_rev_arr[returned_mask]))
    ret_rate_rev_pct = safe_divide(ret_gross, gross_rev) * 100.0
    ret_rate_unit_pct = safe_divide(ret_units, total_units) * 100.0

    return FinancialSummary(
        total_orders=total_orders,
        total_line_items=total_lines,
        total_units=total_units,
        gross_revenue=gross_rev,
        total_discount=tot_disc,
        net_billed_revenue=net_rev,
        product_cost=tot_cogs,
        product_contribution=tot_contrib,
        marketing_cost=tot_mktg,
        shipping_cost=tot_ship,
        operating_expenses=tot_op_exp,
        estimated_profit=tot_profit,
        contribution_margin_pct=contrib_margin_pct,
        profit_margin_pct=profit_margin_pct,
        average_order_value=aov,
        average_units_per_order=avg_units_order,
        returned_units=ret_units,
        returned_gross_revenue=ret_gross,
        return_rate_revenue_pct=ret_rate_rev_pct,
        return_rate_unit_pct=ret_rate_unit_pct,
    )


@dataclass
class PeriodComparison:
    """Holds prior vs current metrics with absolute and percentage deltas."""
    metric_name: str
    prior_value: float
    current_value: float
    absolute_change: float
    percentage_change: Optional[float]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "prior_value": round(self.prior_value, 2),
            "current_value": round(self.current_value, 2),
            "absolute_change": round(self.absolute_change, 2),
            "percentage_change": round(self.percentage_change, 2) if self.percentage_change is not None else None,
        }


def compare_periods(
    prior_summary: FinancialSummary,
    current_summary: FinancialSummary
) -> Dict[str, PeriodComparison]:
    """
    Compare two FinancialSummary snapshots and compute absolute and percentage variations.
    Handles zero-denominator boundaries cleanly.
    """
    metrics_to_compare = [
        ("Gross Revenue", prior_summary.gross_revenue, current_summary.gross_revenue),
        ("Net Billed Revenue", prior_summary.net_billed_revenue, current_summary.net_billed_revenue),
        ("Discounts", prior_summary.total_discount, current_summary.total_discount),
        ("Product Cost (COGS)", prior_summary.product_cost, current_summary.product_cost),
        ("Product Contribution", prior_summary.product_contribution, current_summary.product_contribution),
        ("Operating Expenses", prior_summary.operating_expenses, current_summary.operating_expenses),
        ("Estimated Profit", prior_summary.estimated_profit, current_summary.estimated_profit),
        ("Contribution Margin (%)", prior_summary.contribution_margin_pct, current_summary.contribution_margin_pct),
        ("Profit Margin (%)", prior_summary.profit_margin_pct, current_summary.profit_margin_pct),
        ("Orders", float(prior_summary.total_orders), float(current_summary.total_orders)),
        ("Units Sold", float(prior_summary.total_units), float(current_summary.total_units)),
        ("AOV", prior_summary.average_order_value, current_summary.average_order_value),
        ("Return Rate (Rev %)", prior_summary.return_rate_revenue_pct, current_summary.return_rate_revenue_pct),
    ]

    comparisons: Dict[str, PeriodComparison] = {}
    for name, p_val, c_val in metrics_to_compare:
        abs_change = c_val - p_val
        # If comparing percentage margins, percentage change can be confusing vs bps/percentage points.
        # We calculate % change of value, but note base. If prior is 0, pct_change is None.
        if p_val == 0.0:
            pct_change = None
        else:
            pct_change = (abs_change / abs(p_val)) * 100.0

        comparisons[name] = PeriodComparison(
            metric_name=name,
            prior_value=p_val,
            current_value=c_val,
            absolute_change=abs_change,
            percentage_change=pct_change,
        )

    return comparisons
