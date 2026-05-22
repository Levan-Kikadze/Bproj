"""Feature engineering helpers for calendar, holiday, and promotion signals."""

from __future__ import annotations

import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar


TRUTHY_VALUES = {"1", "true", "t", "yes", "y"}
FALSY_VALUES = {"0", "false", "f", "no", "n", ""}


def normalize_event_flag(series: pd.Series) -> pd.Series:
    """Convert common boolean-like event indicators to numeric 0/1 flags."""
    if series.empty:
        return pd.Series(dtype=float)

    if pd.api.types.is_bool_dtype(series):
        return series.astype(int)

    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.notna().any():
        return numeric.fillna(0).clip(lower=0, upper=1)

    lowered = series.fillna("").astype(str).str.strip().str.lower()
    normalized = lowered.map(
        lambda value: 1.0 if value in TRUTHY_VALUES else 0.0 if value in FALSY_VALUES else 0.0
    )
    return normalized.astype(float)


def add_calendar_features(df: pd.DataFrame, date_col: str = "date", start_index: int = 0) -> pd.DataFrame:
    """Add deterministic calendar features derived from a date column."""
    if date_col not in df.columns:
        raise ValueError(f"Missing required column: {date_col}")

    result = df.copy()
    result[date_col] = pd.to_datetime(result[date_col], errors="coerce")
    if result[date_col].isna().any():
        raise ValueError("Calendar features require valid dates.")

    result["day_of_week"] = result[date_col].dt.dayofweek
    result["day_of_month"] = result[date_col].dt.day
    result["week_of_year"] = result[date_col].dt.isocalendar().week.astype(int)
    result["month"] = result[date_col].dt.month
    result["quarter"] = result[date_col].dt.quarter
    result["is_weekend"] = result["day_of_week"].isin([5, 6]).astype(int)
    result["is_month_start"] = result[date_col].dt.is_month_start.astype(int)
    result["is_month_end"] = result[date_col].dt.is_month_end.astype(int)
    result["time_index"] = range(start_index, start_index + len(result))
    return result


def add_holiday_features(
    df: pd.DataFrame,
    date_col: str = "date",
    holiday_col: str | None = None,
) -> pd.DataFrame:
    """Add or normalize a holiday flag column."""
    if date_col not in df.columns:
        raise ValueError(f"Missing required column: {date_col}")

    result = df.copy()
    result[date_col] = pd.to_datetime(result[date_col], errors="coerce")
    if result[date_col].isna().any():
        raise ValueError("Holiday features require valid dates.")

    if holiday_col and holiday_col in result.columns:
        result["is_holiday"] = normalize_event_flag(result[holiday_col])
        return result

    holiday_calendar = USFederalHolidayCalendar()
    holidays = holiday_calendar.holidays(
        start=result[date_col].min(),
        end=result[date_col].max(),
    )
    result["is_holiday"] = result[date_col].isin(holidays).astype(int)
    return result


def build_calendar_feature_matrix(
    dates: pd.Series,
    start_index: int = 0,
    holiday_values: pd.Series | None = None,
    promotion_values: pd.Series | None = None,
    reference_columns: list[str] | None = None,
) -> pd.DataFrame:
    """Build a regression-ready feature matrix from dates and optional event flags."""
    working = pd.DataFrame({"date": pd.to_datetime(dates, errors="coerce")})
    if working["date"].isna().any():
        raise ValueError("Feature matrices require valid dates.")

    working = add_calendar_features(working, start_index=start_index)
    if holiday_values is not None:
        working["is_holiday"] = normalize_event_flag(holiday_values)
    else:
        working = add_holiday_features(working)

    if promotion_values is not None:
        working["promotion_active"] = normalize_event_flag(promotion_values)
    else:
        working["promotion_active"] = 0.0

    working["day_of_week_name"] = working["date"].dt.day_name()
    working["month_name"] = working["date"].dt.month_name()
    encoded = pd.get_dummies(
        working[
            [
                "time_index",
                "day_of_month",
                "week_of_year",
                "quarter",
                "is_weekend",
                "is_month_start",
                "is_month_end",
                "is_holiday",
                "promotion_active",
                "day_of_week_name",
                "month_name",
            ]
        ],
        columns=["day_of_week_name", "month_name"],
        drop_first=True,
        dtype=float,
    )

    if reference_columns is not None:
        encoded = encoded.reindex(columns=reference_columns, fill_value=0.0)

    return encoded.astype(float)