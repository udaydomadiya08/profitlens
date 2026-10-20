# ProfitLens System Architecture

ProfitLens is designed with a strict separation of concerns, ensuring core calculation and analytical routines remain completely decoupled from Streamlit's presentation layer.

---

## 1. Directory Structure

```
profitlens/
├── app.py                  # Main Streamlit dashboard interface
├── requirements.txt        # Runtime and test dependencies
├── README.md               # User guide and analyst portfolio showcase
├── .gitignore              # Repository hygiene
├── data/
│   ├── sample_retail_data.csv  # Reproducible 2-year synthetic dataset
│   └── generate_data.py        # Deterministic dataset generator
├── docs/
│   ├── metric_definitions.md   # Mathematical definitions & financial policies
│   └── architecture.md         # Component boundaries and engineering patterns
├── src/
│   ├── __init__.py
│   ├── data_loader.py      # File ingestion, schema coercion, DuckDB connection
│   ├── validation.py       # Data quality audit engine
│   ├── metrics.py          # Pure financial and operational KPI calculations
│   ├── analytics.py        # Dimensional breakdown, trends, and contributor decomposition
│   ├── scenarios.py        # What-if simulation engine with elasticity assumptions
│   ├── reporting.py        # Markdown/HTML executive briefing generator
│   └── sql_queries.py      # Parametrized DuckDB analytical queries
└── tests/
    ├── __init__.py
    ├── test_data_loader.py
    ├── test_validation.py
    ├── test_metrics.py
    └── test_scenarios.py
```

---

## 2. Core Architectural Principles

1. **Decoupled Business Logic**:
   - Every function in `src/` takes standard Python/Pandas/DuckDB data structures and returns dataclasses or clean DataFrames.
   - Zero Streamlit imports (`import streamlit`) in `src/` (except in UI wrapper helpers if needed, but core calculations must be 100% UI-agnostic).
   - Enables fast, headless testing via `pytest`.

2. **In-Memory Analytical Engine (DuckDB + Pandas)**:
   - High-performance columnar SQL execution via DuckDB for complex aggregations, window functions, and period-over-period joins.
   - Vectorized Pandas routines for dynamic scenario modeling and data transformations.

3. **Multi-Stage Data Lifecycle**:
   ```
   [CSV Upload / Default Data]
               │
               ▼
   [data_loader.py: Ingest & Coerce Types]
               │
               ▼
   [validation.py: Quality Checks & Anomalies Audit]
               │
               ├── Critical Issues? ──► [Block Analytics & Display Actionable Warnings]
               └── Clean / Warnings ──► [Proceed to Analytics & Metrics Engine]
                                           │
                        ┌──────────────────┴──────────────────┐
                        ▼                                     ▼
                [src/metrics.py]                      [src/analytics.py]
                (Summary KPIs & Margins)            (DuckDB Aggregations, Trends,
                        │                            Contributor Decomposition)
                        ▼                                     │
                [src/scenarios.py] ◄──────────────────────────┘
                (What-If Elasticity Sim)
                        │
                        ▼
                [src/reporting.py] ──► [Executive Markdown/HTML/CSV Export]
                        │
                        ▼
                [app.py (Streamlit UI)]
   ```

4. **Auditability & Traceability**:
   - Every scenario calculation explicitly retains baseline values, adjusted values, absolute differences, and percentage deltas.
   - Scenarios specify explicit assumptions (e.g., price elasticity of demand $\epsilon = -1.2$, fixed vs. variable cost behavior).
