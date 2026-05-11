"""Plotly visualizations used by the Streamlit dashboard."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.kpis import add_growth_rate


PLOT_TEMPLATE = "plotly_white"


def revenue_trend_chart(df: pd.DataFrame) -> go.Figure:
    """Create a revenue trend line chart."""
    figure = px.line(
        df,
        x="date",
        y="revenue",
        markers=True,
        title="Revenue Trend Over Time",
        template=PLOT_TEMPLATE,
    )
    figure.update_layout(yaxis_title="Revenue", xaxis_title="Date")
    return figure


def revenue_growth_chart(df: pd.DataFrame) -> go.Figure:
    """Create a period-over-period revenue growth chart."""
    growth_df = add_growth_rate(df)
    figure = px.line(
        growth_df,
        x="date",
        y="revenue_growth_rate",
        markers=True,
        title="Revenue Growth Rate",
        template=PLOT_TEMPLATE,
    )
    figure.add_hline(y=0, line_dash="dash", line_color="gray")
    figure.update_layout(yaxis_title="Growth Rate (%)", xaxis_title="Date")
    return figure


def revenue_by_dimension_chart(df: pd.DataFrame, dimension: str, top_n: int = 15) -> go.Figure:
    """Create a bar chart for revenue by a categorical dimension."""
    grouped = (
        df.groupby(dimension, dropna=False, as_index=False)["revenue"]
        .sum()
        .sort_values("revenue", ascending=False)
        .head(top_n)
    )
    grouped[dimension] = grouped[dimension].astype(str)
    figure = px.bar(
        grouped,
        x=dimension,
        y="revenue",
        title=f"Revenue by {dimension}",
        template=PLOT_TEMPLATE,
    )
    figure.update_layout(yaxis_title="Revenue", xaxis_title=dimension)
    return figure


def forecast_chart(
    history_df: pd.DataFrame,
    test_forecast_df: pd.DataFrame,
    future_forecast_df: pd.DataFrame,
) -> go.Figure:
    """Create an actual vs predicted revenue chart."""
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=history_df["date"],
            y=history_df["revenue"],
            mode="lines+markers",
            name="Actual Revenue",
        )
    )

    if not test_forecast_df.empty:
        figure.add_trace(
            go.Scatter(
                x=test_forecast_df["date"],
                y=test_forecast_df["predicted"],
                mode="lines+markers",
                name="Test Prediction",
            )
        )

    if not future_forecast_df.empty:
        figure.add_trace(
            go.Scatter(
                x=future_forecast_df["date"],
                y=future_forecast_df["predicted"],
                mode="lines+markers",
                name="Future Forecast",
                line={"dash": "dash"},
            )
        )

    figure.update_layout(
        title="Actual vs Predicted Revenue",
        xaxis_title="Date",
        yaxis_title="Revenue",
        template=PLOT_TEMPLATE,
    )
    return figure


def anomaly_chart(anomaly_df: pd.DataFrame) -> go.Figure:
    """Create a revenue trend chart with anomalies highlighted."""
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=anomaly_df["date"],
            y=anomaly_df["revenue"],
            mode="lines+markers",
            name="Revenue",
        )
    )

    anomalies = anomaly_df[anomaly_df["is_anomaly"]]
    if not anomalies.empty:
        figure.add_trace(
            go.Scatter(
                x=anomalies["date"],
                y=anomalies["revenue"],
                mode="markers",
                name="Anomaly",
                marker={"color": "red", "size": 11, "symbol": "x"},
            )
        )

    figure.update_layout(
        title="Rolling Z-Score Anomaly Detection",
        xaxis_title="Date",
        yaxis_title="Revenue",
        template=PLOT_TEMPLATE,
    )
    return figure

