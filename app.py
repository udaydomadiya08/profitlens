"""
ProfitLens - Executive Business Analytics Application.
Streamlit interactive dashboard demonstrating the end-to-end analytical workflow.
"""

from datetime import datetime
from typing import Optional, Any
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.data_loader import load_dataset, init_duckdb_session
from src.validation import validate_dataset
from src.metrics import calculate_financial_summary, compare_periods, safe_divide
from src.sql_queries import query_monthly_trend, query_dimension_breakdown, query_cross_tabulation
from src.analytics import decompose_profit_variance, identify_top_contributors
from src.scenarios import ScenarioAssumptions, simulate_scenario
from src.reporting import generate_markdown_report, generate_html_report

# ---------------------------------------------------------
# Page Configuration & Global Theme
# ---------------------------------------------------------
st.set_page_config(
    page_title="ProfitLens | Business Analytics & Profit Intelligence",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for polished aesthetics
st.markdown("""
<style>
    /* Metric Card Styling */
    .metric-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 12px;
    }
    .metric-title {
        color: #64748b;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-value {
        color: #0f172a;
        font-size: 1.8rem;
        font-weight: 700;
        margin: 4px 0;
    }
    .metric-sub {
        font-size: 0.82rem;
        font-weight: 500;
    }
    .delta-pos { color: #16a34a; }
    .delta-neg { color: #dc2626; }
    .delta-neu { color: #64748b; }
    
    /* Section Headers */
    .section-header {
        border-left: 4px solid #2563eb;
        padding-left: 12px;
        margin: 24px 0 16px 0;
        font-size: 1.25rem;
        font-weight: 700;
        color: #1e293b;
    }
    
    /* Banner */
    .portfolio-banner {
        background: linear-gradient(90deg, #1e3a8a 0%, #2563eb 100%);
        color: white;
        padding: 20px 24px;
        border-radius: 12px;
        margin-bottom: 24px;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# Data Loading & Caching
# ---------------------------------------------------------
@st.cache_data(show_spinner=False)
def get_dataset(uploaded_file=None):
    if uploaded_file is not None:
        return load_dataset(uploaded_file)
    return load_dataset("data/sample_retail_data.csv")


# ---------------------------------------------------------
# Sidebar Controls & Filters
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%); padding: 18px 14px; border-radius: 10px; margin-bottom: 12px; text-align: center; color: white;">
        <span style="font-size: 2.2rem;">🔍</span>
        <h2 style="color: white; margin: 4px 0 0 0; font-size: 1.35rem; font-weight: 700;">ProfitLens</h2>
        <p style="margin: 2px 0 0 0; font-size: 0.75rem; opacity: 0.9; letter-spacing: 0.5px;">BUSINESS & PROFIT INTELLIGENCE</p>
    </div>
    """, unsafe_allow_html=True)
    st.caption("Analyst Portfolio Project | Illustrative Benchmark Engine")
    
    st.divider()
    
    st.subheader("📁 Data Source")
    data_mode = st.radio(
        "Choose Data Source:",
        ["Sample Retail Data (2023-2024)", "Upload Custom CSV"],
        index=0
    )
    
    uploaded_file = None
    if data_mode == "Upload Custom CSV":
        uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
        if uploaded_file is None:
            st.info("Using sample retail data until a file is uploaded.")
    
    df_raw = get_dataset(uploaded_file)
    
    st.divider()
    
    st.subheader("🎯 Dimension Filters")
    
    # Date Range Filter
    min_date = df_raw["order_date"].min().date() if not df_raw.empty and "order_date" in df_raw.columns else datetime(2023, 1, 1).date()
    max_date = df_raw["order_date"].max().date() if not df_raw.empty and "order_date" in df_raw.columns else datetime(2024, 12, 31).date()
    
    date_selection = st.date_input(
        "Order Date Range:",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # Region Filter
    available_regions = sorted(df_raw["region"].dropna().unique().tolist()) if "region" in df_raw.columns else []
    selected_regions = st.multiselect("Regions:", available_regions, default=available_regions)
    
    # Category Filter
    available_categories = sorted(df_raw["product_category"].dropna().unique().tolist()) if "product_category" in df_raw.columns else []
    selected_categories = st.multiselect("Product Categories:", available_categories, default=available_categories)
    
    # Return treatment toggle
    st.divider()
    st.subheader("⚙️ Accounting Policy")
    exclude_returns = st.toggle("Exclude Returned Orders from Revenue/Profit", value=False)
    
    st.caption("ProfitLens v1.0.0 | Pure Python + DuckDB + Plotly")


# ---------------------------------------------------------
df_filtered: pd.DataFrame = pd.DataFrame(df_raw.copy())

if isinstance(date_selection, tuple) and len(date_selection) == 2:
    start_dt, end_dt = pd.to_datetime(date_selection[0]), pd.to_datetime(date_selection[1]) + pd.Timedelta(days=1)
    df_filtered = pd.DataFrame(df_filtered[(df_filtered["order_date"] >= start_dt) & (df_filtered["order_date"] < end_dt)])

if selected_regions:
    df_filtered = pd.DataFrame(df_filtered[df_filtered["region"].isin(selected_regions)])

if selected_categories:
    df_filtered = pd.DataFrame(df_filtered[df_filtered["product_category"].isin(selected_categories)])

if exclude_returns and "returned" in df_filtered.columns:
    df_filtered = pd.DataFrame(df_filtered[df_filtered["returned"] == 0])

# Pre-declared references to prevent unbound issues across tabs
df_prior: Optional[pd.DataFrame] = None
sim_result: Optional[Any] = None


# ---------------------------------------------------------
# Main App Header & Navigation
# ---------------------------------------------------------
st.markdown("""
<div class="portfolio-banner">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h2 style="margin:0; font-size:1.75rem;">ProfitLens: Business Performance & Profit Intelligence</h2>
            <p style="margin:6px 0 0 0; opacity:0.95; font-size:0.92rem;">
                End-to-End Analytics Workflow: Business Problem → Data Validation → Columnar SQL → Variance Decomposition → Decision Simulator → Executive Briefing
            </p>
        </div>
        <div style="background: rgba(255,255,255,0.15); padding: 6px 14px; border-radius: 8px; font-size: 0.8rem; font-weight: 600; text-align: right;">
            Illustrative Portfolio Demo<br><span style="font-weight:400; opacity:0.85;">Synthetic Retail Benchmark</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Navigation Tabs
tab_overview, tab_quality, tab_performance, tab_root_cause, tab_simulator, tab_report = st.tabs([
    "📈 Executive Overview",
    "🛡️ Data Quality & Audit",
    "📊 Performance & SQL Analytics",
    "🔬 Root-Cause Investigation",
    "🎲 What-If Simulator",
    "📄 Executive Report"
])


# =========================================================
# TAB 1: EXECUTIVE OVERVIEW
# =========================================================
with tab_overview:
    if df_filtered.empty:
        st.warning("⚠️ No data matches the selected filters. Please expand your filter criteria in the sidebar.")
    else:
        # Calculate current summary
        summary = calculate_financial_summary(df_filtered)
        
        # Calculate previous period for comparison (if date range is filtered)
        # For meaningful comparison, split filtered date range into prior equivalent duration
        date_span = (df_filtered["order_date"].max() - df_filtered["order_date"].min()).days
        prior_end = df_filtered["order_date"].min()
        prior_start = prior_end - pd.Timedelta(days=max(date_span, 30))
        df_prior = pd.DataFrame(df_raw[
            (df_raw["order_date"] >= prior_start) & 
            (df_raw["order_date"] < prior_end) & 
            (df_raw["region"].isin(selected_regions if selected_regions else available_regions)) &
            (df_raw["product_category"].isin(selected_categories if selected_categories else available_categories))
        ])
        if exclude_returns and "returned" in df_prior.columns:
            df_prior = pd.DataFrame(df_prior[df_prior["returned"] == 0])
            
        prior_summary = calculate_financial_summary(df_prior)
        pop_comparison = compare_periods(prior_summary, summary)

        # Top KPI Ribbon
        kpi_cols = st.columns(6)
        
        def render_kpi(col, title, value_str, pop_key, is_currency=False, is_pct=False):
            cmp = pop_comparison.get(pop_key)
            with col:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">{title}</div>
                    <div class="metric-value">{value_str}</div>
                    <div class="metric-sub">
                        {f'<span class="delta-pos">▲ +{cmp.percentage_change:.1f}%</span>' if cmp and cmp.percentage_change and cmp.percentage_change > 0 else (f'<span class="delta-neg">▼ {cmp.percentage_change:.1f}%</span>' if cmp and cmp.percentage_change and cmp.percentage_change < 0 else '<span class="delta-neu">Baseline</span>')} vs prior
                    </div>
                </div>
                """, unsafe_allow_html=True)

        render_kpi(kpi_cols[0], "Net Billed Revenue", f"${summary.net_billed_revenue:,.0f}", "Net Billed Revenue")
        render_kpi(kpi_cols[1], "Estimated Profit", f"${summary.estimated_profit:,.0f}", "Estimated Profit")
        render_kpi(kpi_cols[2], "Profit Margin", f"{summary.profit_margin_pct:.1f}%", "Profit Margin (%)")
        render_kpi(kpi_cols[3], "Contribution Margin", f"{summary.contribution_margin_pct:.1f}%", "Contribution Margin (%)")
        render_kpi(kpi_cols[4], "Average Order Value", f"${summary.average_order_value:.2f}", "AOV")
        render_kpi(kpi_cols[5], "Return Rate (Rev)", f"{summary.return_rate_revenue_pct:.1f}%", "Return Rate (Rev %)")

        st.markdown("<div class=\"section-header\">Financial P&L Waterfall Breakdown</div>", unsafe_allow_html=True)
        
        # P&L Waterfall Chart
        wf_x = ["Gross Revenue", "Discounts", "Net Revenue", "Product Cost (COGS)", "Product Contribution", "Operating Expenses", "Estimated Profit"]
        wf_y = [
            summary.gross_revenue,
            -summary.total_discount,
            summary.net_billed_revenue,
            -summary.product_cost,
            summary.product_contribution,
            -summary.operating_expenses,
            summary.estimated_profit
        ]
        wf_measures = ["relative", "relative", "total", "relative", "total", "relative", "total"]
        
        fig_wf = go.Figure(go.Waterfall(
            name="P&L Summary",
            orientation="v",
            measure=wf_measures,
            x=wf_x,
            textposition="outside",
            text=[f"${abs(v):,.0f}" for v in wf_y],
            y=wf_y,
            connector={"line": {"color": "#94a3b8"}},
            decreasing={"marker": {"color": "#ef4444"}},
            increasing={"marker": {"color": "#10b981"}},
            totals={"marker": {"color": "#2563eb"}}
        ))
        fig_wf.update_layout(
            height=380,
            margin=dict(l=20, r=20, t=30, b=20),
            plot_bgcolor="white",
            paper_bgcolor="white",
            yaxis=dict(title="USD ($)", gridcolor="#f1f5f9")
        )
        st.plotly_chart(fig_wf, use_container_width=True)

        # Contextual summary metrics in columns
        sum_col1, sum_col2 = st.columns(2)
        with sum_col1:
            st.markdown("<div class=\"section-header\">Volume & Customer Throughput</div>", unsafe_allow_html=True)
            st.dataframe(pd.DataFrame({
                "Operational Metric": ["Total Orders Fulfilled", "Total Units Sold", "Average Units per Order", "Total Line Items Processed"],
                "Current Performance": [f"{summary.total_orders:,}", f"{summary.total_units:,}", f"{summary.average_units_per_order:.2f}", f"{summary.total_line_items:,}"]
            }), hide_index=True, use_container_width=True)

        with sum_col2:
            st.markdown("<div class=\"section-header\">Expense Breakdown</div>", unsafe_allow_html=True)
            st.dataframe(pd.DataFrame({
                "Expense Category": ["Product Acquisition (COGS)", "Logistics & Shipping Cost", "Marketing Attribution Cost", "Total Discounts Conceded"],
                "Total USD ($)": [f"${summary.product_cost:,.2f}", f"${summary.shipping_cost:,.2f}", f"${summary.marketing_cost:,.2f}", f"${summary.total_discount:,.2f}"],
                "% of Gross Revenue": [
                    f"{safe_divide(summary.product_cost, summary.gross_revenue)*100:.1f}%",
                    f"{safe_divide(summary.shipping_cost, summary.gross_revenue)*100:.1f}%",
                    f"{safe_divide(summary.marketing_cost, summary.gross_revenue)*100:.1f}%",
                    f"{safe_divide(summary.total_discount, summary.gross_revenue)*100:.1f}%"
                ]
            }), hide_index=True, use_container_width=True)


# =========================================================
# TAB 2: DATA QUALITY & AUDIT
# =========================================================
with tab_quality:
    st.markdown("<div class=\"section-header\">Data Quality & Integrity Audit</div>", unsafe_allow_html=True)
    st.write(
        "ProfitLens systematically validates incoming data against analytical constraints prior to computation. "
        "Every identified issue is categorized by severity with explicit remediation guidance."
    )
    
    validation_report = validate_dataset(df_raw)
    
    # Audit Scorecard
    card1, card2, card3, card4 = st.columns(4)
    card1.metric("Total Records Audited", f"{validation_report.total_rows:,}")
    card2.metric("Critical Errors (Blocking)", f"{validation_report.critical_count}", delta_color="inverse")
    card3.metric("Warnings (Non-blocking)", f"{validation_report.warning_count}", delta_color="inverse")
    card4.metric("Dataset Health Status", "PASSED" if validation_report.is_valid else "FAILED")

    if not validation_report.is_valid:
        st.error("🚨 Critical data validation errors detected! Core financial calculations may be compromised until addressed.")
    else:
        st.success("✅ Dataset meets all primary integrity standards for business intelligence.")

    # Issues Table
    if validation_report.issues:
        st.subheader("Inspection Log & Diagnostic Findings")
        issues_data = []
        for issue in validation_report.issues:
            issues_data.append({
                "Severity": issue.severity,
                "Audit Check": issue.check_name,
                "Target Column": issue.column or "General",
                "Affected Records": f"{issue.affected_rows_count:,}",
                "Observation": issue.message,
                "Action Recommendation": issue.action_recommendation
            })
        st.dataframe(pd.DataFrame(issues_data), hide_index=True, use_container_width=True)
    else:
        st.info("No anomalies or warnings identified.")

    with st.expander("🔍 View Raw Schema & Column Profiling"):
        profile_df = pd.DataFrame({
            "Column": df_raw.columns,
            "Data Type": [str(t) for t in df_raw.dtypes],
            "Null Count": df_raw.isna().sum().values,
            "Null Pct": [f"{(c/len(df_raw))*100:.1f}%" for c in df_raw.isna().sum().values],
            "Unique Values": df_raw.nunique().values
        })
        st.dataframe(profile_df, hide_index=True, use_container_width=True)


# =========================================================
# TAB 3: PERFORMANCE & SQL ANALYTICS
# =========================================================
with tab_performance:
    st.markdown("<div class=\"section-header\">Columnar SQL Analytics (Powered by DuckDB)</div>", unsafe_allow_html=True)
    st.caption("All aggregations below execute in-memory columnar SQL queries via DuckDB.")
    
    if df_filtered.empty:
        st.warning("⚠️ No data matches the active filters. Please adjust your date range or dimension filters in the sidebar.")
    else:
        con = init_duckdb_session(df_filtered, table_name="active_retail")
        
        # 1. Monthly Time Series
        monthly_df, monthly_sql = query_monthly_trend(con, table_name="active_retail")
        
        if not monthly_df.empty:
            st.subheader("Monthly Revenue, Profit & Margin Trajectory")
            
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Bar(
                x=monthly_df["order_month"],
                y=monthly_df["net_billed_revenue"],
                name="Net Billed Revenue ($)",
                marker_color="#3b82f6",
                opacity=0.85
            ))
            fig_trend.add_trace(go.Bar(
                x=monthly_df["order_month"],
                y=monthly_df["estimated_profit"],
                name="Estimated Profit ($)",
                marker_color="#10b981",
                opacity=0.9
            ))
            fig_trend.add_trace(go.Scatter(
                x=monthly_df["order_month"],
                y=monthly_df["profit_margin_pct"],
                name="Profit Margin (%)",
                yaxis="y2",
                mode="lines+markers",
                line=dict(color="#f59e0b", width=3)
            ))
            
            fig_trend.update_layout(
                barmode="group",
                height=420,
                margin=dict(l=20, r=20, t=30, b=20),
                plot_bgcolor="white",
                paper_bgcolor="white",
                yaxis=dict(title="Amount in USD ($)", gridcolor="#f1f5f9"),
                yaxis2=dict(title="Profit Margin (%)", overlaying="y", side="right", range=[-10, 60]),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_trend, use_container_width=True)

        # 2. Categorical & Regional Breakdown
        perf_col1, perf_col2 = st.columns(2)
        
        with perf_col1:
            st.subheader("Performance by Product Category")
            cat_df, cat_sql = query_dimension_breakdown(con, "product_category", table_name="active_retail")
            if not cat_df.empty:
                fig_cat = px.bar(
                    cat_df,
                    x="product_category",
                    y="net_billed_revenue",
                    color="profit_margin_pct",
                    color_continuous_scale="Tealgrn",
                    text="net_billed_revenue",
                    labels={"net_billed_revenue": "Net Revenue ($)", "profit_margin_pct": "Margin %", "product_category": "Category"}
                )
                fig_cat.update_traces(texttemplate="$%{text:,.0f}", textposition="outside")
                fig_cat.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=350, margin=dict(l=10, r=10, t=20, b=10))
                st.plotly_chart(fig_cat, use_container_width=True)

        with perf_col2:
            st.subheader("Performance by Region")
            reg_df, reg_sql = query_dimension_breakdown(con, "region", table_name="active_retail")
            if not reg_df.empty:
                fig_reg = px.bar(
                    reg_df,
                    x="region",
                    y="estimated_profit",
                    color="profit_margin_pct",
                    color_continuous_scale="Blues",
                    text="estimated_profit",
                    labels={"estimated_profit": "Profit ($)", "profit_margin_pct": "Margin %", "region": "Region"}
                )
                fig_reg.update_traces(texttemplate="$%{text:,.0f}", textposition="outside")
                fig_reg.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=350, margin=dict(l=10, r=10, t=20, b=10))
                st.plotly_chart(fig_reg, use_container_width=True)

        # Cross-tabulation Heatmap: Category x Region
        st.subheader("Category × Region Profitability Cross-Tabulation")
        cross_df, cross_sql = query_cross_tabulation(con, table_name="active_retail", metric_col="estimated_profit")
        if not cross_df.empty:
            fig_heat = px.imshow(
                cross_df,
                text_auto=True,
                aspect="auto",
                color_continuous_scale="RdYlGn",
                labels=dict(x="Region", y="Category", color="Profit ($)")
            )
            fig_heat.update_layout(height=320, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_heat, use_container_width=True)

        # Transparent SQL Query Inspector
        with st.expander("💻 View Executed DuckDB SQL Statements"):
            st.code(monthly_sql, language="sql")


# =========================================================
# TAB 4: ROOT-CAUSE INVESTIGATION
# =========================================================
with tab_root_cause:
    st.markdown("<div class=\"section-header\">Root-Cause Analysis & Performance Variance</div>", unsafe_allow_html=True)
    st.write(
        "Isolate business performance changes between any two comparative periods. "
        "ProfitLens decomposes total profit delta into volume, net price realization, COGS, and operating logistics expenses."
    )
    
    st.info("💡 **Methodology Notice**: Descriptive findings quantify segment association with variations. A segment associated with a decline is not automatically its sole causal driver.")
    
    # Period selector for comparison
    available_years = sorted(df_raw["order_date"].dt.year.dropna().unique().tolist()) if ("order_date" in df_raw.columns and not df_raw.empty) else [2023, 2024]
    if len(available_years) < 2:
        available_years = available_years + available_years  # Support single-year datasets gracefully

    rc_col1, rc_col2 = st.columns(2)
    with rc_col1:
        st.markdown("**Baseline Period (Prior)**")
        prior_year = st.selectbox("Baseline Year:", available_years, index=0, key="rc_prior_year_select")
        prior_data = pd.DataFrame(df_raw[df_raw["order_date"].dt.year == prior_year])
    with rc_col2:
        st.markdown("**Comparison Period (Current)**")
        curr_year = st.selectbox("Comparison Year:", available_years, index=min(1, len(available_years)-1), key="rc_curr_year_select")
        curr_data = pd.DataFrame(df_raw[df_raw["order_date"].dt.year == curr_year])

    if prior_year == curr_year:
        st.info("ℹ️ Select two different years above to analyze period-over-period variance decomposition.")
    elif prior_data.empty or curr_data.empty:
        st.warning("Insufficient period data for root-cause comparison.")
    else:
        decomp = decompose_profit_variance(prior_data, curr_data)
        
        st.subheader(f"Total Profit Variance Decomposition: {prior_year} vs {curr_year}")
        
        decomp_c1, decomp_c2, decomp_c3, decomp_c4 = st.columns(4)
        decomp_c1.metric("Baseline Profit", f"${decomp.prior_profit:,.0f}")
        decomp_c2.metric("Comparison Profit", f"${decomp.current_profit:,.0f}")
        decomp_c3.metric("Total Profit Variance", f"${decomp.total_profit_change:,.0f}", delta=f"{decomp.total_profit_change:,.0f}")
        decomp_c4.metric("Variance Explanability", f"{safe_divide((decomp.total_profit_change - decomp.unexplained_residual), decomp.total_profit_change)*100:.1f}%")

        # Waterfall of the Variance Breakdown
        var_x = [f"{prior_year} Profit", "Volume Effect", "Price/Discount Effect", "COGS Acquisition Effect", "Operating Expense Effect", f"{curr_year} Profit"]
        var_y = [
            decomp.prior_profit,
            decomp.volume_effect,
            decomp.price_realization_effect,
            decomp.cost_cogs_effect,
            decomp.operating_expense_effect,
            decomp.current_profit
        ]
        var_measure = ["relative", "relative", "relative", "relative", "relative", "total"]

        fig_var = go.Figure(go.Waterfall(
            orientation="v",
            measure=var_measure,
            x=var_x,
            y=var_y,
            textposition="outside",
            text=[f"${abs(v):,.0f}" for v in var_y],
            connector={"line": {"color": "#94a3b8"}},
            decreasing={"marker": {"color": "#ef4444"}},
            increasing={"marker": {"color": "#10b981"}},
            totals={"marker": {"color": "#1e3a8a"}}
        ))
        fig_var.update_layout(
            height=380,
            margin=dict(l=20, r=20, t=30, b=20),
            plot_bgcolor="white",
            paper_bgcolor="white",
            yaxis=dict(title="Profit Impact USD ($)", gridcolor="#f1f5f9")
        )
        st.plotly_chart(fig_var, use_container_width=True)

        # Contributor Ranking
        st.subheader("Segment Driver Ranking")
        dim_choice = st.radio("Decompose by Dimension:", ["product_category", "region"], horizontal=True)
        
        pos_drivers, neg_drivers = identify_top_contributors(prior_data, curr_data, dimension_col=dim_choice, top_n=5)
        
        rank_col1, rank_col2 = st.columns(2)
        with rank_col1:
            st.markdown("🟢 **Top Positive Contributors (Profit Growth)**")
            if pos_drivers:
                pos_records = [{
                    "Segment": d.segment_value,
                    "Prior Profit": f"${d.prior_profit:,.0f}",
                    "Current Profit": f"${d.current_profit:,.0f}",
                    "Profit Delta": f"+${d.profit_change:,.0f}",
                    "Margin Shift": f"{d.margin_change_pts:+.1f} pts"
                } for d in pos_drivers]
                st.dataframe(pd.DataFrame(pos_records), hide_index=True, use_container_width=True)
            else:
                st.caption("No segments demonstrated positive profit expansion.")

        with rank_col2:
            st.markdown("🔴 **Top Negative Detractors (Margin / Profit Drag)**")
            if neg_drivers:
                neg_records = [{
                    "Segment": d.segment_value,
                    "Prior Profit": f"${d.prior_profit:,.0f}",
                    "Current Profit": f"${d.current_profit:,.0f}",
                    "Profit Delta": f"-${abs(d.profit_change):,.0f}",
                    "Margin Shift": f"{d.margin_change_pts:+.1f} pts"
                } for d in neg_drivers]
                st.dataframe(pd.DataFrame(neg_records), hide_index=True, use_container_width=True)
            else:
                st.caption("No segments demonstrated negative profit contractions.")

        # Analytical Narratives
        st.markdown("**Evidence-Based Observations**")
        all_narratives = [d.analytical_narrative for d in (pos_drivers + neg_drivers)]
        for narr in all_narratives:
            st.markdown(f"- {narr}")


# =========================================================
# TAB 5: WHAT-IF SCENARIO SIMULATOR
# =========================================================
with tab_simulator:
    st.markdown("<div class=\"section-header\">Strategic Decision Simulator (What-If Modeling)</div>", unsafe_allow_html=True)
    st.write(
        "Simulate the financial impact of commercial decisions on the active baseline dataset. "
        "Outputs are sensitivity estimates computed using price elasticity and variable cost behavior."
    )
    
    if df_filtered.empty:
        st.warning("⚠️ No data available for simulation. Please select active filters in the sidebar.")
    else:
        # Simulator Controls
        sim_col1, sim_col2 = st.columns([1, 2])
        
        with sim_col1:
            st.subheader("Decision Levers")
            
            p_change = st.slider("List Price Adjustment (%):", min_value=-30.0, max_value=30.0, value=0.0, step=1.0)
            d_change = st.slider("Promotional Discount Rate Change (%):", min_value=-50.0, max_value=50.0, value=0.0, step=5.0, help="E.g., -20% reduces existing discount amounts by a fifth.")
            v_shock = st.slider("Exogenous Demand Volume Shift (%):", min_value=-30.0, max_value=30.0, value=0.0, step=1.0, help="Independent market trend or ad-driven demand variation.")
            cogs_change = st.slider("Supplier Cost (COGS) Change (%):", min_value=-20.0, max_value=30.0, value=0.0, step=1.0)
            ship_change = st.slider("Carrier Shipping Rate Change (%):", min_value=-20.0, max_value=40.0, value=0.0, step=2.0)
            
            with st.expander("⚙️ Advanced Elasticity & Cost Structure Assumptions"):
                elasticity = st.slider("Price Elasticity of Demand (PED):", min_value=-3.0, max_value=0.0, value=-1.2, step=0.1, help="Demand response: -1.2 means +1% net price causes -1.2% volume decrease.")
                fixed_mktg = st.slider("Fixed Share of Marketing Spend (%):", min_value=0, max_value=100, value=70, step=5, help="Portion of ad budget unaffected by transaction volume changes.")
            
            assumptions = ScenarioAssumptions(
                price_change_pct=p_change,
                discount_change_pct=d_change,
                volume_shock_pct=v_shock,
                cogs_change_pct=cogs_change,
                shipping_cost_change_pct=ship_change,
                price_elasticity_of_demand=elasticity,
                fixed_marketing_share=fixed_mktg / 100.0
            )

        with sim_col2:
            st.subheader("Simulated Outcome vs Baseline")
            sim_result = simulate_scenario(df_filtered, assumptions)
            
            # Top outcome cards
            sc1, sc2, sc3 = st.columns(3)
            base_p = sim_result.baseline_summary.estimated_profit
            sim_p = sim_result.simulated_summary.estimated_profit
            p_delta = sim_p - base_p
            p_pct = sim_result.outcomes["Estimated Profit"].percentage_change
            
            sc1.metric(
                "Simulated Profit (Est.)",
                f"${sim_p:,.0f}",
                delta=f"${p_delta:+,.0f} ({p_pct:+.1f}%)" if p_pct is not None else None
            )
            sc2.metric(
                "Simulated Net Revenue",
                f"${sim_result.simulated_summary.net_billed_revenue:,.0f}",
                delta=f"${sim_result.simulated_summary.net_billed_revenue - sim_result.baseline_summary.net_billed_revenue:+,.0f}"
            )
            sc3.metric(
                "Simulated Profit Margin",
                f"{sim_result.simulated_summary.profit_margin_pct:.1f}%",
                delta=f"{sim_result.simulated_summary.profit_margin_pct - sim_result.baseline_summary.profit_margin_pct:+.1f} pts"
            )

            st.caption(f"ℹ️ **Executive Simulation Note:** {sim_result.narrative_summary}")

            # Comparison Table
            st.dataframe(sim_result.to_dataframe(), hide_index=True, use_container_width=True)

            # Visual Comparison Chart
            fig_sim = go.Figure()
            comp_metrics = ["Net Billed Revenue", "Product Contribution", "Operating Expenses", "Estimated Profit"]
            fig_sim.add_trace(go.Bar(
                name="Baseline",
                x=comp_metrics,
                y=[sim_result.baseline_summary.net_billed_revenue, sim_result.baseline_summary.product_contribution, sim_result.baseline_summary.operating_expenses, sim_result.baseline_summary.estimated_profit],
                marker_color="#94a3b8"
            ))
            fig_sim.add_trace(go.Bar(
                name="Simulated Scenario",
                x=comp_metrics,
                y=[sim_result.simulated_summary.net_billed_revenue, sim_result.simulated_summary.product_contribution, sim_result.simulated_summary.operating_expenses, sim_result.simulated_summary.estimated_profit],
                marker_color="#2563eb"
            ))
            fig_sim.update_layout(
                barmode="group",
                height=320,
                margin=dict(l=10, r=10, t=20, b=10),
                plot_bgcolor="white",
                paper_bgcolor="white",
                yaxis=dict(title="USD ($)", gridcolor="#f1f5f9"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_sim, use_container_width=True)


# =========================================================
# TAB 6: EXECUTIVE REPORT & EXPORT
# =========================================================
with tab_report:
    st.markdown("<div class=\"section-header\">Executive Decision Report & Export</div>", unsafe_allow_html=True)
    st.write(
        "Compile live findings, data-quality audit logs, root-cause evidence, and simulation estimates into a standardized "
        "executive briefing. Ready for distribution to leadership and stakeholders."
    )
    
    if df_filtered.empty:
        st.warning("Cannot generate report: No data matches active filters.")
    else:
        # Prepare components for report
        rep_summary = calculate_financial_summary(df_filtered)
        rep_val = validate_dataset(df_raw)
        
        # Get date strings
        rep_start = df_filtered["order_date"].min().strftime("%Y-%m-%d")
        rep_end = df_filtered["order_date"].max().strftime("%Y-%m-%d")
        
        # Scenario result from tab 5 (if levers were used, otherwise baseline)
        if sim_result is not None:
            rep_sim = sim_result
        else:
            rep_sim = simulate_scenario(df_filtered)

        # Include root-cause variance and driver findings in report if prior period exists
        r_decomp = None
        r_pos, r_neg = None, None
        if df_prior is not None and not df_prior.empty and not df_filtered.empty:
            try:
                r_decomp = decompose_profit_variance(df_prior, df_filtered)
                r_pos, r_neg = identify_top_contributors(df_prior, df_filtered, dimension_col="product_category", top_n=3)
            except Exception:
                pass

        # Build Markdown and HTML report
        report_markdown = generate_markdown_report(
            summary=rep_summary,
            validation_report=rep_val,
            start_date=rep_start,
            end_date=rep_end,
            simulation_result=rep_sim,
            pos_contributors=r_pos,
            neg_contributors=r_neg,
            variance_decomp=r_decomp
        )
        report_html = generate_html_report(report_markdown)

        # Download Buttons
        dl_col1, dl_col2, dl_col3 = st.columns(3)
        with dl_col1:
            st.download_button(
                label="📥 Download Executive Briefing (Markdown .md)",
                data=report_markdown,
                file_name=f"ProfitLens_Executive_Report_{rep_start}_{rep_end}.md",
                mime="text/markdown",
                use_container_width=True
            )
        with dl_col2:
            st.download_button(
                label="🌐 Download Standalone Briefing (HTML .html)",
                data=report_html,
                file_name=f"ProfitLens_Executive_Report_{rep_start}_{rep_end}.html",
                mime="text/html",
                use_container_width=True
            )
        with dl_col3:
            # Download filtered underlying table as CSV
            csv_data = df_filtered.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📊 Export Filtered Dataset (CSV .csv)",
                data=csv_data,
                file_name=f"ProfitLens_Filtered_Data_{rep_start}_{rep_end}.csv",
                mime="text/csv",
                use_container_width=True
            )

        st.divider()
        st.subheader("Live Report Preview")
        st.markdown(report_markdown)
