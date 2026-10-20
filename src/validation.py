"""
Data quality and validation engine for ProfitLens.
Provides non-destructive audits with actionable recommendations.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

from src.data_loader import REQUIRED_COLUMNS


@dataclass
class ValidationIssue:
    check_name: str
    severity: str  # "CRITICAL", "WARNING", "INFO"
    message: str
    affected_rows_count: int = 0
    column: Optional[str] = None
    sample_indices: List[Any] = field(default_factory=list)
    action_recommendation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_name": self.check_name,
            "severity": self.severity,
            "column": self.column or "N/A",
            "affected_rows_count": self.affected_rows_count,
            "message": self.message,
            "action_recommendation": self.action_recommendation,
        }


@dataclass
class ValidationReport:
    total_rows: int
    total_columns: int
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Data is valid if there are no CRITICAL severity issues."""
        return not any(issue.severity == "CRITICAL" for issue in self.issues)

    @property
    def has_critical_errors(self) -> bool:
        return any(issue.severity == "CRITICAL" for issue in self.issues)

    @property
    def has_warnings(self) -> bool:
        return any(issue.severity == "WARNING" for issue in self.issues)

    @property
    def critical_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "CRITICAL")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "WARNING")

    @property
    def info_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "INFO")

    def get_issues_by_severity(self, severity: str) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == severity]

    def to_summary(self) -> Dict[str, Any]:
        return {
            "total_rows": self.total_rows,
            "total_columns": self.total_columns,
            "is_valid": self.is_valid,
            "critical_errors": self.critical_count,
            "warnings": self.warning_count,
            "info_notes": self.info_count,
            "issues": [i.to_dict() for i in self.issues],
        }


def validate_dataset(df: Optional[pd.DataFrame]) -> ValidationReport:
    """
    Run the comprehensive data quality validation suite on an ingested DataFrame.
    Does NOT modify the dataset. Returns a structured ValidationReport.
    """
    issues: List[ValidationIssue] = []

    # 1. Empty dataset check
    if df is None or df.empty:
        issues.append(
            ValidationIssue(
                check_name="empty_dataset",
                severity="CRITICAL",
                message="The dataset is completely empty or None.",
                affected_rows_count=0,
                action_recommendation="Upload a valid CSV file containing transaction records.",
            )
        )
        return ValidationReport(total_rows=0, total_columns=0, issues=issues)

    total_rows, total_cols = df.shape

    # 2. Required columns check
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        issues.append(
            ValidationIssue(
                check_name="missing_required_columns",
                severity="CRITICAL",
                message=f"Missing required columns: {', '.join(missing_cols)}.",
                affected_rows_count=total_rows,
                action_recommendation=f"Ensure your CSV includes all required columns: {REQUIRED_COLUMNS}.",
            )
        )
        # Cannot safely perform row-level numeric checks if required columns are absent
        return ValidationReport(total_rows=total_rows, total_columns=total_cols, issues=issues)

    # 3. Missing / Null values in required columns
    for col in REQUIRED_COLUMNS:
        null_mask = df[col].isna()
        null_count = int(null_mask.sum())
        if null_count > 0:
            sample_idx = df.index[null_mask][:5].tolist()
            issues.append(
                ValidationIssue(
                    check_name="missing_values",
                    severity="CRITICAL" if col in ["order_id", "order_date"] else "WARNING",
                    column=col,
                    message=f"Column '{col}' has {null_count} missing (NaN/null) values ({null_count/total_rows:.1%}).",
                    affected_rows_count=null_count,
                    sample_indices=sample_idx,
                    action_recommendation=f"Impute or review records missing '{col}'. Key fields cannot be null.",
                )
            )

    # 4. Invalid dates / unparseable timestamps
    if "order_date" in df.columns:
        invalid_dates_mask = df["order_date"].isna()
        invalid_dates_count = int(invalid_dates_mask.sum())
        if invalid_dates_count > 0:
            issues.append(
                ValidationIssue(
                    check_name="invalid_dates",
                    severity="CRITICAL",
                    column="order_date",
                    message=f"Found {invalid_dates_count} unparseable or null order dates.",
                    affected_rows_count=invalid_dates_count,
                    sample_indices=df.index[invalid_dates_mask][:5].tolist(),
                    action_recommendation="Ensure all dates follow ISO format YYYY-MM-DD or standard datetime formats.",
                )
            )
        else:
            # Check for implausible dates (e.g. before 2000 or far into future)
            future_mask = df["order_date"] > (pd.Timestamp.now() + pd.Timedelta(days=365))
            past_mask = df["order_date"] < pd.Timestamp("2000-01-01")
            anomalous_dates = int((future_mask | past_mask).sum())
            if anomalous_dates > 0:
                issues.append(
                    ValidationIssue(
                        check_name="date_range_anomaly",
                        severity="WARNING",
                        column="order_date",
                        message=f"{anomalous_dates} records have order dates outside plausible range (2000 to +1 year).",
                        affected_rows_count=anomalous_dates,
                        action_recommendation="Review timestamps for year typos or simulated future projections.",
                    )
                )

    # 5. Duplicate records and duplicate line items
    # Check exact row duplicates across business columns (ignoring auto-generated line_item_id surrogate key)
    dup_cols = [c for c in df.columns if c != "line_item_id"]
    exact_duplicates_count = int(df.duplicated(subset=dup_cols).sum())
    if exact_duplicates_count > 0:
        issues.append(
            ValidationIssue(
                check_name="exact_duplicate_rows",
                severity="WARNING",
                message=f"Found {exact_duplicates_count} completely identical duplicate records.",
                affected_rows_count=exact_duplicates_count,
                action_recommendation="Deduplicate identical rows to avoid inflating revenue and units.",
            )
        )

    # Check line_item_id uniqueness if present
    if "line_item_id" in df.columns and df["line_item_id"].notna().all():
        line_item_dups = int(df["line_item_id"].duplicated().sum())
        if line_item_dups > 0:
            issues.append(
                ValidationIssue(
                    check_name="duplicate_line_item_ids",
                    severity="WARNING",
                    column="line_item_id",
                    message=f"Found {line_item_dups} duplicate line_item_id occurrences.",
                    affected_rows_count=line_item_dups,
                    action_recommendation="Ensure line_item_id is a unique surrogate key for each row.",
                )
            )

    # 6. Non-positive quantities (quantity <= 0)
    qty_invalid_mask = df["quantity"] <= 0
    qty_invalid_count = int(qty_invalid_mask.sum())
    if qty_invalid_count > 0:
        issues.append(
            ValidationIssue(
                check_name="non_positive_quantity",
                severity="CRITICAL",
                column="quantity",
                message=f"{qty_invalid_count} records contain non-positive (zero or negative) quantities.",
                affected_rows_count=qty_invalid_count,
                sample_indices=df.index[qty_invalid_mask][:5].tolist(),
                action_recommendation="Quantities must be strictly positive integers (>= 1). Returns should be flagged via 'returned' column.",
            )
        )

    # 7. Non-positive unit prices (unit_price <= 0)
    price_invalid_mask = df["unit_price"] <= 0
    price_invalid_count = int(price_invalid_mask.sum())
    if price_invalid_count > 0:
        issues.append(
            ValidationIssue(
                check_name="non_positive_unit_price",
                severity="CRITICAL",
                column="unit_price",
                message=f"{price_invalid_count} records contain non-positive (zero or negative) unit prices.",
                affected_rows_count=price_invalid_count,
                sample_indices=df.index[price_invalid_mask][:5].tolist(),
                action_recommendation="Unit prices must be positive numbers. Free items should be marked with explicit promotional discount.",
            )
        )

    # 8. Negative unit costs (unit_cost < 0)
    cost_invalid_mask = df["unit_cost"] < 0
    cost_invalid_count = int(cost_invalid_mask.sum())
    if cost_invalid_count > 0:
        issues.append(
            ValidationIssue(
                check_name="negative_unit_cost",
                severity="CRITICAL",
                column="unit_cost",
                message=f"{cost_invalid_count} records contain negative unit costs (COGS).",
                affected_rows_count=cost_invalid_count,
                sample_indices=df.index[cost_invalid_mask][:5].tolist(),
                action_recommendation="Product cost (COGS) cannot be negative.",
            )
        )

    # 9. Discount anomalies: discount < 0 or discount > unit_price
    neg_discount_mask = df["discount"] < 0
    neg_discount_count = int(neg_discount_mask.sum())
    if neg_discount_count > 0:
        issues.append(
            ValidationIssue(
                check_name="negative_discount",
                severity="CRITICAL",
                column="discount",
                message=f"{neg_discount_count} records contain negative discount values.",
                affected_rows_count=neg_discount_count,
                sample_indices=df.index[neg_discount_mask][:5].tolist(),
                action_recommendation="Discounts must be zero or positive amounts.",
            )
        )

    excess_discount_mask = (df["discount"] > df["unit_price"]) & (df["discount"].notna()) & (df["unit_price"].notna())
    excess_discount_count = int(excess_discount_mask.sum())
    if excess_discount_count > 0:
        issues.append(
            ValidationIssue(
                check_name="discount_exceeds_unit_price",
                severity="CRITICAL",
                column="discount",
                message=f"{excess_discount_count} records have discount amounts exceeding the unit price (resulting in negative price).",
                affected_rows_count=excess_discount_count,
                sample_indices=df.index[excess_discount_mask][:5].tolist(),
                action_recommendation="Ensure discount per unit does not exceed list unit price.",
            )
        )

    # 10. Negative operating costs (marketing_cost < 0 or shipping_cost < 0)
    for op_col in ["marketing_cost", "shipping_cost"]:
        if op_col in df.columns:
            neg_op_mask = df[op_col] < 0
            neg_op_count = int(neg_op_mask.sum())
            if neg_op_count > 0:
                issues.append(
                    ValidationIssue(
                        check_name=f"negative_{op_col}",
                        severity="WARNING",
                        column=op_col,
                        message=f"{neg_op_count} records have negative {op_col}.",
                        affected_rows_count=neg_op_count,
                        sample_indices=df.index[neg_op_mask][:5].tolist(),
                        action_recommendation=f"Verify if negative {op_col} represents credits/rebates or data entry errors.",
                    )
                )

    # 11. Return and Status consistency
    if "returned" in df.columns and "order_status" in df.columns:
        mismatch_mask = (df["returned"] == 1) & (df["order_status"].astype(str).str.lower() == "completed")
        mismatch_count = int(mismatch_mask.sum())
        if mismatch_count > 0:
            issues.append(
                ValidationIssue(
                    check_name="return_status_inconsistency",
                    severity="INFO",
                    column="order_status",
                    message=f"{mismatch_count} records have returned=1 but order_status='Completed'.",
                    affected_rows_count=mismatch_count,
                    action_recommendation="Align return flags with order statuses for cleaner funnel categorization.",
                )
            )

    # 12. Check for order-level cost duplication risk
    # If shipping_cost or marketing_cost is constant and repeated identically across multi-item orders
    if "order_id" in df.columns and "shipping_cost" in df.columns:
        multi_line_orders = df.groupby("order_id").filter(lambda g: len(g) > 1)
        if not multi_line_orders.empty:
            # Check if total shipping on order lines sums to realistic amounts or if order-level cost was pasted on each line
            nunique_shipping_per_order = multi_line_orders.groupby("order_id")["shipping_cost"].nunique()
            # If every multi-line order has exactly identical non-zero shipping on every line, warn user
            identical_shipping_orders = (nunique_shipping_per_order == 1).sum()
            total_multi_orders = multi_line_orders["order_id"].nunique()
            if total_multi_orders > 10 and (identical_shipping_orders / total_multi_orders) > 0.8:
                issues.append(
                    ValidationIssue(
                        check_name="possible_unallocated_order_cost",
                        severity="INFO",
                        column="shipping_cost",
                        message=(
                            f"{identical_shipping_orders} of {total_multi_orders} multi-item orders have identical shipping cost on every line. "
                            "Ensure costs are allocated per line rather than unallocated whole-order fees to prevent double-counting."
                        ),
                        action_recommendation="Verify whether shipping costs are allocated per item or repeated order-level values.",
                    )
                )

    return ValidationReport(total_rows=total_rows, total_columns=total_cols, issues=issues)
