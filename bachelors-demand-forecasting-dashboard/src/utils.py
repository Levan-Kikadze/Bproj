"""Small shared helpers for the Streamlit dashboard."""

from __future__ import annotations

import math

import pandas as pd


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Convert a DataFrame to UTF-8 CSV bytes for Streamlit downloads."""
    return df.to_csv(index=False).encode("utf-8")


def detect_categorical_columns(
    df: pd.DataFrame,
    exclude_columns: list[str] | None = None,
    max_unique_values: int = 50,
) -> list[str]:
    """Find likely categorical columns suitable for filtering and grouping."""
    if df.empty:
        return []

    exclude = set(exclude_columns or [])
    categorical_columns: list[str] = []
    for column in df.columns:
        if column in exclude:
            continue
        unique_count = df[column].nunique(dropna=True)
        if pd.api.types.is_object_dtype(df[column]) or pd.api.types.is_categorical_dtype(df[column]):
            categorical_columns.append(column)
        elif unique_count <= max_unique_values:
            categorical_columns.append(column)
    return categorical_columns


def default_column(columns: list[str], keywords: list[str], fallback_index: int = 0) -> str:
    """Pick a default column by keyword matching."""
    lowered = {column.lower(): column for column in columns}
    for keyword in keywords:
        for lowered_name, original_name in lowered.items():
            if keyword in lowered_name:
                return original_name
    return columns[fallback_index]


def optional_default_column(columns: list[str], keywords: list[str]) -> str:
    """Pick a default optional column or return `None` as a string sentinel."""
    for column in columns:
        lowered = column.lower()
        if any(keyword in lowered for keyword in keywords):
            return column
    return "None"


def format_currency(value: float | int | None) -> str:
    """Format a number as currency for KPI cards."""
    if value is None or _is_nan(value):
        return "N/A"
    return f"${float(value):,.2f}"


def format_number(value: float | int | None) -> str:
    """Format a number for KPI cards."""
    if value is None or _is_nan(value):
        return "N/A"
    return f"{float(value):,.0f}"


def format_percentage(value: float | int | None) -> str:
    """Format a percentage for KPI cards."""
    if value is None or _is_nan(value):
        return "N/A"
    return f"{float(value):,.2f}%"


def _is_nan(value: float | int) -> bool:
    try:
        return math.isnan(float(value))
    except (TypeError, ValueError):
        return False

