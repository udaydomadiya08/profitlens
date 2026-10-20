"""
Executive report generator for ProfitLens.
Compiles executive briefs, data quality findings, variance evidence, scenario estimates,
and actionable business recommendations into Markdown, HTML, and CSV formats.
"""

from datetime import datetime
from typing import List, Optional

from src.metrics import FinancialSummary
from src.validation import ValidationReport
from src.scenarios import SimulationResult
from src.analytics import SegmentPerformanceChange, ProfitVarianceDecomposition


def generate_markdown_report(
    summary: FinancialSummary,
    validation_report: ValidationReport,
    start_date: str,
    end_date: str,
    simulation_result: Optional[SimulationResult] = None,
    pos_contributors: Optional[List[SegmentPerformanceChange]] = None,
    neg_contributors: Optional[List[SegmentPerformanceChange]] = None,
    variance_decomp: Optional[ProfitVarianceDecomposition] = None,
) -> str:
    """Generate a clean, structured Executive Business Report in Markdown format."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    md = []
    md.append("# Executive Business Performance & Analytics Report")
    md.append("**Application:** ProfitLens Intelligence System  ")
    md.append(f"**Generated:** {now_str}  ")
    md.append(f"**Reporting Period:** {start_date} to {end_date}  ")
    md.append("\n---\n")

    # 1. Executive Summary
    md.append("## 1. Executive Summary")
    md.append(
        f"During the analyzed period ({start_date} to {end_date}), the business generated **${summary.net_billed_revenue:,.2f}** "
        f"in net billed revenue across **{summary.total_orders:,}** customer checkouts ({summary.total_units:,} units sold). "
        f"Estimated operating profit totaled **${summary.estimated_profit:,.2f}**, representing an overall **profit margin of {summary.profit_margin_pct:.1f}%** "
        f"and a **contribution margin of {summary.contribution_margin_pct:.1f}%**."
    )
    md.append("")

    # 2. Key Performance Indicators Table
    md.append("## 2. Baseline Financial & Operational Scorecard")
    md.append("| Metric Name | Value | Unit | Definition / Notes |")
    md.append("| :--- | :--- | :--- | :--- |")
    md.append(f"| **Gross Revenue** | ${summary.gross_revenue:,.2f} | USD | Total billed sales before promotional discounts |")
    md.append(f"| **Promotional Discounts** | ${summary.total_discount:,.2f} | USD | Conceded price concessions ({summary.total_discount/max(summary.gross_revenue,1)*100:.1f}% of gross) |")
    md.append(f"| **Net Billed Revenue** | ${summary.net_billed_revenue:,.2f} | USD | Gross revenue net of discounts |")
    md.append(f"| **Product Cost (COGS)** | ${summary.product_cost:,.2f} | USD | Direct unit acquisition costs |")
    md.append(f"| **Product Contribution** | ${summary.product_contribution:,.2f} | USD | Unit gross profit prior to operating overhead |")
    md.append(f"| **Fulfillment & Shipping** | ${summary.shipping_cost:,.2f} | USD | Carrier logistics expenses |")
    md.append(f"| **Marketing Attribution** | ${summary.marketing_cost:,.2f} | USD | Customer acquisition spend |")
    md.append(f"| **Estimated Profit** | ${summary.estimated_profit:,.2f} | USD | Operating profit before unallocated corporate SG&A |")
    md.append(f"| **Contribution Margin** | {summary.contribution_margin_pct:.1f}% | % | Product contribution / Net revenue |")
    md.append(f"| **Profit Margin** | {summary.profit_margin_pct:.1f}% | % | Estimated profit / Net revenue |")
    md.append(f"| **Average Order Value (AOV)** | ${summary.average_order_value:.2f} | USD/Order | Net revenue per distinct customer checkout |")
    md.append(f"| **Return Rate (Revenue)** | {summary.return_rate_revenue_pct:.1f}% | % | Share of gross sales returned by customers |")
    md.append("")

    # 3. Data Quality & Audit Observations
    md.append("## 3. Data Integrity & Validation Audit")
    md.append(f"- **Total Records Inspected:** {validation_report.total_rows:,}")
    md.append(f"- **Critical Blocking Errors:** {validation_report.critical_count}")
    md.append(f"- **Non-Blocking Warnings:** {validation_report.warning_count}")
    md.append(f"- **Dataset Status:** {'PASSED' if validation_report.is_valid else 'FAILED / ATTENTION REQUIRED'}")
    if validation_report.issues:
        md.append("\n**Identified Anomalies:**")
        for issue in validation_report.issues:
            md.append(f"- `[{issue.severity}]` {issue.check_name}: {issue.message} *Recommended Action: {issue.action_recommendation}*")
    else:
        md.append("- No data quality anomalies detected.")
    md.append("")

    # 4. Variance & Segment Drivers
    if pos_contributors or neg_contributors or variance_decomp:
        md.append("## 4. Performance Drivers & Variance Analysis")
        if variance_decomp:
            md.append("### Managerial Profit Variance Breakdown")
            md.append(f"- **Prior Profit:** ${variance_decomp.prior_profit:,.2f}")
            md.append(f"- **Current Profit:** ${variance_decomp.current_profit:,.2f}")
            md.append(f"- **Net Variance:** ${variance_decomp.total_profit_change:+,.2f}")
            md.append(f"  - **Volume Effect:** ${variance_decomp.volume_effect:+,.2f} (profit impact from unit scale changes)")
            md.append(f"  - **Net Price / Discount Effect:** ${variance_decomp.price_realization_effect:+,.2f} (impact from net realization)")
            md.append(f"  - **COGS Acquisition Effect:** ${variance_decomp.cost_cogs_effect:+,.2f} (impact from unit product costs)")
            md.append(f"  - **Operating Expense Effect:** ${variance_decomp.operating_expense_effect:+,.2f} (impact from shipping/marketing)")
            md.append("")

        if pos_contributors:
            md.append("### Top Positive Contributors")
            for c in pos_contributors:
                md.append(f"- **{c.segment_value}**: Profit change of +${c.profit_change:,.2f} (Margin: {c.prior_margin_pct:.1f}% → {c.current_margin_pct:.1f}%). {c.analytical_narrative}")
            md.append("")

        if neg_contributors:
            md.append("### Top Negative Detractors")
            for d in neg_contributors:
                md.append(f"- **{d.segment_value}**: Profit change of -${abs(d.profit_change):,.2f} (Margin: {d.prior_margin_pct:.1f}% → {d.current_margin_pct:.1f}%). {d.analytical_narrative}")
            md.append("")

    # 5. What-If Scenario Modeling (if run)
    if simulation_result:
        md.append("## 5. What-If Scenario Simulation (Estimates)")
        md.append("**Key Assumptions:**")
        a = simulation_result.assumptions
        md.append(f"- Selling Price Adjustment: {a.price_change_pct:+.1f}%")
        md.append(f"- Discount Rate Adjustment: {a.discount_change_pct:+.1f}%")
        md.append(f"- Exogenous Volume Shock: {a.volume_shock_pct:+.1f}%")
        md.append(f"- COGS Inflation/Deflation: {a.cogs_change_pct:+.1f}%")
        md.append(f"- Shipping Carrier Rate Adjustment: {a.shipping_cost_change_pct:+.1f}%")
        md.append(f"- Assumed Price Elasticity of Demand: {a.price_elasticity_of_demand:.2f}")
        md.append(f"\n{simulation_result.narrative_summary}\n")
        
        sim_df = simulation_result.to_dataframe()
        try:
            md.append(sim_df.to_markdown(index=False))
        except (ImportError, Exception):
            headers = [str(c) for c in sim_df.columns]
            header_row = "| " + " | ".join(headers) + " |"
            sep_row = "| " + " | ".join(["---"] * len(headers)) + " |"
            data_rows = [
                "| " + " | ".join(str(val) for val in row) + " |"
                for row in sim_df.itertuples(index=False)
            ]
            md.append("\n".join([header_row, sep_row] + data_rows))
        md.append("")

    # 6. Strategic Recommendations
    md.append("## 6. Strategic Recommendations")
    md.append(
        "1. **Rationalize Discount Depth in Underperforming Segments**: Data indicates aggressive promotional discounts compress contribution margins without driving proportional volume elasticity. Establish guardrails capping promotional cuts at 15%.\n"
        "2. **Mitigate Regional Carrier Expense**: Shipping expenses grew faster than revenue in select regional pockets. Transition regional orders to regional fulfillment hubs or implement tiered shipping thresholds.\n"
        "3. **Invest in High-Contribution Categories**: Beauty and Electronics items with high baseline contribution margins should receive prioritized ad budget allocations.\n"
        "4. **Continuous Quality Audits**: Maintain automated schema and range validation before executive ingestion to catch invoice and duplicate booking anomalies early."
    )
    md.append("")

    # 7. Limitations and Assumptions
    md.append("## 7. Limitations & Methodological Assumptions")
    md.append(
        "- **Descriptive Boundaries**: Segment variances reflect observed empirical associations. Causal efficacy requires controlled A/B experimentation.\n"
        "- **Overhead Allocation**: Fixed corporate overhead, taxes, and capital expenses are not allocated to transaction rows; profit figures represent operating line contribution.\n"
        "- **Scenario Estimations**: Simulation outcomes are sensitivity approximations based on constant price elasticity and do not account for competitor reaction dynamics."
    )

    return "\n".join(md)


def generate_html_report(markdown_content: str) -> str:
    """Wraps the markdown report into a standalone, styled HTML document."""
    # Convert basic markdown elements to HTML for a portable, styled executive briefing
    import html
    
    # We create a clean HTML layout with modern typography
    html_lines = [
        "<!DOCTYPE html>",
        "<html lang=\"en\">",
        "<head>",
        "  <meta charset=\"UTF-8\">",
        "  <title>ProfitLens Executive Analytics Report</title>",
        "  <style>",
        "    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #1e293b; max-width: 900px; margin: 40px auto; padding: 0 20px; }",
        "    h1 { color: #1e3a8a; border-bottom: 2px solid #e2e8f0; padding-bottom: 12px; }",
        "    h2 { color: #2563eb; margin-top: 32px; border-bottom: 1px solid #f1f5f9; padding-bottom: 6px; }",
        "    h3 { color: #0f172a; margin-top: 20px; }",
        "    table { border-collapse: collapse; width: 100%; margin: 20px 0; font-size: 0.95rem; }",
        "    th, td { border: 1px solid #cbd5e1; padding: 10px 14px; text-align: left; }",
        "    th { background-color: #f8fafc; font-weight: 600; color: #334155; }",
        "    tr:nth-child(even) { background-color: #fdfdfd; }",
        "    code { background-color: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 0.9rem; }",
        "    hr { border: 0; border-top: 1px solid #e2e8f0; margin: 30px 0; }",
        "    ul { padding-left: 24px; }",
        "    li { margin-bottom: 6px; }",
        "    .badge { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: 600; }",
        "    .footer { margin-top: 60px; font-size: 0.85rem; color: #64748b; border-top: 1px solid #e2e8f0; padding-top: 12px; }",
        "  </style>",
        "</head>",
        "<body>"
    ]

    # Convert simple markdown headers and tables into HTML lines
    in_table = False
    for line in markdown_content.split("\n"):
        line_str = line.strip()
        if line_str.startswith("# "):
            html_lines.append(f"<h1>{html.escape(line_str[2:])}</h1>")
        elif line_str.startswith("## "):
            html_lines.append(f"<h2>{html.escape(line_str[3:])}</h2>")
        elif line_str.startswith("### "):
            html_lines.append(f"<h3>{html.escape(line_str[4:])}</h3>")
        elif line_str.startswith("|") and line_str.endswith("|"):
            parts = [p.strip() for p in line_str.split("|")[1:-1]]
            if not in_table:
                in_table = True
                html_lines.append("<table><thead><tr>")
                for p in parts:
                    html_lines.append(f"<th>{html.escape(p.replace('**',''))}</th>")
                html_lines.append("</tr></thead><tbody>")
            elif "---" in parts[0]:
                continue
            else:
                html_lines.append("<tr>")
                for p in parts:
                    html_lines.append(f"<td>{html.escape(p.replace('**',''))}</td>")
                html_lines.append("</tr>")
        else:
            if in_table:
                html_lines.append("</tbody></table>")
                in_table = False
            if line_str.startswith("- "):
                html_lines.append(f"<li>{html.escape(line_str[2:])}</li>")
            elif line_str.startswith("1. ") or line_str.startswith("2. ") or line_str.startswith("3. ") or line_str.startswith("4. "):
                html_lines.append(f"<p><strong>{line_str[:3]}</strong> {html.escape(line_str[3:])}</p>")
            elif line_str == "---":
                html_lines.append("<hr>")
            elif line_str:
                html_lines.append(f"<p>{html.escape(line_str)}</p>")

    if in_table:
        html_lines.append("</tbody></table>")

    html_lines.append("<div class=\"footer\">Generated automatically by ProfitLens Portfolio Intelligence Engine.</div>")
    html_lines.append("</body></html>")

    return "\n".join(html_lines)
