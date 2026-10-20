"""
Data loading and schema coercion module for ProfitLens.
Provides pure Python/Pandas loading routines and DuckDB in-memory integration.
"""

from io import StringIO, BytesIO
from typing import Union, Optional, Tuple
import duckdb
import pandas as pd

# Core required columns without which baseline analysis cannot proceed
REQUIRED_COLUMNS = [
    "order_id",
    "order_date",
    "region",
    "product_category",
    "quantity",
    "unit_price",
    "unit_cost",
    "discount",
]

# Standard optional columns that enrich the dataset if present
OPTIONAL_COLUMNS = [
    "line_item_id",
    "customer_id",
    "product_name",
    "marketing_cost",
    "shipping_cost",
    "returned",
    "order_status",
]

ALL_KNOWN_COLUMNS = REQUIRED_COLUMNS + OPTIONAL_COLUMNS


def load_dataset(
    source: Union[str, StringIO, BytesIO],
    date_col: str = "order_date",
    default_sample_path: str = "data/sample_retail_data.csv",
) -> pd.DataFrame:
    """
    Load retail dataset from a filepath, string, or file-like buffer.
    Performs standard schema coercion without destructive filtering.

    Parameters
    ----------
    source : Union[str, StringIO, BytesIO]
        File path, StringIO, or BytesIO object (e.g. from Streamlit file uploader).
    date_col : str
        Column to parse as datetime.
    default_sample_path : str
        Fallback sample dataset path if source is None.

    Returns
    -------
    pd.DataFrame
        Cleaned, typed DataFrame with standard column names.
    """
    if source is None:
        source = default_sample_path

    if hasattr(source, "read") or isinstance(source, (str, bytes)):
        df = pd.read_csv(source)
    else:
        raise ValueError(f"Unsupported source type: {type(source)}")

    if df.empty:
        return df

    # Standardize column headers: trim whitespace and lowercase
    df.columns = [str(col).strip().lower() for col in df.columns]

    # Type coercion (non-destructive; invalid entries become NaN for validator to flag)
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    numeric_cols = [
        "quantity",
        "unit_price",
        "unit_cost",
        "discount",
        "marketing_cost",
        "shipping_cost",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # If missing optional operational cost columns, populate with 0.0 with clear provenance
    if "marketing_cost" not in df.columns:
        df["marketing_cost"] = 0.0
    if "shipping_cost" not in df.columns:
        df["shipping_cost"] = 0.0

    # Ensure returned column is standardized boolean/int (0/1)
    if "returned" in df.columns:
        if df["returned"].dtype == bool:
            df["returned"] = df["returned"].astype(int)
        else:
            # Map strings or numbers to 0/1
            df["returned"] = (
                df["returned"]
                .astype(str)
                .str.strip()
                .str.lower()
                .map({"true": 1, "1": 1, "yes": 1, "t": 1, "false": 0, "0": 0, "no": 0, "f": 0})
                .fillna(0)
                .astype(int)
            )
    else:
        df["returned"] = 0

    # Ensure line_item_id exists
    if "line_item_id" not in df.columns:
        df["line_item_id"] = [f"LINE-{i+1:07d}" for i in range(len(df))]

    # Ensure order_status exists
    if "order_status" not in df.columns:
        df["order_status"] = df["returned"].apply(lambda r: "Returned" if r == 1 else "Completed")

    return df


def init_duckdb_session(df: Optional[pd.DataFrame] = None, table_name: str = "retail_data") -> duckdb.DuckDBPyConnection:
    """
    Initialize an in-memory DuckDB connection and register the DataFrame as a view/table.

    Parameters
    ----------
    df : Optional[pd.DataFrame]
        DataFrame to register in DuckDB.
    table_name : str
        Name of the SQL table/view.

    Returns
    -------
    duckdb.DuckDBPyConnection
        Active in-memory DuckDB connection.
    """
    con = duckdb.connect(database=":memory:")
    if df is not None and not df.empty:
        con.register(table_name, df)
    elif df is not None:
        # Register empty dataframe with known columns to prevent CatalogError
        empty_cols = list(df.columns) if not df.columns.empty else ALL_KNOWN_COLUMNS
        con.register(table_name, pd.DataFrame(columns=empty_cols))
    return con
