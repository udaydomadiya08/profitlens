"""
Unit tests for executive report generation.
"""

import pytest
import pandas as pd
from src.data_loader import load_dataset
from src.metrics import calculate_financial_summary
from src.validation import validate_dataset
from src.scenarios import simulate_scenario
from src.reporting import generate_markdown_report, generate_html_report


@pytest.fixture
def sample_data():
    return load_dataset("data/sample_retail_data.csv")


def test_markdown_report_structure(sample_data):
    """Verify generated markdown report includes all required executive sections."""
    summary = calculate_financial_summary(sample_data)
    validation = validate_dataset(sample_data)
    sim = simulate_scenario(sample_data)

    report_md = generate_markdown_report(
        summary=summary,
        validation_report=validation,
        start_date="2023-01-01",
        end_date="2024-12-31",
        simulation_result=sim
    )

    assert "# Executive Business Performance & Analytics Report" in report_md
    assert "## 1. Executive Summary" in report_md
    assert "## 2. Baseline Financial & Operational Scorecard" in report_md
    assert "## 3. Data Integrity & Validation Audit" in report_md
    assert "## 5. What-If Scenario Simulation" in report_md
    assert "## 6. Strategic Recommendations" in report_md
    assert "## 7. Limitations & Methodological Assumptions" in report_md
    assert f"${summary.net_billed_revenue:,.2f}" in report_md


def test_html_report_rendering(sample_data):
    """Verify HTML generation wraps properly."""
    summary = calculate_financial_summary(sample_data)
    validation = validate_dataset(sample_data)
    report_md = generate_markdown_report(summary, validation, "2023-01-01", "2024-12-31")
    report_html = generate_html_report(report_md)

    assert "<!DOCTYPE html>" in report_html
    assert "<title>ProfitLens Executive Analytics Report</title>" in report_html
    assert "<table>" in report_html
    assert "</html>" in report_html
