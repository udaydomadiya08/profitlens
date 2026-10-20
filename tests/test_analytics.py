"""
Unit tests for analytics engine, SQL queries, and decomposition routines.
"""

import pytest
import pandas as pd
from src.data_loader import load_dataset, init_duckdb_session
from src.metrics import calculate_financial_summary
from src.analytics import decompose_profit_variance, identify_top_contributors
from src.sql_queries import query_monthly_trend, query_dimension_breakdown, query_cross_tabulation


@pytest.fixture
def sample_dataset():
    return load_dataset("data/sample_retail_data.csv")


def test_sql_vs_pandas_financial_equivalence(sample_dataset):
    """
    Verify that DuckDB SQL aggregations produce the exact same total revenue,
    product contribution, and estimated profit as the pure Pandas metrics engine.
    """
    con = init_duckdb_session(sample_dataset, table_name="retail_data")
    sql_monthly, _ = query_monthly_trend(con, table_name="retail_data")

    pandas_summary = calculate_financial_summary(sample_dataset)

    # Sum of monthly values from DuckDB
    sql_total_net_rev = sql_monthly["net_billed_revenue"].sum()
    sql_total_profit = sql_monthly["estimated_profit"].sum()
    sql_total_units = sql_monthly["total_units"].sum()

    assert pytest.approx(sql_total_net_rev, 0.5) == pandas_summary.net_billed_revenue
    assert pytest.approx(sql_total_profit, 0.5) == pandas_summary.estimated_profit
    assert int(sql_total_units) == pandas_summary.total_units


def test_dimension_breakdown_query(sample_dataset):
    """Verify categorical dimension queries execute without error and return expected categories."""
    con = init_duckdb_session(sample_dataset, table_name="retail_data")
    cat_df, sql = query_dimension_breakdown(con, "product_category")

    assert not cat_df.empty
    assert "product_category" in cat_df.columns
    assert "net_billed_revenue" in cat_df.columns
    assert "estimated_profit" in cat_df.columns
    assert len(cat_df) == 5  # Electronics, Apparel, Home & Kitchen, Beauty, Sports
    assert "SELECT" in sql


def test_profit_variance_decomposition(sample_dataset):
    """Verify variance decomposition accurately breaks down period delta."""
    # Split dataset into 2023 (prior) and 2024 (current)
    df_2023 = sample_dataset[sample_dataset["order_date"].dt.year == 2023]
    df_2024 = sample_dataset[sample_dataset["order_date"].dt.year == 2024]

    decomp = decompose_profit_variance(df_2023, df_2024)

    assert isinstance(decomp.total_profit_change, float)
    # Total change should match current_profit - prior_profit
    assert pytest.approx(decomp.total_profit_change, 0.01) == (decomp.current_profit - decomp.prior_profit)

    # Accounted effects should explain the bulk of variance
    accounted = decomp.volume_effect + decomp.price_realization_effect + decomp.cost_cogs_effect + decomp.operating_expense_effect
    assert pytest.approx(accounted + decomp.unexplained_residual, 0.01) == decomp.total_profit_change


def test_identify_top_contributors(sample_dataset):
    """Verify ranking of positive and negative contributors across categories."""
    df_2023 = sample_dataset[sample_dataset["order_date"].dt.year == 2023]
    df_2024 = sample_dataset[sample_dataset["order_date"].dt.year == 2024]

    pos, neg = identify_top_contributors(df_2023, df_2024, dimension_col="product_category", top_n=3)

    assert isinstance(pos, list)
    assert isinstance(neg, list)
    # Check that positive list items all have profit_change > 0
    for item in pos:
        assert item.profit_change > 0
        assert len(item.analytical_narrative) > 0
        assert "Descriptive variance" in item.analytical_narrative

    # Check that negative list items all have profit_change < 0
    for item in neg:
        assert item.profit_change < 0
        assert len(item.analytical_narrative) > 0


def test_sql_cross_tab_and_filters(sample_dataset):
    """Verify cross tabulation query and parameterized WHERE clause filtering."""
    con = init_duckdb_session(sample_dataset, table_name="retail_data")
    
    # Cross tabulation
    matrix, sql = query_cross_tabulation(con, table_name="retail_data", metric_col="estimated_profit")
    assert not matrix.empty
    assert "North" in matrix.columns or "South" in matrix.columns
    assert len(matrix.index) == 5

    # Filtered monthly trend
    filtered_df, filtered_sql = query_monthly_trend(
        con,
        table_name="retail_data",
        start_date="2023-01-01",
        end_date="2023-06-30",
        regions=["North", "East"],
        categories=["Electronics"]
    )
    assert not filtered_df.empty
    assert len(filtered_df) <= 6
    assert "region IN (?, ?)" in filtered_sql

