"""
Unit tests for data loading and DuckDB session setup.
"""

from io import StringIO
import os
import pytest
import pandas as pd
from src.data_loader import load_dataset, init_duckdb_session, REQUIRED_COLUMNS

SAMPLE_DATA_PATH = "data/sample_retail_data.csv"


def test_load_sample_retail_data_exists():
    """Verify default sample dataset exists and loads cleanly."""
    assert os.path.exists(SAMPLE_DATA_PATH), "data/sample_retail_data.csv should exist"
    df = load_dataset(SAMPLE_DATA_PATH)
    assert not df.empty
    assert len(df) > 1000
    for col in REQUIRED_COLUMNS:
        assert col in df.columns, f"Required column {col} missing from loaded data"


def test_load_from_stringio_buffer():
    """Verify loading from in-memory StringIO (simulates Streamlit file uploader)."""
    csv_data = """order_id,order_date,region,product_category,quantity,unit_price,unit_cost,discount
ORD-001,2024-01-15,North,Electronics,2,100.00,60.00,10.00
ORD-002,2024-01-16,South,Apparel,1,50.00,20.00,5.00
"""
    df = load_dataset(StringIO(csv_data))
    assert len(df) == 2
    assert df["quantity"].tolist() == [2, 1]
    assert df["unit_price"].tolist() == [100.0, 50.0]
    # Check default enrichment for optional columns
    assert "marketing_cost" in df.columns
    assert "shipping_cost" in df.columns
    assert "returned" in df.columns
    assert df["marketing_cost"].sum() == 0.0


def test_type_coercion():
    """Verify data types are properly coerced."""
    csv_data = """order_id,order_date,region,product_category,quantity,unit_price,unit_cost,discount,returned
ORD-101,2024-05-10,East,Sports,3,30.5,12.0,2.5,True
ORD-102,2024-05-11,West,Beauty,1,45.0,10.0,0.0,False
"""
    df = load_dataset(StringIO(csv_data))
    assert pd.api.types.is_datetime64_any_dtype(df["order_date"])
    assert pd.api.types.is_numeric_dtype(df["quantity"])
    assert pd.api.types.is_float_dtype(df["unit_price"])
    assert df["returned"].tolist() == [1, 0]


def test_init_duckdb_session():
    """Verify DuckDB session registers dataframe and allows querying."""
    csv_data = """order_id,order_date,region,product_category,quantity,unit_price,unit_cost,discount
ORD-001,2024-01-15,North,Electronics,2,100.00,60.00,10.00
ORD-002,2024-01-16,South,Apparel,1,50.00,20.00,5.00
"""
    df = load_dataset(StringIO(csv_data))
    con = init_duckdb_session(df, table_name="test_table")
    res = con.execute("SELECT COUNT(*) AS cnt, SUM(quantity) AS total_qty FROM test_table").fetchdf()
    assert res["cnt"].iloc[0] == 2
    assert res["total_qty"].iloc[0] == 3
