"""
End-to-end integration and workflow verification test for ProfitLens.
Simulates real analyst interactions:
Custom CSV upload -> Data validation -> Financial Metrics -> DuckDB SQL -> Variance Decomposition -> Scenario Simulation -> Report Generation.
"""

from io import StringIO
import pytest
import pandas as pd
from src.data_loader import load_dataset, init_duckdb_session
from src.validation import validate_dataset
from src.metrics import calculate_financial_summary, compare_periods
from src.sql_queries import query_monthly_trend, query_dimension_breakdown, query_cross_tabulation
from src.analytics import decompose_profit_variance, identify_top_contributors
from src.scenarios import simulate_scenario, ScenarioAssumptions
from src.reporting import generate_markdown_report, generate_html_report


def test_complete_analyst_workflow_sample_data():
    """Simulate complete 7-step analyst workflow on standard benchmark dataset."""
    # Step 1: Ingestion
    df = load_dataset("data/sample_retail_data.csv")
    assert not df.empty
    assert len(df) == 8368

    # Step 2: Quality audit
    val = validate_dataset(df)
    assert val.is_valid is True
    assert val.critical_count == 0

    # Step 3: Pure metrics
    summary = calculate_financial_summary(df)
    assert summary.gross_revenue > 0
    assert summary.net_billed_revenue > 0
    assert summary.estimated_profit > 0
    assert 0 < summary.profit_margin_pct < 100

    # Step 4: DuckDB Columnar SQL queries
    con = init_duckdb_session(df, table_name="active_retail")
    m_df, m_sql = query_monthly_trend(con, table_name="active_retail")
    assert len(m_df) == 24  # 24 months in 2023-2024
    
    cat_df, cat_sql = query_dimension_breakdown(con, "product_category", table_name="active_retail")
    assert len(cat_df) == 5

    matrix, x_sql = query_cross_tabulation(con, table_name="active_retail")
    assert not matrix.empty

    # Step 5: Root-cause variance decomposition (2023 vs 2024)
    df_2023 = df[df["order_date"].dt.year == 2023]
    df_2024 = df[df["order_date"].dt.year == 2024]
    decomp = decompose_profit_variance(df_2023, df_2024)
    assert decomp.total_profit_change != 0
    pos, neg = identify_top_contributors(df_2023, df_2024, dimension_col="region")
    assert len(pos) > 0 or len(neg) > 0

    # Step 6: What-If Decision Simulation
    assumptions = ScenarioAssumptions(
        price_change_pct=5.0,
        discount_change_pct=-15.0,
        shipping_cost_change_pct=-8.0,
        price_elasticity_of_demand=-1.2
    )
    sim = simulate_scenario(df, assumptions)
    assert sim.simulated_summary.estimated_profit > 0
    assert sim.outcomes["Estimated Profit"].percentage_change is not None

    # Step 7: Executive Report compilation
    md_report = generate_markdown_report(
        summary=summary,
        validation_report=val,
        start_date="2023-01-01",
        end_date="2024-12-31",
        simulation_result=sim,
        pos_contributors=pos,
        neg_contributors=neg,
        variance_decomp=decomp
    )
    assert "# Executive Business Performance & Analytics Report" in md_report
    assert "Managerial Profit Variance Breakdown" in md_report

    html_report = generate_html_report(md_report)
    assert "<!DOCTYPE html>" in html_report


def test_custom_uploaded_csv_workflow():
    """Verify workflow when an analyst uploads a custom CSV with non-standard years (e.g. 2021-2022)."""
    custom_csv = """order_id,order_date,customer_id,region,product_category,product_name,quantity,unit_price,unit_cost,discount,marketing_cost,shipping_cost,returned
ORD-901,2021-03-15,C-01,Midwest,Industrial,Wrench Set,5,40.0,18.0,2.0,5.0,8.0,0
ORD-902,2021-06-20,C-02,Midwest,Industrial,Power Drill,2,120.0,65.0,10.0,12.0,15.0,0
ORD-903,2022-03-10,C-03,Midwest,Industrial,Wrench Set,6,45.0,20.0,5.0,6.0,10.0,0
ORD-904,2022-08-14,C-04,Midwest,Industrial,Power Drill,3,130.0,75.0,20.0,14.0,22.0,1
"""
    df = load_dataset(StringIO(custom_csv))
    assert len(df) == 4
    assert df["order_date"].dt.year.tolist() == [2021, 2021, 2022, 2022]

    val = validate_dataset(df)
    assert val.is_valid is True

    summary = calculate_financial_summary(df)
    assert summary.total_orders == 4
    assert summary.returned_units == 3  # row 4 has qty=3 returned

    # Variance decomposition 2021 vs 2022
    df_2021 = df[df["order_date"].dt.year == 2021]
    df_2022 = df[df["order_date"].dt.year == 2022]
    decomp = decompose_profit_variance(df_2021, df_2022)
    assert decomp.prior_profit > 0


def test_empty_filter_safety():
    """Ensure zero-row filtered slices do not crash metrics, DuckDB, or simulation."""
    empty_df = pd.DataFrame(columns=[
        "order_id", "order_date", "region", "product_category", "quantity",
        "unit_price", "unit_cost", "discount", "marketing_cost", "shipping_cost", "returned"
    ])
    
    # Metrics
    summary = calculate_financial_summary(empty_df)
    assert summary.total_orders == 0
    assert summary.estimated_profit == 0.0

    # DuckDB session
    con = init_duckdb_session(empty_df, table_name="test_empty")
    res_m, _ = query_monthly_trend(con, table_name="test_empty")
    assert res_m.empty

    # Simulation
    sim = simulate_scenario(empty_df)
    assert sim.simulated_summary.total_orders == 0
