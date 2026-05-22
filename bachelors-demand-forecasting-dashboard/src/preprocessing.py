"""Data validation, cleaning, and aggregation utilities."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class DataQualityReport:
    """Summary of data quality changes made during preprocessing."""

    original_row_count: int
    final_row_count: int
    duplicates_removed: int
    invalid_date_rows_removed: int
    invalid_revenue_rows_removed: int
    negative_revenue_rows_removed: int
    invalid_transaction_rows_normalized: int
    negative_transaction_rows_clipped: int
    missing_values_by_column: dict[str, int]
    date_range_start: pd.Timestamp | None
    date_range_end: pd.Timestamp | None

    @property
    def total_rows_removed_for_invalid_data(self) -> int:
        """Unique rows removed for invalid date, invalid revenue, or negative revenue."""
        return max(self.original_row_count - self.duplicates_removed - self.final_row_count, 0)

    def to_dict(self) -> dict[str, Any]:
        """Return the report as a plain dictionary for display or testing."""
        data = asdict(self)
        data["total_rows_removed_for_invalid_data"] = self.total_rows_removed_for_invalid_data
        return data


def clean_sales_data(
    raw_df: pd.DataFrame,
    date_col: str,
    revenue_col: str,
    transactions_col: str | None = None,
    category_cols: list[str] | None = None,
    remove_negative_revenue: bool = True,
) -> tuple[pd.DataFrame, DataQualityReport]:
    """Clean uploaded sales data and return a standardized DataFrame.

    The returned DataFrame uses standardized names:
    `date`, `revenue`, and, if selected, `transactions`.
    Selected categorical columns are preserved with their original names.
    """
    if raw_df.empty:
        report = DataQualityReport(
            original_row_count=0,
            final_row_count=0,
            duplicates_removed=0,
            invalid_date_rows_removed=0,
            invalid_revenue_rows_removed=0,
            negative_revenue_rows_removed=0,
            invalid_transaction_rows_normalized=0,
            negative_transaction_rows_clipped=0,
            missing_values_by_column={},
            date_range_start=None,
            date_range_end=None,
        )
        return pd.DataFrame(columns=["date", "revenue"]), report

    _validate_required_columns(raw_df, [date_col, revenue_col])
    if transactions_col:
        _validate_required_columns(raw_df, [transactions_col])

    category_cols = category_cols or []
    valid_category_cols = [col for col in category_cols if col in raw_df.columns]

    original_row_count = len(raw_df)
    missing_values = raw_df.isna().sum().astype(int).to_dict()

    deduped = raw_df.drop_duplicates().copy()
    duplicates_removed = original_row_count - len(deduped)

    selected_columns = _unique_preserving_order(
        [date_col, revenue_col, transactions_col, *valid_category_cols]
    )
    cleaned = deduped[selected_columns].copy()

    rename_map = {date_col: "date", revenue_col: "revenue"}
    if transactions_col:
        rename_map[transactions_col] = "transactions"
    cleaned = cleaned.rename(columns=rename_map)

    cleaned["date"] = pd.to_datetime(cleaned["date"], errors="coerce")
    cleaned["revenue"] = pd.to_numeric(cleaned["revenue"], errors="coerce")
    invalid_transaction_mask = pd.Series(False, index=cleaned.index, dtype=bool)
    negative_transaction_mask = pd.Series(False, index=cleaned.index, dtype=bool)
    if "transactions" in cleaned.columns:
        raw_transactions = cleaned["transactions"]
        normalized_transactions = pd.to_numeric(raw_transactions, errors="coerce")
        invalid_transaction_mask = raw_transactions.notna() & normalized_transactions.isna()
        negative_transaction_mask = normalized_transactions < 0
        cleaned["transactions"] = normalized_transactions.fillna(0)

    invalid_date_mask = cleaned["date"].isna()
    invalid_revenue_mask = cleaned["revenue"].isna()
    negative_revenue_mask = cleaned["revenue"] < 0

    rows_to_remove = invalid_date_mask | invalid_revenue_mask
    if remove_negative_revenue:
        rows_to_remove = rows_to_remove | negative_revenue_mask

    final_df = cleaned.loc[~rows_to_remove].copy()
    final_df["date"] = final_df["date"].dt.floor("D")
    final_df = final_df.sort_values("date").reset_index(drop=True)

    if "transactions" in final_df.columns:
        final_df["transactions"] = final_df["transactions"].clip(lower=0)

    report = DataQualityReport(
        original_row_count=original_row_count,
        final_row_count=len(final_df),
        duplicates_removed=duplicates_removed,
        invalid_date_rows_removed=int(invalid_date_mask.sum()),
        invalid_revenue_rows_removed=int(invalid_revenue_mask.sum()),
        negative_revenue_rows_removed=int((negative_revenue_mask & ~invalid_revenue_mask).sum())
        if remove_negative_revenue
        else 0,
        invalid_transaction_rows_normalized=int(invalid_transaction_mask.sum()),
        negative_transaction_rows_clipped=int(negative_transaction_mask.sum()),
        missing_values_by_column=missing_values,
        date_range_start=final_df["date"].min() if not final_df.empty else None,
        date_range_end=final_df["date"].max() if not final_df.empty else None,
    )
    return final_df, report


def aggregate_sales_data(
    cleaned_df: pd.DataFrame,
    frequency: str = "Daily",
    group_columns: list[str] | None = None,
) -> pd.DataFrame:
    """Aggregate cleaned sales data by daily, weekly, or monthly periods."""
    if cleaned_df.empty:
        columns = ["date", "revenue"]
        if "transactions" in cleaned_df.columns:
            columns.append("transactions")
        return pd.DataFrame(columns=columns)

    _validate_required_columns(cleaned_df, ["date", "revenue"])
    group_columns = [col for col in (group_columns or []) if col in cleaned_df.columns]

    working = cleaned_df.copy()
    working["date"] = pd.to_datetime(working["date"], errors="coerce")
    working = working.dropna(subset=["date"])
    working["date"] = _period_start(working["date"], frequency)

    aggregation_map: dict[str, str] = {"revenue": "sum"}
    if "transactions" in working.columns:
        aggregation_map["transactions"] = "sum"

    grouped = (
        working.groupby(["date", *group_columns], dropna=False, as_index=False)
        .agg(aggregation_map)
        .sort_values(["date", *group_columns])
        .reset_index(drop=True)
    )
    return grouped


def _period_start(date_series: pd.Series, frequency: str) -> pd.Series:
    frequency_normalized = frequency.lower()
    if frequency_normalized == "daily":
        return date_series.dt.floor("D")
    if frequency_normalized == "weekly":
        return date_series.dt.to_period("W-SUN").dt.start_time
    if frequency_normalized == "monthly":
        return date_series.dt.to_period("M").dt.to_timestamp()
    raise ValueError("frequency must be one of: Daily, Weekly, Monthly")


def _validate_required_columns(df: pd.DataFrame, required_columns: list[str]) -> None:
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required column(s): {', '.join(missing)}")


def _unique_preserving_order(values: list[str | None]) -> list[str]:
    seen: set[str] = set()
    unique_values: list[str] = []
    for value in values:
        if value is None or value in seen:
            continue
        seen.add(value)
        unique_values.append(value)
    return unique_values

