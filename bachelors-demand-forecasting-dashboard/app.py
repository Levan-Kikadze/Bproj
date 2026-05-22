"""Streamlit app for SME demand and revenue forecasting."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from src.anomaly_detection import count_anomalies, detect_rolling_zscore_anomalies
from src.forecasting import (
    ForecastResult,
    run_exponential_smoothing_forecast,
    run_linear_regression_forecast,
    run_moving_average_forecast,
)
from src.kpis import calculate_kpis
from src.preprocessing import DataQualityReport, aggregate_sales_data, clean_sales_data
from src.utils import (
    dataframe_to_csv_bytes,
    default_column,
    detect_categorical_columns,
    format_currency,
    format_number,
    format_percentage,
    optional_default_column,
)
from src.visualization import (
    anomaly_chart,
    forecast_chart,
    revenue_by_dimension_chart,
    revenue_growth_chart,
    revenue_trend_chart,
    segment_forecast_comparison_chart,
)


PROJECT_ROOT = Path(__file__).parent
SAMPLE_DATA_PATH = PROJECT_ROOT / "sample_data" / "sample_sales_data.csv"


def main() -> None:
    """Run the Streamlit dashboard."""
    st.set_page_config(
        page_title="AI Demand and Revenue Forecasting Dashboard",
        layout="wide",
    )

    st.title("AI-Driven Demand and Revenue Forecasting Dashboard")
    st.caption(
        "A practical dashboard for SMEs to clean sales data, monitor KPIs, forecast revenue, "
        "and detect unusual sales behavior."
    )

    raw_df = load_sales_data()
    if raw_df.empty:
        st.error("No data is available. Upload a CSV file or restore the sample dataset.")
        return

    st.subheader("Raw Data Preview")
    st.dataframe(raw_df.head(25), width="stretch")

    selections = render_sidebar_controls(raw_df)
    try:
        cleaned_df, quality_report = clean_sales_data(
            raw_df=raw_df,
            date_col=selections["date_col"],
            revenue_col=selections["revenue_col"],
            transactions_col=selections["transactions_col"],
            category_cols=selections["filter_columns"],
            extra_cols=[selections["holiday_col"], selections["promotion_col"]],
        )
    except ValueError as exc:
        st.error(str(exc))
        return

    filtered_df = apply_sidebar_filters(cleaned_df, selections["filter_columns"])
    if filtered_df.empty:
        st.error("No rows remain after cleaning and filtering. Adjust filters or upload a different CSV.")
        return

    frequency = selections["frequency"]
    event_columns = [col for col in [selections["holiday_col"], selections["promotion_col"]] if col]
    time_series_df = aggregate_sales_data(filtered_df, frequency=frequency, event_columns=event_columns)
    grouped_export_df = aggregate_sales_data(
        filtered_df,
        frequency=frequency,
        group_columns=selections["filter_columns"],
        event_columns=event_columns,
    )

    tabs = st.tabs(["Overview", "Data Quality", "Forecasting", "Anomaly Detection", "Export"])
    forecast_result: ForecastResult | None = None
    anomaly_df = pd.DataFrame()

    with tabs[0]:
        render_overview_tab(time_series_df, filtered_df, selections["filter_columns"])

    with tabs[1]:
        render_data_quality_tab(quality_report, cleaned_df, filtered_df)

    with tabs[2]:
        forecast_result = render_forecasting_tab(
            time_series_df,
            filtered_df,
            frequency,
            selections["holiday_col"],
            selections["promotion_col"],
        )

    with tabs[3]:
        anomaly_df = render_anomaly_tab(time_series_df)

    with tabs[4]:
        render_export_tab(grouped_export_df, forecast_result, anomaly_df)


def load_sales_data() -> pd.DataFrame:
    """Load uploaded CSV data or the bundled sample dataset."""
    st.sidebar.header("1. Data Source")
    uploaded_file = st.sidebar.file_uploader("Upload sales CSV", type=["csv"])

    if uploaded_file is not None:
        try:
            return pd.read_csv(uploaded_file)
        except Exception as exc:
            st.sidebar.error(f"Could not read uploaded CSV: {exc}")
            return pd.DataFrame()

    st.sidebar.info("No file uploaded. Using bundled sample sales data.")
    if not SAMPLE_DATA_PATH.exists():
        return pd.DataFrame()
    return pd.read_csv(SAMPLE_DATA_PATH)


def render_sidebar_controls(raw_df: pd.DataFrame) -> dict[str, object]:
    """Render column mapping and aggregation controls."""
    st.sidebar.header("2. Column Mapping")
    columns = list(raw_df.columns)

    date_col = st.sidebar.selectbox(
        "Date column",
        options=columns,
        index=columns.index(default_column(columns, ["date", "day", "period"])),
    )
    revenue_col = st.sidebar.selectbox(
        "Revenue column",
        options=columns,
        index=columns.index(default_column(columns, ["revenue", "sales", "amount", "total"])),
    )

    optional_transaction_options = ["None", *columns]
    default_transactions = optional_default_column(columns, ["transaction", "orders", "quantity", "units"])
    transactions_col_selection = st.sidebar.selectbox(
        "Transactions column (optional)",
        options=optional_transaction_options,
        index=optional_transaction_options.index(default_transactions),
    )
    transactions_col = None if transactions_col_selection == "None" else transactions_col_selection

    default_holiday = optional_default_column(columns, ["holiday", "festive", "event"])
    holiday_col_selection = st.sidebar.selectbox(
        "Holiday column (optional)",
        options=optional_transaction_options,
        index=optional_transaction_options.index(default_holiday),
        help="Optional binary or yes/no column used as an extra forecasting feature.",
    )
    holiday_col = None if holiday_col_selection == "None" else holiday_col_selection

    default_promotion = optional_default_column(columns, ["promotion", "promo", "campaign", "discount"])
    promotion_col_selection = st.sidebar.selectbox(
        "Promotion column (optional)",
        options=optional_transaction_options,
        index=optional_transaction_options.index(default_promotion),
        help="Optional binary or yes/no promotion indicator used by Linear Regression.",
    )
    promotion_col = None if promotion_col_selection == "None" else promotion_col_selection

    candidate_filter_columns = detect_categorical_columns(
        raw_df,
        exclude_columns=[
            col
            for col in [date_col, revenue_col, transactions_col, holiday_col, promotion_col]
            if col is not None
        ],
    )
    preferred_filter_columns = [
        col for col in ["product_category", "store_id", "product_id"] if col in candidate_filter_columns
    ]

    filter_columns = st.sidebar.multiselect(
        "Filter/group columns (optional)",
        options=candidate_filter_columns,
        default=preferred_filter_columns,
        help="Use categorical columns such as product category, store, or product ID.",
    )

    st.sidebar.header("3. Aggregation")
    frequency = st.sidebar.selectbox("Aggregation frequency", ["Daily", "Weekly", "Monthly"], index=0)

    return {
        "date_col": date_col,
        "revenue_col": revenue_col,
        "transactions_col": transactions_col,
        "holiday_col": holiday_col,
        "promotion_col": promotion_col,
        "filter_columns": filter_columns,
        "frequency": frequency,
    }


def apply_sidebar_filters(cleaned_df: pd.DataFrame, filter_columns: list[str]) -> pd.DataFrame:
    """Apply selected categorical filters to cleaned data."""
    filtered_df = cleaned_df.copy()
    if not filter_columns:
        return filtered_df

    st.sidebar.header("4. Filters")
    for column in filter_columns:
        if column not in filtered_df.columns:
            continue
        options = sorted(filtered_df[column].dropna().astype(str).unique().tolist())
        if not options:
            continue
        selected_values = st.sidebar.multiselect(column, options=options, default=options)
        if selected_values:
            filtered_df = filtered_df[filtered_df[column].astype(str).isin(selected_values)]
        else:
            filtered_df = filtered_df.iloc[0:0]
    return filtered_df


def render_overview_tab(
    time_series_df: pd.DataFrame,
    filtered_df: pd.DataFrame,
    filter_columns: list[str],
) -> None:
    """Render KPI cards and core revenue charts."""
    st.header("Overview")
    if time_series_df.empty:
        st.warning("No aggregated data is available for the selected filters.")
        return

    kpis = calculate_kpis(time_series_df)
    metric_columns = st.columns(4)
    metric_columns[0].metric("Total Revenue", format_currency(kpis.get("total_revenue")))
    metric_columns[1].metric("Average Revenue", format_currency(kpis.get("average_revenue")))
    metric_columns[2].metric("Maximum Revenue", format_currency(kpis.get("maximum_revenue")))
    metric_columns[3].metric("Minimum Revenue", format_currency(kpis.get("minimum_revenue")))

    metric_columns = st.columns(3)
    if "total_transactions" in kpis:
        metric_columns[0].metric("Total Transactions", format_number(kpis.get("total_transactions")))
        metric_columns[1].metric("Average Order Value", format_currency(kpis.get("average_order_value")))
        metric_columns[2].metric(
            "Latest Revenue Growth",
            format_percentage(kpis.get("period_over_period_growth")),
        )
    else:
        metric_columns[0].metric(
            "Latest Revenue Growth",
            format_percentage(kpis.get("period_over_period_growth")),
        )

    st.plotly_chart(revenue_trend_chart(time_series_df), width="stretch")
    st.plotly_chart(revenue_growth_chart(time_series_df), width="stretch")

    available_dimensions = [col for col in filter_columns if col in filtered_df.columns]
    if available_dimensions:
        dimension = st.selectbox("Revenue breakdown dimension", available_dimensions)
        st.plotly_chart(revenue_by_dimension_chart(filtered_df, dimension), width="stretch")


def render_data_quality_tab(
    quality_report: DataQualityReport,
    cleaned_df: pd.DataFrame,
    filtered_df: pd.DataFrame,
) -> None:
    """Render data cleaning and validation details."""
    st.header("Data Quality")

    metric_columns = st.columns(4)
    metric_columns[0].metric("Original Rows", format_number(quality_report.original_row_count))
    metric_columns[1].metric("Final Clean Rows", format_number(quality_report.final_row_count))
    metric_columns[2].metric("Duplicates Removed", format_number(quality_report.duplicates_removed))
    metric_columns[3].metric(
        "Rows Removed",
        format_number(quality_report.total_rows_removed_for_invalid_data),
    )

    detail_columns = st.columns(3)
    detail_columns[0].metric(
        "Invalid Dates",
        format_number(quality_report.invalid_date_rows_removed),
    )
    detail_columns[1].metric(
        "Invalid/Missing Revenue",
        format_number(quality_report.invalid_revenue_rows_removed),
    )
    detail_columns[2].metric(
        "Negative Revenue Removed",
        format_number(quality_report.negative_revenue_rows_removed),
    )
    st.caption("Rows Removed counts unique rows removed after deduplication. Issue counts below can overlap.")

    if "transactions" in cleaned_df.columns:
        transaction_columns = st.columns(2)
        transaction_columns[0].metric(
            "Invalid Transactions Set to 0",
            format_number(quality_report.invalid_transaction_rows_normalized),
        )
        transaction_columns[1].metric(
            "Negative Transactions Set to 0",
            format_number(quality_report.negative_transaction_rows_clipped),
        )

    if quality_report.date_range_start is not None and quality_report.date_range_end is not None:
        st.info(
            "Cleaned date range: "
            f"{quality_report.date_range_start.date()} to {quality_report.date_range_end.date()}"
        )

    st.subheader("Missing Values in Uploaded Data")
    missing_df = pd.DataFrame(
        {
            "column": list(quality_report.missing_values_by_column.keys()),
            "missing_values": list(quality_report.missing_values_by_column.values()),
        }
    )
    st.dataframe(missing_df, width="stretch")

    st.subheader("Cleaned Data Preview")
    st.dataframe(cleaned_df.head(50), width="stretch")

    st.subheader("Filtered Data Preview")
    st.caption(f"{len(filtered_df):,} row(s) after sidebar filters.")
    st.dataframe(filtered_df.head(50), width="stretch")


def render_forecasting_tab(
    time_series_df: pd.DataFrame,
    filtered_df: pd.DataFrame,
    frequency: str,
    holiday_col: str | None,
    promotion_col: str | None,
) -> ForecastResult:
    """Render forecasting controls, metrics, chart, and result tables."""
    st.header("Forecasting")
    if time_series_df.empty:
        st.warning("No data is available for forecasting.")
        return ForecastResult("", pd.DataFrame(), pd.DataFrame(), None, None, ["No data available."])

    available_methods = ["Moving Average", "Exponential Smoothing", "Linear Regression"]
    selected_methods = st.multiselect(
        "Models to evaluate",
        available_methods,
        default=available_methods,
        help="Run multiple models on the same split to compare forecast quality.",
    )
    if not selected_methods:
        st.warning("Select at least one forecasting method.")
        return ForecastResult("", pd.DataFrame(), pd.DataFrame(), None, None, ["No forecasting method selected."])

    summary_controls = st.columns(4)
    default_primary_index = selected_methods.index("Linear Regression") if "Linear Regression" in selected_methods else 0
    primary_method = summary_controls[0].selectbox(
        "Detailed model view",
        selected_methods,
        index=default_primary_index,
    )
    horizon = int(summary_controls[1].selectbox("Future horizon", [7, 14, 30], index=0))
    confidence_level = float(summary_controls[2].selectbox("Confidence level", [0.8, 0.9, 0.95], index=2))
    segment_candidates = detect_categorical_columns(
        filtered_df,
        exclude_columns=[col for col in ["date", "revenue", "transactions", holiday_col, promotion_col] if col],
    )
    segment_dimension_selection = summary_controls[3].selectbox(
        "Segment comparison",
        ["None", *segment_candidates],
        index=0,
    )

    option_columns = st.columns(3)
    max_window = max(2, min(30, len(time_series_df) - 1))
    default_window = min(7, max_window)
    window = int(option_columns[0].slider("Moving average window", 2, max_window, default_window))
    use_trend = option_columns[1].checkbox("Use trend", value=True)
    use_seasonality = option_columns[2].checkbox("Use seasonality", value=False)
    default_period = {"Daily": 7, "Weekly": 4, "Monthly": 12}[frequency]
    seasonal_periods = default_period if use_seasonality else None

    st.caption(
        "Linear Regression uses a time trend, calendar effects, built-in holiday dates, and optional uploaded "
        "holiday/promotion columns. Exponential Smoothing and Linear Regression show prediction intervals."
    )

    results = {
        method_name: run_selected_forecast_method(
            method=method_name,
            time_series_df=time_series_df,
            frequency=frequency,
            horizon=horizon,
            window=window,
            use_trend=use_trend,
            seasonal_periods=seasonal_periods,
            confidence_level=confidence_level,
            holiday_col=holiday_col,
            promotion_col=promotion_col,
        )
        for method_name in selected_methods
    }
    result = results[primary_method]

    comparison_rows = []
    for method_name, method_result in results.items():
        comparison_rows.append(
            {
                "method": method_name,
                "mae": method_result.mae,
                "mape": method_result.mape,
                "test_periods": len(method_result.test_forecast),
                "future_periods": len(method_result.future_forecast),
                "warnings": " | ".join(method_result.warnings),
            }
        )
        for warning in method_result.warnings:
            st.warning(f"{method_name}: {warning}")

    comparison_df = pd.DataFrame(comparison_rows)
    st.subheader("Model Comparison")
    st.dataframe(comparison_df, width="stretch")

    valid_comparisons = comparison_df.dropna(subset=["mae"])
    if not valid_comparisons.empty:
        best_method_row = valid_comparisons.sort_values("mae").iloc[0]
        st.info(f"Lowest MAE on the held-out test split: {best_method_row['method']}.")

    metric_columns = st.columns(2)
    metric_columns[0].metric("MAE", format_currency(result.mae))
    metric_columns[1].metric("MAPE", format_percentage(result.mape))
    if result.mape is not None and np.isnan(result.mape):
        st.info("MAPE is unavailable because all valid test actual values are zero.")
    if result.confidence_level is not None:
        st.caption(f"Prediction intervals shown at {result.confidence_level:.0%} confidence for {primary_method}.")

    st.plotly_chart(
        forecast_chart(time_series_df, result.test_forecast, result.future_forecast),
        width="stretch",
    )

    st.subheader("Test Forecast")
    st.dataframe(result.test_forecast, width="stretch")

    st.subheader("Future Forecast")
    st.dataframe(result.future_forecast, width="stretch")

    if result.model_details is not None and not result.model_details.empty:
        st.subheader("Model Coefficients")
        st.dataframe(result.model_details, width="stretch")

    if segment_dimension_selection != "None":
        render_segment_comparison_section(
            filtered_df=filtered_df,
            segment_dimension=segment_dimension_selection,
            method=primary_method,
            frequency=frequency,
            horizon=horizon,
            window=window,
            use_trend=use_trend,
            seasonal_periods=seasonal_periods,
            confidence_level=confidence_level,
            holiday_col=holiday_col,
            promotion_col=promotion_col,
        )

    return result


def run_selected_forecast_method(
    method: str,
    time_series_df: pd.DataFrame,
    frequency: str,
    horizon: int,
    window: int,
    use_trend: bool,
    seasonal_periods: int | None,
    confidence_level: float,
    holiday_col: str | None,
    promotion_col: str | None,
) -> ForecastResult:
    """Run the selected forecasting method with shared UI settings."""
    if method == "Moving Average":
        return run_moving_average_forecast(
            time_series_df,
            window=window,
            horizon=horizon,
            frequency=frequency,
        )
    if method == "Exponential Smoothing":
        return run_exponential_smoothing_forecast(
            time_series_df,
            horizon=horizon,
            frequency=frequency,
            use_trend=use_trend,
            seasonal_periods=seasonal_periods,
            confidence_level=confidence_level,
        )
    if method == "Linear Regression":
        return run_linear_regression_forecast(
            time_series_df,
            horizon=horizon,
            frequency=frequency,
            holiday_col=holiday_col,
            promotion_col=promotion_col,
            confidence_level=confidence_level,
        )
    raise ValueError(f"Unsupported forecasting method: {method}")


def render_segment_comparison_section(
    filtered_df: pd.DataFrame,
    segment_dimension: str,
    method: str,
    frequency: str,
    horizon: int,
    window: int,
    use_trend: bool,
    seasonal_periods: int | None,
    confidence_level: float,
    holiday_col: str | None,
    promotion_col: str | None,
) -> None:
    """Render forecast comparisons across the top segments of one selected dimension."""
    st.subheader(f"Segment Comparison by {segment_dimension}")
    if segment_dimension not in filtered_df.columns:
        st.info("The selected comparison dimension is not available after filtering.")
        return

    top_segments = (
        filtered_df.groupby(segment_dimension, dropna=False)["revenue"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
    )
    if top_segments.empty:
        st.info("No segment data is available for comparison.")
        return

    event_columns = [col for col in [holiday_col, promotion_col] if col]
    comparison_rows: list[dict[str, object]] = []
    future_segment_frames: list[pd.DataFrame] = []

    for segment_value in top_segments.index.tolist():
        segment_df = filtered_df[filtered_df[segment_dimension].astype(str) == str(segment_value)]
        segment_time_series = aggregate_sales_data(
            segment_df,
            frequency=frequency,
            event_columns=event_columns,
        )
        segment_result = run_selected_forecast_method(
            method=method,
            time_series_df=segment_time_series,
            frequency=frequency,
            horizon=horizon,
            window=window,
            use_trend=use_trend,
            seasonal_periods=seasonal_periods,
            confidence_level=confidence_level,
            holiday_col=holiday_col,
            promotion_col=promotion_col,
        )

        comparison_rows.append(
            {
                segment_dimension: str(segment_value),
                "mae": segment_result.mae,
                "mape": segment_result.mape,
                "forecast_total": float(segment_result.future_forecast["predicted"].sum())
                if not segment_result.future_forecast.empty
                else np.nan,
                "warnings": " | ".join(segment_result.warnings),
            }
        )

        if not segment_result.future_forecast.empty:
            segment_future = segment_result.future_forecast.copy()
            segment_future[segment_dimension] = str(segment_value)
            future_segment_frames.append(segment_future)

    segment_comparison_df = pd.DataFrame(comparison_rows).sort_values("mae", na_position="last")
    st.dataframe(segment_comparison_df, width="stretch")

    if future_segment_frames:
        st.plotly_chart(
            segment_forecast_comparison_chart(pd.concat(future_segment_frames, ignore_index=True), segment_dimension),
            width="stretch",
        )
    else:
        st.info("No segment forecasts could be generated with the current settings.")


def render_anomaly_tab(time_series_df: pd.DataFrame) -> pd.DataFrame:
    """Render rolling z-score anomaly detection controls and outputs."""
    st.header("Anomaly Detection")
    if time_series_df.empty:
        st.warning("No data is available for anomaly detection.")
        return pd.DataFrame()

    max_window = max(2, min(90, len(time_series_df) - 1))
    control_columns = st.columns(2)
    window = int(control_columns[0].slider("Rolling window", 2, max_window, min(14, max_window)))
    threshold = float(control_columns[1].slider("Anomaly threshold (absolute z-score)", 1.0, 5.0, 3.0, 0.1))

    anomaly_df = detect_rolling_zscore_anomalies(
        time_series_df,
        window=window,
        threshold=threshold,
    )
    anomaly_count = count_anomalies(anomaly_df)
    st.metric("Anomalies Detected", format_number(anomaly_count))
    st.plotly_chart(anomaly_chart(anomaly_df), width="stretch")

    st.subheader("Anomalous Rows")
    anomalies = anomaly_df[anomaly_df["is_anomaly"]]
    if anomalies.empty:
        st.info("No anomalies detected with the current settings.")
    else:
        st.dataframe(anomalies, width="stretch")

    st.subheader("Full Anomaly Results")
    st.dataframe(anomaly_df, width="stretch")
    return anomaly_df


def render_export_tab(
    grouped_export_df: pd.DataFrame,
    forecast_result: ForecastResult | None,
    anomaly_df: pd.DataFrame,
) -> None:
    """Render CSV export buttons."""
    st.header("Export")
    st.download_button(
        "Download cleaned aggregated dataset",
        data=dataframe_to_csv_bytes(grouped_export_df),
        file_name="cleaned_aggregated_sales.csv",
        mime="text/csv",
        disabled=grouped_export_df.empty,
    )

    if forecast_result is not None:
        forecast_export_df = pd.concat(
            [
                forecast_result.test_forecast.assign(result_type="test"),
                forecast_result.future_forecast.assign(actual=np.nan, result_type="future"),
            ],
            ignore_index=True,
            sort=False,
        )
    else:
        forecast_export_df = pd.DataFrame()

    st.download_button(
        "Download forecast results",
        data=dataframe_to_csv_bytes(forecast_export_df),
        file_name="forecast_results.csv",
        mime="text/csv",
        disabled=forecast_export_df.empty,
    )

    st.download_button(
        "Download anomaly results",
        data=dataframe_to_csv_bytes(anomaly_df),
        file_name="anomaly_results.csv",
        mime="text/csv",
        disabled=anomaly_df.empty,
    )


if __name__ == "__main__":
    main()
