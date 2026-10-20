"""
Unit tests for data validation engine.
Verifies quality checks, severity categorization, and actionable diagnostics.
"""

from io import StringIO
import pytest
import pandas as pd
from src.data_loader import load_dataset
from src.validation import validate_dataset, ValidationReport


@pytest.fixture
def clean_sample_df():
    """Returns the default clean sample dataset."""
    return load_dataset("data/sample_retail_data.csv")


def test_clean_sample_data_passes_validation(clean_sample_df):
    """Verify that the generated sample dataset is valid with no critical errors."""
    report = validate_dataset(clean_sample_df)
    assert isinstance(report, ValidationReport)
    assert report.is_valid is True
    assert report.has_critical_errors is False
    assert report.critical_count == 0
    assert report.total_rows == len(clean_sample_df)


def test_empty_dataset_validation():
    """Verify empty dataframe flags critical issue."""
    report = validate_dataset(pd.DataFrame())
    assert report.is_valid is False
    assert report.has_critical_errors is True
    assert any(i.check_name == "empty_dataset" for i in report.issues)


def test_missing_required_columns():
    """Verify missing required columns are flagged as CRITICAL."""
    df = pd.DataFrame({
        "order_id": ["ORD-1"],
        "region": ["North"],
        # Missing order_date, quantity, unit_price, unit_cost, discount, product_category
    })
    report = validate_dataset(df)
    assert report.is_valid is False
    assert any(i.check_name == "missing_required_columns" for i in report.issues)


def test_non_positive_quantity():
    """Verify quantity <= 0 is flagged as CRITICAL."""
    csv_data = """order_id,order_date,region,product_category,quantity,unit_price,unit_cost,discount
ORD-001,2024-01-15,North,Electronics,0,100.00,60.00,10.00
ORD-002,2024-01-16,South,Apparel,-2,50.00,20.00,5.00
"""
    df = load_dataset(StringIO(csv_data))
    report = validate_dataset(df)
    assert report.is_valid is False
    issue = next(i for i in report.issues if i.check_name == "non_positive_quantity")
    assert issue.severity == "CRITICAL"
    assert issue.affected_rows_count == 2
    assert len(issue.action_recommendation) > 0


def test_non_positive_unit_price():
    """Verify unit_price <= 0 is flagged as CRITICAL."""
    csv_data = """order_id,order_date,region,product_category,quantity,unit_price,unit_cost,discount
ORD-001,2024-01-15,North,Electronics,1,0.00,60.00,0.00
ORD-002,2024-01-16,South,Apparel,1,-50.00,20.00,0.00
"""
    df = load_dataset(StringIO(csv_data))
    report = validate_dataset(df)
    assert report.is_valid is False
    issue = next(i for i in report.issues if i.check_name == "non_positive_unit_price")
    assert issue.severity == "CRITICAL"
    assert issue.affected_rows_count == 2


def test_negative_unit_cost():
    """Verify unit_cost < 0 is flagged as CRITICAL."""
    csv_data = """order_id,order_date,region,product_category,quantity,unit_price,unit_cost,discount
ORD-001,2024-01-15,North,Electronics,1,100.00,-15.00,0.00
"""
    df = load_dataset(StringIO(csv_data))
    report = validate_dataset(df)
    assert report.is_valid is False
    assert any(i.check_name == "negative_unit_cost" for i in report.issues)


def test_discount_exceeds_unit_price():
    """Verify discount > unit_price is flagged as CRITICAL."""
    csv_data = """order_id,order_date,region,product_category,quantity,unit_price,unit_cost,discount
ORD-001,2024-01-15,North,Electronics,1,100.00,60.00,120.00
"""
    df = load_dataset(StringIO(csv_data))
    report = validate_dataset(df)
    assert report.is_valid is False
    issue = next(i for i in report.issues if i.check_name == "discount_exceeds_unit_price")
    assert issue.severity == "CRITICAL"
    assert issue.affected_rows_count == 1


def test_duplicate_rows_warning():
    """Verify duplicate rows trigger a warning without crashing."""
    csv_data = """order_id,order_date,region,product_category,quantity,unit_price,unit_cost,discount
ORD-001,2024-01-15,North,Electronics,1,100.00,60.00,10.00
ORD-001,2024-01-15,North,Electronics,1,100.00,60.00,10.00
"""
    df = load_dataset(StringIO(csv_data))
    report = validate_dataset(df)
    assert report.has_warnings is True
    assert any(i.check_name == "exact_duplicate_rows" for i in report.issues)
