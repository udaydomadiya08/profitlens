# ProfitLens 🔍 | Business Performance & Profit Intelligence Engine

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![DuckDB](https://img.shields.io/badge/DuckDB-In--Memory%20SQL-yellow.svg)](https://duckdb.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red.svg)](https://streamlit.io/)
[![pytest](https://img.shields.io/badge/pytest-passing-brightgreen.svg)](https://pytest.org/)

**ProfitLens** is an end-to-end business analytics application designed as a portfolio showcase for Senior Analyst and Analytics Engineering roles. It demonstrates the complete analytical lifecycle:

$$\text{Business Problem} \longrightarrow \text{Data Ingestion} \longrightarrow \text{Integrity Audit} \longrightarrow \text{Columnar SQL} \longrightarrow \text{Variance Decomposition} \longrightarrow \text{What-If Simulation} \longrightarrow \text{Executive Report}$$

---

## 1. Quickstart & Installation

### Prerequisites
- Python 3.9+
- pip

### Step-by-Step Setup
```bash
# 1. Clone repository & navigate to directory
cd profitlens

# 2. (Optional) Create & activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install required dependencies
pip install -r requirements.txt

# 4. (Optional) Re-generate deterministic synthetic dataset (seed=42)
python3 data/generate_data.py

# 5. Run automated test suite
pytest -v

# 6. Launch interactive dashboard
streamlit run app.py
```

The application will launch in your browser at `http://localhost:8501`.

---

## 2. Key Architecture & Modular Design

ProfitLens enforces strict separation of concerns. Calculation logic is completely decoupled from Streamlit presentation, enabling 100% headless testability.

```
profitlens/
├── app.py                      # Interactive Streamlit dashboard
├── requirements.txt            # Pinned runtime dependencies
├── README.md                   # System documentation & showcase
├── .gitignore                  # Clean repository exclusions
├── data/
│   ├── sample_retail_data.csv  # Reproducible 2-year synthetic dataset (8,368 records)
│   └── generate_data.py        # Deterministic dataset generator (seed=42)
├── docs/
│   ├── metric_definitions.md   # Mathematical formulas & return policies
│   ├── architecture.md         # Component boundaries & data lifecycle
│   └── interview_demonstration_script.md # 7-minute interview walkthrough
├── src/
│   ├── __init__.py
│   ├── data_loader.py          # Ingestion, schema coercion, DuckDB connection
│   ├── validation.py           # Automated data quality & integrity engine
│   ├── metrics.py              # Pure financial metrics & PoP comparison models
│   ├── analytics.py            # Managerial variance decomposition & driver ranking
│   ├── scenarios.py            # What-if elasticity simulation engine
│   ├── reporting.py            # Markdown, HTML, and CSV executive report generator
│   └── sql_queries.py          # Controlled DuckDB SQL analytical queries
└── tests/
    ├── __init__.py
    ├── test_data_loader.py     # Ingestion & DuckDB tests
    ├── test_validation.py      # Data quality constraint tests
    ├── test_metrics.py         # Hand-calculated financial fixture tests
    ├── test_analytics.py       # SQL parity & decomposition tests
    ├── test_scenarios.py       # Elasticity & cost behavior tests
    └── test_reporting.py       # Report rendering tests
```

---

## 3. Core Financial Definitions & Policies

All calculations adhere strictly to standard managerial accounting:

- **Gross Revenue**: $\sum (\text{quantity} \times \text{unit\_price})$
- **Promotional Discount Amount**: $\sum (\text{quantity} \times \text{discount})$
- **Net Billed Revenue**: $\text{Gross Revenue} - \text{Discount Amount}$
- **Product Cost (COGS)**: $\sum (\text{quantity} \times \text{unit\_cost})$
- **Product Contribution**: $\text{Net Billed Revenue} - \text{Product Cost}$
- **Allocated Operating Expenses**: $\text{Marketing Attribution} + \text{Fulfillment \& Shipping}$
- **Estimated Operating Profit**: $\text{Product Contribution} - \text{Allocated Operating Expenses}$
- **Contribution Margin (%)**: $(\text{Product Contribution} / \text{Net Billed Revenue}) \times 100\%$
- **Estimated Profit Margin (%)**: $(\text{Estimated Profit} / \text{Net Billed Revenue}) \times 100\%$
- **Average Order Value (AOV)**: $\text{Net Billed Revenue} / \text{Distinct Count of Orders}$
- **Unit Return Rate (%)**: $(\text{Returned Units} / \text{Total Units Sold}) \times 100\%$

> **Policy on Return Treatment**: Items flagged `returned=1` reflect merchandise returned by the customer. Gross revenue is tracked on total checkouts, and a sidebar toggle allows instant switching to **Recognized Net Revenue** (net of refunds). Non-refundable carrier shipping costs are treated as sunk fulfillment expenses.

---

## 4. End-to-End Workflow Capabilities

### 🛡️ 1. Data Quality & Integrity Audit
- Ingests default synthetic retail data or user-uploaded CSV.
- Automatically audits datasets for missing required columns, null values, duplicate rows, invalid timestamps, non-positive quantities ($q \le 0$), negative unit prices/costs, and discounts exceeding list prices.
- Categorizes issues by severity (`CRITICAL`, `WARNING`, `INFO`) with actionable remediation steps.

### 📊 2. In-Memory Columnar SQL Analytics (DuckDB)
- Executes parameterized DuckDB SQL queries over in-memory tables.
- Computes monthly trajectories, category and regional margin distributions, and Category $\times$ Region cross-tabulation heatmaps.
- Provides a transparent **SQL Inspector** showing the exact SQL statements executed.

### 🔬 3. Managerial Variance Decomposition (Root-Cause)
- Decomposes period-over-period profit change into four distinct factors:
  1. **Volume Effect**: Impact of unit scale changes at baseline unit margins.
  2. **Price Realization Effect**: Impact of realized net price changes and promotional discounts.
  3. **COGS Acquisition Effect**: Impact of wholesale product acquisition costs.
  4. **Operating Expense Effect**: Impact of carrier shipping and marketing spend.
- Ranks segments into **Top Positive Contributors** and **Top Negative Detractors** with analytical narratives distinguishing descriptive correlation from causal claims.

### 🎲 4. Strategic What-If Decision Simulator
- Models commercial decisions: price adjustments, discount depth changes, exogenous demand shocks, supplier cost inflation, and shipping carrier rate shifts.
- Utilizes **Price Elasticity of Demand (PED)** ($\epsilon = -1.2$) to compute demand response.
- Separates variable costs (COGS, shipping) from fixed discretionary expenses (marketing).
- Outputs labeled strictly as sensitivity *estimates*.

### 📄 5. Executive Report & Multi-Format Export
- Compiles findings into an executive briefing with scorecards, audit findings, variance evidence, scenario comparisons, and strategic recommendations.
- One-click downloads for:
  - Executive Briefing in Markdown (`.md`)
  - Self-contained, styled HTML briefing (`.html`)
  - Filtered transaction data in CSV (`.csv`)

---

## 5. Automated Testing Suite

ProfitLens includes 26 unit tests verifying calculations against hand-calculated financial fixtures:

```bash
pytest -v
```

```
tests/test_analytics.py::test_sql_vs_pandas_financial_equivalence PASSED
tests/test_analytics.py::test_dimension_breakdown_query PASSED
tests/test_analytics.py::test_profit_variance_decomposition PASSED
tests/test_analytics.py::test_identify_top_contributors PASSED
tests/test_data_loader.py::test_load_sample_retail_data_exists PASSED
tests/test_data_loader.py::test_load_from_stringio_buffer PASSED
tests/test_data_loader.py::test_type_coercion PASSED
tests/test_data_loader.py::test_init_duckdb_session PASSED
tests/test_metrics.py::test_hand_calculated_financials PASSED
tests/test_metrics.py::test_empty_dataframe_financials PASSED
tests/test_metrics.py::test_safe_divide PASSED
tests/test_metrics.py::test_period_comparison PASSED
tests/test_reporting.py::test_markdown_report_structure PASSED
tests/test_reporting.py::test_html_report_rendering PASSED
tests/test_scenarios.py::test_zero_change_scenario_matches_baseline PASSED
tests/test_scenarios.py::test_price_increase_with_elasticity PASSED
tests/test_scenarios.py::test_cost_inflation_compresses_profit PASSED
tests/test_scenarios.py::test_empty_dataset_scenario PASSED
tests/test_validation.py::test_clean_sample_data_passes_validation PASSED
tests/test_validation.py::test_empty_dataset_validation PASSED
tests/test_validation.py::test_missing_required_columns PASSED
tests/test_validation.py::test_non_positive_quantity PASSED
tests/test_validation.py::test_non_positive_unit_price PASSED
tests/test_validation.py::test_negative_unit_cost PASSED
tests/test_validation.py::test_discount_exceeds_unit_price PASSED
tests/test_validation.py::test_duplicate_rows_warning PASSED
```

---

## 6. Known Assumptions & Limitations

1. **Transaction Granularity**: Profit figures reflect operating product contribution minus allocated shipping and marketing costs. Corporate fixed overhead (executive payroll, tax, interest) is not captured at line-item granularity.
2. **Causal Attribution**: Segment driver rankings isolate historical variance. Causal efficacy of price adjustments requires controlled A/B test validation.
3. **Elasticity Linearity**: The what-if simulator assumes constant price elasticity across simulated price ranges; extreme price shocks may exhibit nonlinear consumer behavior.
