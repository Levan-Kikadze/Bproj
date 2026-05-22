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
    st.dataframe(raw_df.head(25), use_container_width=True)

    selections = render_sidebar_controls(raw_df)
    try:
        cleaned_df, quality_report = clean_sales_data(
            raw_df=raw_df,
            date_col=selections["date_col"],
            revenue_col=selections["revenue_col"],
            transactions_col=selections["transactions_col"],
            category_cols=selections["filter_columns"],
        )
    except ValueError as exc:
        st.error(str(exc))
        return

    filtered_df = apply_sidebar_filters(cleaned_df, selections["filter_columns"])
    if filtered_df.empty:
        st.error("No rows remain after cleaning and filtering. Adjust filters or upload a different CSV.")
        return

    frequency = selections["frequency"]
    time_series_df = aggregate_sales_data(filtered_df, frequency=frequency)
    grouped_export_df = aggregate_sales_data(
        filtered_df,
        frequency=frequency,
        group_columns=selections["filter_columns"],
    )

    tabs = st.tabs(["Overview", "Data Quality", "Forecasting", "Anomaly Detection", "Export"])
    forecast_result: ForecastResult | None = None
    anomaly_df = pd.DataFrame()

    with tabs[0]:
        render_overview_tab(time_series_df, filtered_df, selections["filter_columns"])

    with tabs[1]:
        render_data_quality_tab(quality_report, cleaned_df, filtered_df)

    with tabs[2]:
        forecast_result = render_forecasting_tab(time_series_df, frequency)

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

    candidate_filter_columns = detect_categorical_columns(
        raw_df,
        exclude_columns=[date_col, revenue_col, transactions_col] if transactions_col else [date_col, revenue_col],
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

    st.plotly_chart(revenue_trend_chart(time_series_df), use_container_width=True)
    st.plotly_chart(revenue_growth_chart(time_series_df), use_container_width=True)

    available_dimensions = [col for col in filter_columns if col in filtered_df.columns]
    if available_dimensions:
        dimension = st.selectbox("Revenue breakdown dimension", available_dimensions)
        st.plotly_chart(revenue_by_dimension_chart(filtered_df, dimension), use_container_width=True)


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
    st.dataframe(missing_df, use_container_width=True)

    st.subheader("Cleaned Data Preview")
    st.dataframe(cleaned_df.head(50), use_container_width=True)

    st.subheader("Filtered Data Preview")
    st.caption(f"{len(filtered_df):,} row(s) after sidebar filters.")
    st.dataframe(filtered_df.head(50), use_container_width=True)


def render_forecasting_tab(time_series_df: pd.DataFrame, frequency: str) -> ForecastResult:
    """Render forecasting controls, metrics, chart, and result tables."""
    st.header("Forecasting")
    if time_series_df.empty:
        st.warning("No data is available for forecasting.")
        return ForecastResult("", pd.DataFrame(), pd.DataFrame(), None, None, ["No data available."])

    control_columns = st.columns(4)
    method = control_columns[0].selectbox("Forecasting method", ["Moving Average", "Exponential Smoothing"])
    horizon = int(control_columns[1].selectbox("Future horizon", [7, 14, 30], index=0))

    if method == "Moving Average":
        max_window = max(2, min(30, len(time_series_df) - 1))
        default_window = min(7, max_window)
        window = int(control_columns[2].slider("Moving average window", 2, max_window, default_window))
        result = run_moving_average_forecast(
            time_series_df,
            window=window,
            horizon=horizon,
            frequency=frequency,
        )
    else:
        use_trend = control_columns[2].checkbox("Use trend", value=True)
        use_seasonality = control_columns[3].checkbox("Use seasonality", value=False)
        default_period = {"Daily": 7, "Weekly": 4, "Monthly": 12}[frequency]
        seasonal_periods = default_period if use_seasonality else None
        result = run_exponential_smoothing_forecast(
            time_series_df,
            horizon=horizon,
            frequency=frequency,
            use_trend=use_trend,
            seasonal_periods=seasonal_periods,
        )

    for warning in result.warnings:
        st.warning(warning)

    metric_columns = st.columns(2)
    metric_columns[0].metric("MAE", format_currency(result.mae))
    metric_columns[1].metric("MAPE", format_percentage(result.mape))
    if result.mape is not None and np.isnan(result.mape):
        st.info("MAPE is unavailable because all valid test actual values are zero.")

    st.plotly_chart(
        forecast_chart(time_series_df, result.test_forecast, result.future_forecast),
        use_container_width=True,
    )

    st.subheader("Test Forecast")
    st.dataframe(result.test_forecast, use_container_width=True)

    st.subheader("Future Forecast")
    st.dataframe(result.future_forecast, use_container_width=True)
    return result


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
    st.plotly_chart(anomaly_chart(anomaly_df), use_container_width=True)

    st.subheader("Anomalous Rows")
    anomalies = anomaly_df[anomaly_df["is_anomaly"]]
    if anomalies.empty:
        st.info("No anomalies detected with the current settings.")
    else:
        st.dataframe(anomalies, use_container_width=True)

    st.subheader("Full Anomaly Results")
    st.dataframe(anomaly_df, use_container_width=True)
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
