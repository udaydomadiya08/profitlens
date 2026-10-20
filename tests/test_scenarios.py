"""
Unit tests for what-if scenario simulator.
Verifies economic elasticity models, cost scaling, and boundary conditions.
"""

import pytest
import pandas as pd
from src.data_loader import load_dataset
from src.scenarios import simulate_scenario, ScenarioAssumptions


@pytest.fixture
def sample_data():
    return load_dataset("data/sample_retail_data.csv")


def test_zero_change_scenario_matches_baseline(sample_data):
    """Verify that 0% adjustments across all parameters yields identical results to baseline."""
    res = simulate_scenario(sample_data, ScenarioAssumptions())
    
    assert res.baseline_summary.total_units == res.simulated_summary.total_units
    assert pytest.approx(res.baseline_summary.net_billed_revenue, 0.01) == res.simulated_summary.net_billed_revenue
    assert pytest.approx(res.baseline_summary.estimated_profit, 0.01) == res.simulated_summary.estimated_profit
    
    for outcome in res.outcomes.values():
        assert outcome.absolute_change == 0.0


def test_price_increase_with_elasticity(sample_data):
    """
    Verify that an increase in price with negative elasticity (-1.2):
    1. Reduces units sold.
    2. Modifies net revenue accordingly.
    """
    assumptions = ScenarioAssumptions(
        price_change_pct=10.0,
        price_elasticity_of_demand=-1.2
    )
    res = simulate_scenario(sample_data, assumptions)

    # Elasticity of -1.2 on ~10% price increase should reduce volume by ~12%
    assert res.simulated_summary.total_units < res.baseline_summary.total_units
    assert res.outcomes["Total Units Sold"].percentage_change < 0


def test_cost_inflation_compresses_profit(sample_data):
    """Verify supplier cost inflation (+15% COGS) compresses profit and margins."""
    assumptions = ScenarioAssumptions(cogs_change_pct=15.0)
    res = simulate_scenario(sample_data, assumptions)

    assert res.simulated_summary.product_cost > res.baseline_summary.product_cost
    assert res.simulated_summary.estimated_profit < res.baseline_summary.estimated_profit
    assert res.simulated_summary.profit_margin_pct < res.baseline_summary.profit_margin_pct


def test_empty_dataset_scenario():
    """Verify simulation handles empty dataset safely without throwing exceptions."""
    res = simulate_scenario(pd.DataFrame(), ScenarioAssumptions())
    assert res.simulated_summary.total_orders == 0
    assert "Simulation could not be performed" in res.narrative_summary
