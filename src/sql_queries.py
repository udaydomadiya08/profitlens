"""
Controlled DuckDB SQL analytical queries for ProfitLens.
Provides parameterized, readable SQL queries with full text transparency.
"""

from typing import List, Optional, Tuple
import duckdb
import pandas as pd


def build_where_clause(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    regions: Optional[List[str]] = None,
    categories: Optional[List[str]] = None,
) -> Tuple[str, List]:
    """Build a parameterized SQL WHERE clause and parameters list."""
    clauses = ["1=1"]
    params = []

    if start_date:
        clauses.append("order_date >= ?")
        params.append(start_date)
    if end_date:
        clauses.append("order_date <= ?")
        params.append(end_date)
    if regions:
        placeholders = ", ".join(["?"] * len(regions))
        clauses.append(f"region IN ({placeholders})")
        params.extend(regions)
    if categories:
        placeholders = ", ".join(["?"] * len(categories))
        clauses.append(f"product_category IN ({placeholders})")
        params.extend(categories)

    where_sql = " AND ".join(clauses)
    return where_sql, params


def query_monthly_trend(
    con: duckdb.DuckDBPyConnection,
    table_name: str = "retail_data",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    regions: Optional[List[str]] = None,
    categories: Optional[List[str]] = None,
) -> Tuple[pd.DataFrame, str]:
    """
    Aggregate monthly revenue, profit, costs, orders, and margins over time.
    Returns (DataFrame, executed_sql_string).
    """
    where_sql, params = build_where_clause(start_date, end_date, regions, categories)

    sql = f"""
    SELECT 
        STRFTIME(TRY_CAST(order_date AS TIMESTAMP), '%Y-%m') AS order_month,
        COUNT(DISTINCT order_id) AS total_orders,
        SUM(quantity) AS total_units,
        ROUND(SUM(quantity * unit_price), 2) AS gross_revenue,
        ROUND(SUM(quantity * discount), 2) AS total_discount,
        ROUND(SUM(quantity * (unit_price - discount)), 2) AS net_billed_revenue,
        ROUND(SUM(quantity * unit_cost), 2) AS product_cost,
        ROUND(SUM(quantity * (unit_price - discount) - quantity * unit_cost), 2) AS product_contribution,
        ROUND(SUM(COALESCE(marketing_cost, 0.0) + COALESCE(shipping_cost, 0.0)), 2) AS operating_expenses,
        ROUND(SUM(quantity * (unit_price - discount) - quantity * unit_cost - (COALESCE(marketing_cost, 0.0) + COALESCE(shipping_cost, 0.0))), 2) AS estimated_profit,
        ROUND(
            CASE 
                WHEN SUM(quantity * (unit_price - discount)) > 0 
                THEN (SUM(quantity * (unit_price - discount) - quantity * unit_cost) / SUM(quantity * (unit_price - discount))) * 100.0 
                ELSE 0.0 
            END, 2
        ) AS contribution_margin_pct,
        ROUND(
            CASE 
                WHEN SUM(quantity * (unit_price - discount)) > 0 
                THEN (SUM(quantity * (unit_price - discount) - quantity * unit_cost - (COALESCE(marketing_cost, 0.0) + COALESCE(shipping_cost, 0.0))) / SUM(quantity * (unit_price - discount))) * 100.0 
                ELSE 0.0 
            END, 2
        ) AS profit_margin_pct
    FROM {table_name}
    WHERE {where_sql}
    GROUP BY STRFTIME(TRY_CAST(order_date AS TIMESTAMP), '%Y-%m')
    ORDER BY order_month ASC;
    """

    df = con.execute(sql, params).fetchdf()
    return df, sql


def query_dimension_breakdown(
    con: duckdb.DuckDBPyConnection,
    dimension_col: str,
    table_name: str = "retail_data",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    regions: Optional[List[str]] = None,
    categories: Optional[List[str]] = None,
) -> Tuple[pd.DataFrame, str]:
    """
    Aggregate metrics by a specific categorical dimension (e.g. region, product_category, product_name).
    """
    valid_dims = ["region", "product_category", "product_name", "order_status"]
    if dimension_col not in valid_dims:
        raise ValueError(f"Invalid dimension_col: {dimension_col}. Must be one of {valid_dims}")

    where_sql, params = build_where_clause(start_date, end_date, regions, categories)

    sql = f"""
    SELECT 
        {dimension_col},
        COUNT(DISTINCT order_id) AS total_orders,
        SUM(quantity) AS total_units,
        ROUND(SUM(quantity * unit_price), 2) AS gross_revenue,
        ROUND(SUM(quantity * discount), 2) AS total_discount,
        ROUND(SUM(quantity * (unit_price - discount)), 2) AS net_billed_revenue,
        ROUND(SUM(quantity * unit_cost), 2) AS product_cost,
        ROUND(SUM(quantity * (unit_price - discount) - quantity * unit_cost), 2) AS product_contribution,
        ROUND(SUM(COALESCE(marketing_cost, 0.0) + COALESCE(shipping_cost, 0.0)), 2) AS operating_expenses,
        ROUND(SUM(quantity * (unit_price - discount) - quantity * unit_cost - (COALESCE(marketing_cost, 0.0) + COALESCE(shipping_cost, 0.0))), 2) AS estimated_profit,
        ROUND(
            CASE 
                WHEN SUM(quantity * (unit_price - discount)) > 0 
                THEN (SUM(quantity * (unit_price - discount) - quantity * unit_cost) / SUM(quantity * (unit_price - discount))) * 100.0 
                ELSE 0.0 
            END, 2
        ) AS contribution_margin_pct,
        ROUND(
            CASE 
                WHEN SUM(quantity * (unit_price - discount)) > 0 
                THEN (SUM(quantity * (unit_price - discount) - quantity * unit_cost - (COALESCE(marketing_cost, 0.0) + COALESCE(shipping_cost, 0.0))) / SUM(quantity * (unit_price - discount))) * 100.0 
                ELSE 0.0 
            END, 2
        ) AS profit_margin_pct,
        ROUND(
            SUM(CASE WHEN returned = 1 THEN quantity * unit_price ELSE 0.0 END) / 
            NULLIF(SUM(quantity * unit_price), 0.0) * 100.0, 2
        ) AS return_rate_rev_pct
    FROM {table_name}
    WHERE {where_sql}
    GROUP BY {dimension_col}
    ORDER BY net_billed_revenue DESC;
    """

    df = con.execute(sql, params).fetchdf()
    return df, sql


def query_cross_tabulation(
    con: duckdb.DuckDBPyConnection,
    table_name: str = "retail_data",
    dim1: str = "product_category",
    dim2: str = "region",
    metric_col: str = "estimated_profit",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Tuple[pd.DataFrame, str]:
    """Generate a cross-tabulated matrix of dimensions for heatmap or matrix inspection."""
    where_sql, params = build_where_clause(start_date, end_date)

    sql = f"""
    SELECT 
        {dim1},
        {dim2},
        ROUND(SUM(quantity * (unit_price - discount)), 2) AS net_billed_revenue,
        ROUND(SUM(quantity * (unit_price - discount) - quantity * unit_cost - (COALESCE(marketing_cost, 0.0) + COALESCE(shipping_cost, 0.0))), 2) AS estimated_profit,
        ROUND(
            CASE 
                WHEN SUM(quantity * (unit_price - discount)) > 0 
                THEN (SUM(quantity * (unit_price - discount) - quantity * unit_cost - (COALESCE(marketing_cost, 0.0) + COALESCE(shipping_cost, 0.0))) / SUM(quantity * (unit_price - discount))) * 100.0 
                ELSE 0.0 
            END, 2
        ) AS profit_margin_pct
    FROM {table_name}
    WHERE {where_sql}
    GROUP BY {dim1}, {dim2}
    ORDER BY {dim1}, {dim2};
    """

    raw_df = con.execute(sql, params).fetchdf()
    if not raw_df.empty and metric_col in raw_df.columns:
        pivoted = raw_df.pivot(index=dim1, columns=dim2, values=metric_col).fillna(0.0)
    else:
        pivoted = raw_df

    return pivoted, sql
