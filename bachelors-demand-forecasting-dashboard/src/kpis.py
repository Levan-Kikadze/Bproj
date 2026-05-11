"""KPI calculations for aggregated sales data."""

from __future__ import annotations

import numpy as np
import pandas as pd


def calculate_kpis(aggregated_df: pd.DataFrame) -> dict[str, float]:
    """Calculate revenue and transaction KPIs from an aggregated time series."""
    if aggregated_df.empty or "revenue" not in aggregated_df.columns:
        return {
            "total_revenue": 0.0,
            "average_revenue": 0.0,
            "maximum_revenue": 0.0,
            "minimum_revenue": 0.0,
            "period_over_period_growth": np.nan,
        }

    revenue = pd.to_numeric(aggregated_df["revenue"], errors="coerce").fillna(0)
    result: dict[str, float] = {
        "total_revenue": float(revenue.sum()),
        "average_revenue": float(revenue.mean()),
        "maximum_revenue": float(revenue.max()),
        "minimum_revenue": float(revenue.min()),
        "period_over_period_growth": calculate_latest_growth_rate(aggregated_df),
    }

    if "transactions" in aggregated_df.columns:
        transactions = pd.to_numeric(aggregated_df["transactions"], errors="coerce").fillna(0)
        total_transactions = float(transactions.sum())
        result["total_transactions"] = total_transactions
        result["average_order_value"] = (
            float(revenue.sum() / total_transactions) if total_transactions > 0 else np.nan
        )

    return result


def add_growth_rate(aggregated_df: pd.DataFrame) -> pd.DataFrame:
    """Add a percentage revenue growth column to an aggregated DataFrame."""
    result = aggregated_df.copy()
    if result.empty or "revenue" not in result.columns:
        result["revenue_growth_rate"] = pd.Series(dtype=float)
        return result

    result["revenue"] = pd.to_numeric(result["revenue"], errors="coerce").fillna(0)
    result["revenue_growth_rate"] = result["revenue"].pct_change().replace([np.inf, -np.inf], np.nan)
    result["revenue_growth_rate"] = result["revenue_growth_rate"] * 100
    return result


def calculate_latest_growth_rate(aggregated_df: pd.DataFrame) -> float:
    """Calculate growth from the previous period to the latest period."""
    if len(aggregated_df) < 2 or "revenue" not in aggregated_df.columns:
        return np.nan

    ordered = aggregated_df.sort_values("date") if "date" in aggregated_df.columns else aggregated_df
    revenue = pd.to_numeric(ordered["revenue"], errors="coerce").fillna(0).to_numpy()
    previous = revenue[-2]
    current = revenue[-1]
    if previous == 0:
        return np.nan
    return float(((current - previous) / previous) * 100)

