"""Rolling z-score anomaly detection."""

from __future__ import annotations

import numpy as np
import pandas as pd


def detect_rolling_zscore_anomalies(
    aggregated_df: pd.DataFrame,
    value_col: str = "revenue",
    date_col: str = "date",
    window: int = 7,
    threshold: float = 3.0,
) -> pd.DataFrame:
    """Detect anomalies using a historical rolling z-score.

    The rolling baseline is shifted by one row so the current observation does
    not influence its own anomaly score.
    """
    required_columns = {date_col, value_col}
    missing_columns = required_columns.difference(aggregated_df.columns)
    if missing_columns:
        raise ValueError(f"Missing required column(s): {', '.join(sorted(missing_columns))}")

    result = aggregated_df.copy()
    if result.empty:
        result["rolling_mean"] = pd.Series(dtype=float)
        result["rolling_std"] = pd.Series(dtype=float)
        result["z_score"] = pd.Series(dtype=float)
        result["is_anomaly"] = pd.Series(dtype=bool)
        return result

    result[date_col] = pd.to_datetime(result[date_col], errors="coerce")
    result[value_col] = pd.to_numeric(result[value_col], errors="coerce")
    result = result.dropna(subset=[date_col, value_col]).sort_values(date_col).reset_index(drop=True)

    window = max(2, int(window))
    historical_values = result[value_col].shift(1)
    min_periods = min(3, window)
    result["rolling_mean"] = historical_values.rolling(window=window, min_periods=min_periods).mean()
    result["rolling_std"] = historical_values.rolling(window=window, min_periods=min_periods).std(ddof=0)

    result["z_score"] = (result[value_col] - result["rolling_mean"]) / result["rolling_std"]
    result["z_score"] = result["z_score"].replace([np.inf, -np.inf], np.nan).fillna(0.0)
    result["is_anomaly"] = (
        result["rolling_std"].fillna(0) > 0
    ) & (result["z_score"].abs() > float(threshold))
    return result


def count_anomalies(anomaly_df: pd.DataFrame) -> int:
    """Return the number of anomaly rows in a detection result."""
    if anomaly_df.empty or "is_anomaly" not in anomaly_df.columns:
        return 0
    return int(anomaly_df["is_anomaly"].sum())

