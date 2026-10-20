# ProfitLens Metric Definitions & Data Model

This document establishes the official data dictionary, financial formulas, granularity rules, and edge-case treatment for ProfitLens.

---

## 1. Data Dictionary

The standard dataset granularity is **Order-Line Level** (one row per SKU ordered within a customer checkout).

| Column Name | Data Type | Units / Format | Granularity | Description & Constraints |
| :--- | :--- | :--- | :--- | :--- |
| `order_id` | String / Integer | Identifier | Order | Unique identifier for customer checkout. Multiple rows may share an `order_id` if an order contains multiple SKUs. |
| `line_item_id` | String / Integer | Identifier | Line Item | Primary key for the specific item row within an order. |
| `order_date` | Date | `YYYY-MM-DD` | Order | Date checkout occurred. |
| `customer_id` | String | Identifier | Customer | Unique identifier of purchasing customer. |
| `region` | String | Categorical | Order | Geographic market (e.g., `North`, `South`, `East`, `West`). |
| `product_category` | String | Categorical | Line Item | High-level taxonomy (e.g., `Electronics`, `Apparel`, `Home & Kitchen`, `Beauty`, `Sports`). |
| `product_name` | String | Text | Line Item | Name/Description of SKU. |
| `quantity` | Integer | Units | Line Item | Number of units purchased. Must be strictly $\ge 1$. |
| `unit_price` | Float | USD ($) | Line Item | Undiscounted list price per single unit. Must be $> 0$. |
| `unit_cost` | Float | USD ($) | Line Item | Direct product acquisition cost (COGS) per single unit. Must be $> 0$. |
| `discount` | Float | USD ($) | Line Item | Discount amount per unit. Constraint: $0 \le \text{discount} \le \text{unit\_price}$. |
| `marketing_cost` | Float | USD ($) | Line Item | Allocated customer acquisition/campaign expense attributed to this line item. |
| `shipping_cost` | Float | USD ($) | Line Item | Allocated fulfillment and delivery cost attributed to this line item. |
| `returned` | Boolean / Int | `0` or `1` / True/False | Line Item | Indicates whether customer returned the item post-delivery. |
| `order_status` | String | Categorical | Order / Line | Status: `Completed`, `Returned`, or `Cancelled`. |

---

## 2. Metric Formulations

### 2.1 Core Revenue & Cost Metrics

1. **Gross Revenue (Line-Item)**:
   $$\text{Gross Revenue} = \text{quantity} \times \text{unit\_price}$$
   *Represents headline billed sales before promotional discounts.*

2. **Total Discount Amount (Line-Item)**:
   $$\text{Discount Amount} = \text{quantity} \times \text{discount}$$

3. **Net Billed Revenue (Line-Item)**:
   $$\text{Net Billed Revenue} = \text{Gross Revenue} - \text{Discount Amount} = \text{quantity} \times (\text{unit\_price} - \text{discount})$$

4. **Product Cost (COGS)**:
   $$\text{Product Cost} = \text{quantity} \times \text{unit\_cost}$$

5. **Product Contribution (Gross Profit)**:
   $$\text{Product Contribution} = \text{Net Billed Revenue} - \text{Product Cost}$$
   *Measures unit economics prior to operating and fulfillment expenses.*

6. **Allocated Operating Expenses**:
   $$\text{Operating Expenses} = \text{marketing\_cost} + \text{shipping\_cost}$$

7. **Estimated Profit**:
   $$\text{Estimated Profit} = \text{Product Contribution} - \text{Operating Expenses}$$
   *Note: This is labeled 'Estimated Profit' because corporate overhead (SG&A, tax, interest) is not captured at line granularity.*

---

## 3. Margin & Operational Metrics

1. **Contribution Margin (%)**:
   $$\text{Contribution Margin} = \frac{\text{Product Contribution}}{\text{Net Billed Revenue}} \times 100\%$$
   *(Defined when $\text{Net Billed Revenue} > 0$; otherwise $0\%$.)*

2. **Estimated Profit Margin (%)**:
   $$\text{Profit Margin} = \frac{\text{Estimated Profit}}{\text{Net Billed Revenue}} \times 100\%$$

3. **Average Order Value (AOV)**:
   $$\text{AOV} = \frac{\sum \text{Net Billed Revenue}}{\text{Count of Distinct } \text{order\_id}}$$

4. **Units Sold**:
   $$\text{Units Sold} = \sum \text{quantity}$$

5. **Return Rate (%)**:
   $$\text{Return Rate} = \frac{\sum (\text{Gross Revenue of Returned Items})}{\sum \text{Gross Revenue}} \times 100\%$$
   *(Can also be reported as Unit Return Rate: $\frac{\text{Returned Units}}{\text{Total Units Sold}} \times 100\%$. ProfitLens displays both financial and unit return metrics.)*

6. **Period-over-Period Growth Rate (%)**:
   $$\text{Growth Rate} = \frac{\text{Metric}_{t} - \text{Metric}_{t-1}}{|\text{Metric}_{t-1}|} \times 100\%$$
   *(If $\text{Metric}_{t-1} = 0$, growth is marked as undefined / $N/A$.)*

---

## 4. Policy on Returns, Cancellations, and Double-Counting

### 4.1 Returns Treatment
- Items marked as `returned = True` or `order_status = 'Returned'` represent merchandise returned by the customer for a full refund.
- **Financial impact**:
  - `Net Recognized Revenue` = $\text{Net Billed Revenue} - \text{Refund Amount}$.
  - Returned units are physically restocked or salvaged, but fulfillment shipping cost is **sunk** and non-refundable.
  - In ProfitLens, dashboard toggles allow the analyst to view **Gross Activity** vs **Net Recognized Performance** (post-return adjustments).

### 4.2 Cancellations Treatment
- Orders marked as `order_status = 'Cancelled'` were cancelled prior to shipping and billing.
- Cancellations are excluded from fulfilled sales, shipping costs, and revenue metrics, but retained for operational funnel/cancellation rate analysis.

### 4.3 Preventing Order-Level Cost Double Counting
- If shipping or marketing expenses are recorded at the order level, summing line-items directly would artificially inflate these costs $N$-fold (where $N$ is the number of line items).
- In ProfitLens:
  - If a dataset provides order-level costs, `data_loader.py` proportions the cost across line items based on line revenue share, OR aggregations use `DISTINCT order_id` subqueries via DuckDB.
  - The standard schema stores pre-allocated line-level operational expenses so that $\sum (\text{line costs}) = \text{total order cost}$.
