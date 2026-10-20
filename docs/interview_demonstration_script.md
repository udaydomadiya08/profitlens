# ProfitLens: Interview Demonstration Script & Walkthrough

**Role Context:** Lead Business Analyst / Analytics Engineer  
**Presentation Duration:** ~7–10 Minutes  
**Demonstration Goal:** Prove quantitative rigor, business problem-solving, SQL fluency, data quality paranoia, and executive communication.

---

## 1. Opening: Framing the Business Problem (1 Minute)

> *"In many retail and e-commerce companies, leadership celebrates top-line revenue growth while bottom-line net profit quietly compresses. I built ProfitLens to solve this exact problem: to take an analyst from raw transactional data to actionable executive strategy."*

> *"ProfitLens isn't a mock UI or a toy dashboard. It's an end-to-end analytical application with a headless Python calculation engine, an in-memory DuckDB columnar SQL backend, an automated data quality auditor, a managerial variance decomposition model, and an elasticity-driven what-if decision simulator."*

---

## 2. Ingestion & Data Quality Paranoia (1.5 Minutes)

**Action:** Open the **🛡️ Data Quality & Audit** tab.

> *"Rule number one of quantitative analysis is 'garbage in, garbage out.' Before calculating a single KPI, ProfitLens runs an automated integrity suite across 12 distinct analytical dimensions.*
> 
> *Notice our audit scorecard:
> 1. It audits for missing required schema columns.
> 2. It inspects non-positive quantities ($q \le 0$) and negative unit prices or unit costs.
> 3. It checks for financial anomalies like promotional discounts exceeding the unit price.
> 4. It flags duplicate surrogate keys and identifies multi-line orders where order-level logistics costs might be accidentally double-counted.
> 5. Most importantly, it outputs actionable remediation messages rather than silent failures."*

---

## 3. Executive Overview & P&L Mechanics (1.5 Minutes)

**Action:** Switch to the **📈 Executive Overview** tab.

> *"Once data is validated, we review the top-level business health. Here we see our primary KPIs with automated period-over-period comparisons: Net Billed Revenue, Estimated Profit, Profit Margin, Contribution Margin, Average Order Value (AOV), and Return Rate.*
> 
> *Notice the P&L Waterfall: We don't make the mistake of equating gross sales with profit. We explicitly bridge Gross Revenue $\rightarrow$ Deduct Promotional Discounts $\rightarrow$ Net Billed Revenue $\rightarrow$ Deduct COGS $\rightarrow$ Product Contribution $\rightarrow$ Deduct Shipping and Marketing Expenses $\rightarrow$ Estimated Operating Profit.*
> 
> *And if executive leadership wants to isolate recognized revenue from refunded returns, a single toggle dynamically recalibrates all downstream metrics."*

---

## 4. Columnar SQL & Multi-Dimensional Deep Dive (2 Minutes)

**Action:** Switch to the **📊 Performance & SQL Analytics** tab.

> *"To analyze large transactional volumes efficiently, ProfitLens integrates DuckDB in-memory. 
> 
> Look at the monthly trajectory: Net revenue grew through 2024, but our profit margin peaked mid-year and began to compress in Q3 and Q4.
> 
> When we examine our Category and Regional breakdowns and our Cross-Tabulation Heatmap (Category $\times$ Region), we see an immediate signal: The South region in Apparel and Electronics is experiencing notable margin erosion.*
> 
> *As an analyst, I believe in SQL transparency. If we expand the 'View Executed DuckDB SQL Statements' section, you can see the exact, parameterized SQL queries powering the dashboard."*

---

## 5. Root-Cause: Managerial Variance Decomposition (2 Minutes)

**Action:** Switch to the **🔬 Root-Cause Investigation** tab.

> *"Here is where descriptive reporting turns into root-cause diagnosis. A common mistake analysts make is confusing correlation with causation. A segment associated with a profit dip isn't automatically its sole driver.*
> 
> *To explain what actually happened between 2023 and 2024, ProfitLens performs a formal managerial accounting variance decomposition:*
> 1. *Volume Effect: How much profit did unit scale expansion contribute? (Positive)*
> 2. *Net Price / Discount Realization Effect: Did higher discounts erode realized prices? (Negative)*
> 3. *COGS Acquisition Effect: Did wholesale product costs rise?*
> 4. *Operating Logistics Expense Effect: Did carrier shipping costs spike? (Steep negative)*
> 
> *Our segment contributor ranking confirms that the South region was the largest profit drag: aggressive promotional discounting coupled with carrier shipping rate spikes wiped out the volume gains."*

---

## 6. What-If Decision Simulator & Executive Action (1.5 Minutes)

**Action:** Switch to the **🎲 What-If Simulator** and then the **📄 Executive Report** tab.

> *"Knowing the root cause is only half the battle. Leadership needs to know: 'What should we do next?'*
> 
> *In the What-If Simulator, we can test corrective business decisions:*
> - *What if we rationalize discounts by -20%?*
> - *Using our Price Elasticity of Demand lever ($\epsilon = -1.2$), the simulator models the induced volume decline.*
> - *What if we simultaneously renegotiate carrier shipping contracts to reduce shipping rates by 8%?*
> 
> *Instantly, we see that profit rebounds by over 14%, and profit margins expand by +3.2 percentage points.*
> 
> *Finally, under the Executive Report tab, ProfitLens compiles the entire narrative—baseline scorecard, data audit, root-cause evidence, and strategic recommendations—into a downloadable executive briefing in Markdown, standalone HTML, or underlying filtered CSV ready for stakeholder review."*

---

## 7. Closing & Technical Rigor Summary

> *"To ensure enterprise-grade reliability, the entire business logic is tested with 26 automated unit tests via pytest, verifying every financial formula against hand-calculated mathematical proofs, testing zero denominators, and ensuring equivalence between DuckDB SQL and Pandas.*
> 
> *Thank you. I'm excited to dive into any architectural, SQL, or financial modeling details you'd like to explore."*
