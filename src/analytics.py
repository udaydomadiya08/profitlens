"""
Analytical engine for ProfitLens: period decomposition, driver ranking, and root-cause diagnostics.
Adheres strictly to the requirement of separating descriptive association from causal claims.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.metrics import calculate_financial_summary, safe_divide


@dataclass
class SegmentPerformanceChange:
    """Represents period-over-period changes within a specific business segment."""
    segment_dimension: str
    segment_value: str
    prior_net_revenue: float
    current_net_revenue: float
    revenue_change: float
    revenue_growth_pct: Optional[float]
    prior_profit: float
    current_profit: float
    profit_change: float
    profit_growth_pct: Optional[float]
    prior_margin_pct: float
    current_margin_pct: float
    margin_change_pts: float
    profit_impact_share_pct: float  # Percentage of total change explained by this segment
    analytical_narrative: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "segment_dimension": self.segment_dimension,
            "segment_value": self.segment_value,
            "prior_net_revenue": round(self.prior_net_revenue, 2),
            "current_net_revenue": round(self.current_net_revenue, 2),
            "revenue_change": round(self.revenue_change, 2),
            "revenue_growth_pct": round(self.revenue_growth_pct, 2) if self.revenue_growth_pct is not None else None,
            "prior_profit": round(self.prior_profit, 2),
            "current_profit": round(self.current_profit, 2),
            "profit_change": round(self.profit_change, 2),
            "profit_growth_pct": round(self.profit_growth_pct, 2) if self.profit_growth_pct is not None else None,
            "prior_margin_pct": round(self.prior_margin_pct, 2),
            "current_margin_pct": round(self.current_margin_pct, 2),
            "margin_change_pts": round(self.margin_change_pts, 2),
            "profit_impact_share_pct": round(self.profit_impact_share_pct, 2),
            "analytical_narrative": self.analytical_narrative,
        }


@dataclass
class ProfitVarianceDecomposition:
    """
    Decomposes total period-over-period profit variance into distinct descriptive factors:
    1. Volume Effect: Change in profit driven by selling more/fewer total units at prior baseline unit margins.
    2. Net Price / Discount Effect: Change driven by higher/lower realized net prices.
    3. Product Cost (COGS) Effect: Change driven by unit acquisition cost inflation/savings.
    4. Operating Expense Effect: Change driven by changes in marketing and logistics costs.
    """
    prior_profit: float
    current_profit: float
    total_profit_change: float
    volume_effect: float
    price_realization_effect: float
    cost_cogs_effect: float
    operating_expense_effect: float
    unexplained_residual: float

    def to_dict(self) -> Dict[str, float]:
        return {
            "prior_profit": round(self.prior_profit, 2),
            "current_profit": round(self.current_profit, 2),
            "total_profit_change": round(self.total_profit_change, 2),
            "volume_effect": round(self.volume_effect, 2),
            "price_realization_effect": round(self.price_realization_effect, 2),
            "cost_cogs_effect": round(self.cost_cogs_effect, 2),
            "operating_expense_effect": round(self.operating_expense_effect, 2),
            "unexplained_residual": round(self.unexplained_residual, 2),
        }


def decompose_profit_variance(
    prior_df: pd.DataFrame,
    current_df: pd.DataFrame
) -> ProfitVarianceDecomposition:
    """
    Perform formal managerial accounting variance decomposition on profit between two periods.
    """
    p_sum = calculate_financial_summary(prior_df)
    c_sum = calculate_financial_summary(current_df)

    p_units = max(p_sum.total_units, 1)
    c_units = max(c_sum.total_units, 1)

    # Average realized rates per unit in prior period
    p_avg_net_price = p_sum.net_billed_revenue / p_units
    p_avg_cogs = p_sum.product_cost / p_units
    p_avg_contrib = p_sum.product_contribution / p_units

    # Average realized rates in current period
    c_avg_net_price = c_sum.net_billed_revenue / c_units
    c_avg_cogs = c_sum.product_cost / c_units

    delta_units = c_sum.total_units - p_sum.total_units
    total_delta_profit = c_sum.estimated_profit - p_sum.estimated_profit

    # 1. Volume effect: (Current Units - Prior Units) * Prior Baseline Unit Contribution
    volume_effect = delta_units * p_avg_contrib

    # 2. Price/Discount realization effect: Current Units * (Current Net Price - Prior Net Price)
    price_effect = c_sum.total_units * (c_avg_net_price - p_avg_net_price)

    # 3. Cost (COGS) effect: Current Units * (Prior COGS - Current COGS) [Savings is positive]
    cost_effect = c_sum.total_units * (p_avg_cogs - c_avg_cogs)

    # 4. Operating expense effect: (Prior OpEx - Current OpEx) [Lower OpEx is positive]
    opex_effect = p_sum.operating_expenses - c_sum.operating_expenses

    accounted_change = volume_effect + price_effect + cost_effect + opex_effect
    residual = total_delta_profit - accounted_change

    return ProfitVarianceDecomposition(
        prior_profit=p_sum.estimated_profit,
        current_profit=c_sum.estimated_profit,
        total_profit_change=total_delta_profit,
        volume_effect=volume_effect,
        price_realization_effect=price_effect,
        cost_cogs_effect=cost_effect,
        operating_expense_effect=opex_effect,
        unexplained_residual=residual,
    )


def identify_top_contributors(
    prior_df: pd.DataFrame,
    current_df: pd.DataFrame,
    dimension_col: str = "product_category",
    top_n: int = 5,
) -> Tuple[List[SegmentPerformanceChange], List[SegmentPerformanceChange]]:
    """
    Rank segments by positive contribution and negative detraction to total profit change.
    Returns (top_positive_contributors, top_negative_detractors).
    Generates descriptive narratives that carefully avoid asserting unsupported causal claims.
    """
    if prior_df.empty or current_df.empty or dimension_col not in prior_df.columns:
        return [], []

    all_segments = sorted(list(set(prior_df[dimension_col].dropna().unique()).union(
        set(current_df[dimension_col].dropna().unique())
    )))

    total_prior_profit = calculate_financial_summary(prior_df).estimated_profit
    total_current_profit = calculate_financial_summary(current_df).estimated_profit
    total_profit_delta = total_current_profit - total_prior_profit

    segment_results: List[SegmentPerformanceChange] = []

    for seg in all_segments:
        p_sub = pd.DataFrame(prior_df[prior_df[dimension_col] == seg])
        c_sub = pd.DataFrame(current_df[current_df[dimension_col] == seg])

        p_m = calculate_financial_summary(p_sub)
        c_m = calculate_financial_summary(c_sub)

        rev_change = c_m.net_billed_revenue - p_m.net_billed_revenue
        rev_growth = ((rev_change / p_m.net_billed_revenue) * 100.0) if p_m.net_billed_revenue > 0 else None

        prof_change = c_m.estimated_profit - p_m.estimated_profit
        prof_growth = ((prof_change / abs(p_m.estimated_profit)) * 100.0) if p_m.estimated_profit != 0 else None

        margin_change = c_m.profit_margin_pct - p_m.profit_margin_pct

        # Share of total movement explained by this segment
        impact_share = safe_divide(prof_change, total_profit_delta) * 100.0 if total_profit_delta != 0 else 0.0

        # Build descriptive narrative
        dir_word = "increased" if prof_change >= 0 else "declined"
        narrative = (
            f"{dimension_col.replace('_', ' ').title()} '{seg}' profit {dir_word} by ${abs(prof_change):,.2f} "
            f"(margin moved from {p_m.profit_margin_pct:.1f}% to {c_m.profit_margin_pct:.1f}%). "
            f"Note: Descriptive variance; verify operational driver details."
        )

        segment_results.append(
            SegmentPerformanceChange(
                segment_dimension=dimension_col,
                segment_value=str(seg),
                prior_net_revenue=p_m.net_billed_revenue,
                current_net_revenue=c_m.net_billed_revenue,
                revenue_change=rev_change,
                revenue_growth_pct=rev_growth,
                prior_profit=p_m.estimated_profit,
                current_profit=c_m.estimated_profit,
                profit_change=prof_change,
                profit_growth_pct=prof_growth,
                prior_margin_pct=p_m.profit_margin_pct,
                current_margin_pct=c_m.profit_margin_pct,
                margin_change_pts=margin_change,
                profit_impact_share_pct=impact_share,
                analytical_narrative=narrative,
            )
        )

    # Sort descending for positive contributors, ascending for negative detractors
    positive_contributors = [s for s in segment_results if s.profit_change > 0]
    positive_contributors.sort(key=lambda x: x.profit_change, reverse=True)

    negative_detractors = [s for s in segment_results if s.profit_change < 0]
    negative_detractors.sort(key=lambda x: x.profit_change, reverse=False)

    return positive_contributors[:top_n], negative_detractors[:top_n]
