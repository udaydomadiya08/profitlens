"""
Scenario simulation engine for ProfitLens.
Models what-if business decisions using explicit elasticity and cost behavior assumptions.
Outputs are strictly designated as estimates rather than forecasts.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

import pandas as pd

from src.metrics import calculate_financial_summary, FinancialSummary, safe_divide


@dataclass
class ScenarioAssumptions:
    """Documented input assumptions for a what-if simulation."""
    price_change_pct: float = 0.0          # e.g., +5.0% or -10.0%
    discount_change_pct: float = 0.0       # e.g., -20.0% (reducing discounts)
    volume_shock_pct: float = 0.0          # Exogenous demand shift e.g., +3.0%
    cogs_change_pct: float = 0.0           # e.g., +4.0% supplier cost inflation
    shipping_cost_change_pct: float = 0.0  # e.g., +8.0% carrier rate hikes
    price_elasticity_of_demand: float = -1.2 # % volume change per 1% price change
    fixed_marketing_share: float = 0.70    # 70% of marketing is fixed; 30% scales with volume


@dataclass
class ScenarioOutcome:
    """Consolidated comparison between baseline and simulated scenario."""
    metric_name: str
    baseline_value: float
    simulated_value: float
    absolute_change: float
    percentage_change: Optional[float]
    unit_label: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "baseline_value": round(self.baseline_value, 2),
            "simulated_value": round(self.simulated_value, 2),
            "absolute_change": round(self.absolute_change, 2),
            "percentage_change": round(self.percentage_change, 2) if self.percentage_change is not None else None,
            "unit_label": self.unit_label,
        }


@dataclass
class SimulationResult:
    """Full outcome package of a scenario run."""
    baseline_summary: FinancialSummary
    simulated_summary: FinancialSummary
    assumptions: ScenarioAssumptions
    outcomes: Dict[str, ScenarioOutcome]
    narrative_summary: str

    def to_dataframe(self) -> pd.DataFrame:
        records = []
        for o in self.outcomes.values():
            records.append({
                "Metric": o.metric_name,
                "Baseline": f"${o.baseline_value:,.2f}" if o.unit_label == "$" else (f"{o.baseline_value:.2f}%" if o.unit_label == "%" else f"{o.baseline_value:,.0f}"),
                "Simulated (Estimate)": f"${o.simulated_value:,.2f}" if o.unit_label == "$" else (f"{o.simulated_value:.2f}%" if o.unit_label == "%" else f"{o.simulated_value:,.0f}"),
                "Absolute Delta": f"${o.absolute_change:+,.2f}" if o.unit_label == "$" else (f"{o.absolute_change:+.2f} pts" if o.unit_label == "%" else f"{o.absolute_change:+,.0f}"),
                "% Change": f"{o.percentage_change:+.1f}%" if o.percentage_change is not None else "N/A"
            })
        return pd.DataFrame(records)


def simulate_scenario(
    df: pd.DataFrame,
    assumptions: Optional[ScenarioAssumptions] = None
) -> SimulationResult:
    """
    Simulate what-if scenario based on documented baseline data and economic adjustments.
    Applies price elasticity to simulate induced volume response.
    """
    if assumptions is None:
        assumptions = ScenarioAssumptions()

    baseline = calculate_financial_summary(df)

    if df.empty or baseline.total_orders == 0:
        empty_sim = calculate_financial_summary(pd.DataFrame())
        return SimulationResult(
            baseline_summary=baseline,
            simulated_summary=empty_sim,
            assumptions=assumptions,
            outcomes={},
            narrative_summary="Dataset is empty. Simulation could not be performed."
        )

    # 1. Price and Discount adjustments
    price_factor = 1.0 + (assumptions.price_change_pct / 100.0)
    discount_factor = 1.0 + (assumptions.discount_change_pct / 100.0)

    # Net price change calculation
    # Average baseline price and discount
    avg_price = safe_divide(baseline.gross_revenue, baseline.total_units)
    avg_disc = safe_divide(baseline.total_discount, baseline.total_units)
    avg_net_price = avg_price - avg_disc

    new_price = avg_price * price_factor
    new_disc = max(0.0, avg_disc * discount_factor)
    new_net_price = max(0.0, new_price - new_disc)

    net_price_pct_change = safe_divide(new_net_price - avg_net_price, avg_net_price) * 100.0

    # 2. Demand response via Price Elasticity of Demand
    # Elasticity volume shift = % change in net price * elasticity
    elasticity_volume_pct = net_price_pct_change * assumptions.price_elasticity_of_demand
    total_volume_pct_change = elasticity_volume_pct + assumptions.volume_shock_pct
    volume_factor = max(0.05, 1.0 + (total_volume_pct_change / 100.0))

    # 3. Cost factor adjustments
    cogs_factor = 1.0 + (assumptions.cogs_change_pct / 100.0)
    shipping_factor = 1.0 + (assumptions.shipping_cost_change_pct / 100.0)

    # 4. Compute Simulated Financials
    sim_units = int(round(baseline.total_units * volume_factor))
    sim_orders = int(round(baseline.total_orders * volume_factor))

    # Revenue
    sim_gross_revenue = baseline.gross_revenue * price_factor * volume_factor
    sim_discount = max(0.0, baseline.total_discount * discount_factor * volume_factor)
    sim_net_revenue = max(0.0, sim_gross_revenue - sim_discount)

    # COGS (strictly variable with volume)
    sim_cogs = baseline.product_cost * cogs_factor * volume_factor

    # Product Contribution
    sim_contribution = sim_net_revenue - sim_cogs

    # Operating expenses:
    # Shipping is 100% variable with volume
    sim_shipping = baseline.shipping_cost * shipping_factor * volume_factor
    # Marketing: fixed portion stays flat, variable portion scales with volume
    var_mktg = baseline.marketing_cost * (1.0 - assumptions.fixed_marketing_share) * volume_factor
    fix_mktg = baseline.marketing_cost * assumptions.fixed_marketing_share
    sim_marketing = fix_mktg + var_mktg

    sim_opex = sim_shipping + sim_marketing
    sim_profit = sim_contribution - sim_opex

    # Margins and AOV
    sim_contrib_margin = safe_divide(sim_contribution, sim_net_revenue) * 100.0
    sim_profit_margin = safe_divide(sim_profit, sim_net_revenue) * 100.0
    sim_aov = safe_divide(sim_net_revenue, sim_orders)

    sim_summary = FinancialSummary(
        total_orders=sim_orders,
        total_line_items=int(round(baseline.total_line_items * volume_factor)),
        total_units=sim_units,
        gross_revenue=sim_gross_revenue,
        total_discount=sim_discount,
        net_billed_revenue=sim_net_revenue,
        product_cost=sim_cogs,
        product_contribution=sim_contribution,
        marketing_cost=sim_marketing,
        shipping_cost=sim_shipping,
        operating_expenses=sim_opex,
        estimated_profit=sim_profit,
        contribution_margin_pct=sim_contrib_margin,
        profit_margin_pct=sim_profit_margin,
        average_order_value=sim_aov,
        average_units_per_order=safe_divide(sim_units, sim_orders),
        returned_units=int(round(baseline.returned_units * volume_factor)),
        returned_gross_revenue=baseline.returned_gross_revenue * price_factor * volume_factor,
        return_rate_revenue_pct=baseline.return_rate_revenue_pct,
        return_rate_unit_pct=baseline.return_rate_unit_pct,
    )

    # Compile Outcome Comparison
    def build_outcome(name: str, base_val: float, sim_val: float, unit: str) -> ScenarioOutcome:
        abs_delta = sim_val - base_val
        pct_delta = safe_divide(abs_delta, abs(base_val)) * 100.0 if base_val != 0.0 else None
        return ScenarioOutcome(
            metric_name=name,
            baseline_value=base_val,
            simulated_value=sim_val,
            absolute_change=abs_delta,
            percentage_change=pct_delta,
            unit_label=unit
        )

    outcomes = {
        "Net Billed Revenue": build_outcome("Net Billed Revenue", baseline.net_billed_revenue, sim_net_revenue, "$"),
        "Product Contribution": build_outcome("Product Contribution", baseline.product_contribution, sim_contribution, "$"),
        "Operating Expenses": build_outcome("Operating Expenses", baseline.operating_expenses, sim_opex, "$"),
        "Estimated Profit": build_outcome("Estimated Profit", baseline.estimated_profit, sim_profit, "$"),
        "Contribution Margin": build_outcome("Contribution Margin", baseline.contribution_margin_pct, sim_contrib_margin, "%"),
        "Profit Margin": build_outcome("Profit Margin", baseline.profit_margin_pct, sim_profit_margin, "%"),
        "Total Units Sold": build_outcome("Total Units Sold", float(baseline.total_units), float(sim_units), "units"),
        "Average Order Value": build_outcome("Average Order Value", baseline.average_order_value, sim_aov, "$"),
    }

    # Narrative summary
    prof_delta = sim_profit - baseline.estimated_profit
    prof_sign = "+" if prof_delta >= 0 else "-"
    direction = "expand" if prof_delta >= 0 else "contract"
    narrative = (
        f"Under modeled assumptions, estimated profit is projected to {direction} by {prof_sign}${abs(prof_delta):,.2f} "
        f"({outcomes['Estimated Profit'].percentage_change:+.1f}% vs baseline). "
        f"Volume shifts by {total_volume_pct_change:+.1f}% based on an assumed price elasticity of demand of {assumptions.price_elasticity_of_demand:.2f}."
    )

    return SimulationResult(
        baseline_summary=baseline,
        simulated_summary=sim_summary,
        assumptions=assumptions,
        outcomes=outcomes,
        narrative_summary=narrative
    )
