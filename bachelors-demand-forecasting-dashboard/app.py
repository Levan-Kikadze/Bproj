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
SAMPLE_DATA_DIR = PROJECT_ROOT / "sample_data"
DASHBOARD_GUIDE_PATH = PROJECT_ROOT / "docs" / "dashboard_help_guide.md"
BUNDLED_DATASETS = {
    "Full clean sample": {
        "file_name": "sample_sales_data.csv",
        "description": "Large clean dataset for the main end-to-end demo, KPI review, and baseline model comparison.",
    },
    "Data quality issues showcase": {
        "file_name": "sample_sales_data_quality_issues.csv",
        "description": "Small dataset with duplicates, invalid dates, missing revenue, negative revenue, and transaction issues.",
    },
    "Holiday and promotion showcase": {
        "file_name": "sample_sales_data_event_features.csv",
        "description": "Includes holiday and promotion signals plus several stores and categories for feature and segment demos.",
    },
    "Anomalies and missing periods showcase": {
        "file_name": "sample_sales_data_anomalies.csv",
        "description": "Irregular time series with gaps and clear spikes or drops for anomaly and missing-period demos.",
    },
}

HELP_TEXT = {
    "guide_tab": (
        "Use this guide when you are new to the dashboard. It explains what each tab shows, how to read every chart, "
        "what the main metrics mean, and how to avoid common interpretation mistakes."
    ),
    "raw_preview": (
        "This table shows the raw file exactly as it was loaded. Use it to confirm that dates, revenue values, "
        "and category names look correct before interpreting the rest of the dashboard."
    ),
    "data_source": (
        "Choose where the dashboard data comes from. Use a bundled demo dataset for practice or upload your own CSV "
        "when you are ready to analyze real data."
    ),
    "column_mapping": (
        "Map each business field to the correct column. If the wrong column is mapped as revenue or date, the charts, "
        "KPIs, and forecasts will be misleading."
    ),
    "aggregation": (
        "Aggregation combines individual rows into daily, weekly, or monthly periods. Use daily for detailed movement, "
        "weekly for smoother short-term patterns, and monthly for high-level trends."
    ),
    "filters": (
        "Filters narrow the cleaned dataset before KPIs, charts, and forecasts are calculated. When you change filters, "
        "every result on the page updates to match the selected subset."
    ),
    "overview": (
        "The Overview tab gives a quick business summary. Start here to understand overall performance before moving to "
        "forecasting or anomaly detection."
    ),
    "kpi_summary": (
        "These KPI cards summarize the selected dataset. Compare them together rather than in isolation: for example, "
        "high revenue with falling growth can mean the business is still large but slowing down."
    ),
    "revenue_trend": (
        "Read this chart from left to right. The line shows how revenue changes over time, while the height of each point "
        "shows the revenue level for that period. Look for upward trends, downward trends, repeating patterns, or sudden breaks."
    ),
    "revenue_growth": (
        "This chart shows period-over-period growth rate. Values above zero mean revenue increased versus the previous period; "
        "values below zero mean it decreased. Large swings can indicate promotions, seasonality, or instability."
    ),
    "revenue_breakdown": (
        "Each bar shows total revenue for one category, store, product, or other chosen dimension. Taller bars mean higher "
        "contribution to revenue. Use this to compare segments, not time trends."
    ),
    "data_quality": (
        "Use this tab before trusting any chart or forecast. It explains how many rows were removed or corrected and shows "
        "whether the uploaded data is suitable for analysis."
    ),
    "data_quality_summary": (
        "Focus first on how many rows were kept versus removed. High removal counts do not always mean bad data, but they do mean "
        "you should explain what was excluded before presenting results."
    ),
    "missing_values": (
        "This table shows missing values in the original uploaded file by column. High missing counts can weaken interpretation, "
        "especially if they affect dates, revenue, or key grouping columns."
    ),
    "cleaned_preview": (
        "This preview shows the cleaned dataset after invalid rows were removed and numeric corrections were applied. Use it to confirm "
        "that the remaining rows still match your business expectations."
    ),
    "filtered_preview": (
        "This preview shows the rows that remain after sidebar filters are applied. If a chart looks surprising, check this table first to "
        "see exactly what subset of data you are analyzing."
    ),
    "forecasting": (
        "This tab compares forecasting models on historical data, shows future projections, and explains model uncertainty. Start with the "
        "model comparison table, then inspect the detailed chart for the chosen model."
    ),
    "model_comparison": (
        "Each row shows one model tested on the same historical holdout period. Lower MAE and MAPE usually mean better accuracy, but you "
        "should also consider whether the model is stable, interpretable, and appropriate for the business pattern."
    ),
    "forecast_chart": (
        "The solid historical line shows actual revenue. Test prediction points show how the model performed on held-out history, and the "
        "dashed future line shows projected revenue. If confidence bands are wide, the forecast is more uncertain."
    ),
    "test_forecast": (
        "This table compares actual versus predicted values on the test period. Use it when you want to inspect where the model was accurate, "
        "where it missed badly, and whether the error pattern is systematic."
    ),
    "future_forecast": (
        "This table contains the model's forward-looking forecast. Treat these values as informed estimates, not guaranteed outcomes, especially "
        "when uncertainty bands are wide or the selected history is short."
    ),
    "model_coefficients": (
        "These coefficients belong to the Linear Regression model. A positive coefficient means that feature tends to push predicted revenue up; "
        "a negative coefficient means it tends to pull predicted revenue down."
    ),
    "segment_comparison": (
        "This section compares future forecasts across major segments such as stores or product categories. Use it to answer which segment is expected "
        "to contribute the most, or which segment appears weakest under the selected model."
    ),
    "anomaly": (
        "The anomaly tab highlights unusual revenue values by comparing each period to a recent rolling baseline. Use it to find spikes, drops, or other "
        "behavior that deserves explanation."
    ),
    "anomaly_chart": (
        "The main line shows revenue over time. Red markers highlight periods whose z-scores crossed the chosen threshold. These are not automatically "
        "errors; they are periods worth investigating."
    ),
    "anomalous_rows": (
        "This table lists only the flagged periods. Review it when you need exact dates, revenue values, and anomaly scores for reporting or investigation."
    ),
    "full_anomaly_results": (
        "This full table includes rolling mean, rolling standard deviation, z-score, and anomaly flag. Use it when you need to understand why a point was or was not flagged."
    ),
    "export": (
        "Use the export tab to download the processed outputs you want to keep or share. Exported files reflect the current filters and settings in the app."
    ),
}


def render_help_heading(title: str, help_text: str, *, container=st, level: str = "header") -> None:
    """Render a heading with Streamlit's native help tooltip."""
    if level == "header":
        container.header(title, help=help_text)
        return
    container.subheader(title, help=help_text)


def help_selectbox(label: str, help_text: str, options, *, container=st, **kwargs):
    """Render a selectbox with Streamlit's native help tooltip."""
    return container.selectbox(label, options=options, help=help_text, **kwargs)


def help_multiselect(label: str, help_text: str, options, *, container=st, **kwargs):
    """Render a multiselect with Streamlit's native help tooltip."""
    return container.multiselect(label, options=options, help=help_text, **kwargs)


def help_slider(label: str, help_text: str, min_value, max_value, value, *slider_args, container=st, **kwargs):
    """Render a slider with Streamlit's native help tooltip."""
    return container.slider(
        label,
        min_value,
        max_value,
        value,
        *slider_args,
        help=help_text,
        **kwargs,
    )


def help_checkbox(label: str, help_text: str, *, container=st, **kwargs):
    """Render a checkbox with Streamlit's native help tooltip."""
    return container.checkbox(label, help=help_text, **kwargs)


def help_file_uploader(label: str, help_text: str, *, container=st, **kwargs):
    """Render a file uploader with Streamlit's native help tooltip."""
    return container.file_uploader(label, help=help_text, **kwargs)


def load_dashboard_guide_markdown() -> str:
    """Load the long-form dashboard guide shown in the in-app documentation tab."""
    if not DASHBOARD_GUIDE_PATH.exists():
        return "# Dashboard Guide\n\nThe dashboard guide file is missing."
    return DASHBOARD_GUIDE_PATH.read_text(encoding="utf-8")


def render_guide_tab() -> None:
    """Render the long-form user guide for interpreting the dashboard."""
    render_help_heading("Dashboard Guide", HELP_TEXT["guide_tab"], level="header")
    st.markdown(load_dashboard_guide_markdown())


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
        st.info("Select a bundled dataset or upload a CSV file to begin. The guide below explains every chart and control.")
        guide_tabs = st.tabs(["Guide"])
        with guide_tabs[0]:
            render_guide_tab()
        return

    render_help_heading("Raw Data Preview", HELP_TEXT["raw_preview"], level="subheader")
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

    tabs = st.tabs(["Overview", "Data Quality", "Forecasting", "Anomaly Detection", "Export", "Guide"])
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

    with tabs[5]:
        render_guide_tab()


def load_sales_data() -> pd.DataFrame:
    """Load uploaded CSV data or one of the bundled demo datasets."""
    render_help_heading("1. Data Source", HELP_TEXT["data_source"], container=st.sidebar, level="header")
    data_source = help_selectbox(
        "Dataset source",
        "Choose bundled data for guided practice or upload your own CSV for real analysis.",
        options=["Bundled demo dataset", "Upload CSV"],
        container=st.sidebar,
        index=0,
    )

    if data_source == "Upload CSV":
        uploaded_file = help_file_uploader(
            "Upload sales CSV",
            "Upload a comma-separated file that contains at least one date column and one revenue column.",
            container=st.sidebar,
            type=["csv"],
        )
        if uploaded_file is None:
            st.sidebar.info("Choose a CSV file to start working with uploaded data.")
            return pd.DataFrame()
        try:
            return pd.read_csv(uploaded_file)
        except Exception as exc:
            st.sidebar.error(f"Could not read uploaded CSV: {exc}")
            return pd.DataFrame()

    dataset_name = help_selectbox(
        "Bundled demo dataset",
        "Switch between curated demo datasets that highlight clean data, data quality issues, event features, or anomalies.",
        options=list(BUNDLED_DATASETS.keys()),
        container=st.sidebar,
        index=0,
    )
    dataset_config = BUNDLED_DATASETS[dataset_name]

    st.sidebar.info("Using a bundled demo dataset.")
    st.sidebar.caption(dataset_config["description"])
    try:
        return load_bundled_dataset(dataset_name)
    except (ValueError, FileNotFoundError) as exc:
        st.sidebar.error(str(exc))
        return pd.DataFrame()


def get_bundled_dataset_path(dataset_name: str) -> Path:
    """Return the filesystem path for a named bundled dataset."""
    if dataset_name not in BUNDLED_DATASETS:
        raise ValueError(f"Unknown bundled dataset: {dataset_name}")

    dataset_path = SAMPLE_DATA_DIR / BUNDLED_DATASETS[dataset_name]["file_name"]
    if not dataset_path.exists():
        raise FileNotFoundError(f"Bundled dataset not found: {dataset_path.name}")
    return dataset_path


def load_bundled_dataset(dataset_name: str) -> pd.DataFrame:
    """Load a named bundled dataset from the sample_data directory."""
    return pd.read_csv(get_bundled_dataset_path(dataset_name))


def render_sidebar_controls(raw_df: pd.DataFrame) -> dict[str, object]:
    """Render column mapping and aggregation controls."""
    render_help_heading("2. Column Mapping", HELP_TEXT["column_mapping"], container=st.sidebar, level="header")
    columns = list(raw_df.columns)

    date_col = help_selectbox(
        "Date column",
        "Select the column that contains the sales dates or periods.",
        options=columns,
        container=st.sidebar,
        index=columns.index(default_column(columns, ["date", "day", "period"])),
    )
    revenue_col = help_selectbox(
        "Revenue column",
        "Select the numeric column that represents revenue or sales amount.",
        options=columns,
        container=st.sidebar,
        index=columns.index(default_column(columns, ["revenue", "sales", "amount", "total"])),
    )

    optional_transaction_options = ["None", *columns]
    default_transactions = optional_default_column(columns, ["transaction", "orders", "quantity", "units"])
    transactions_col_selection = help_selectbox(
        "Transactions column (optional)",
        "Choose transaction or order count if your CSV has one. It is used for transaction KPIs such as average order value.",
        options=optional_transaction_options,
        container=st.sidebar,
        index=optional_transaction_options.index(default_transactions),
    )
    transactions_col = None if transactions_col_selection == "None" else transactions_col_selection

    default_holiday = optional_default_column(columns, ["holiday", "festive", "event"])
    holiday_col_selection = help_selectbox(
        "Holiday column (optional)",
        "Optional binary or yes or no column used as an extra forecasting feature.",
        options=optional_transaction_options,
        container=st.sidebar,
        index=optional_transaction_options.index(default_holiday),
    )
    holiday_col = None if holiday_col_selection == "None" else holiday_col_selection

    default_promotion = optional_default_column(columns, ["promotion", "promo", "campaign", "discount"])
    promotion_col_selection = help_selectbox(
        "Promotion column (optional)",
        "Optional binary or yes or no promotion indicator used by Linear Regression.",
        options=optional_transaction_options,
        container=st.sidebar,
        index=optional_transaction_options.index(default_promotion),
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

    filter_columns = help_multiselect(
        "Filter/group columns (optional)",
        "Choose category columns such as product category, store, or product ID. These fields drive sidebar filters and comparison views.",
        options=candidate_filter_columns,
        container=st.sidebar,
        default=preferred_filter_columns,
    )

    render_help_heading("3. Aggregation", HELP_TEXT["aggregation"], container=st.sidebar, level="header")
    frequency = help_selectbox(
        "Aggregation frequency",
        "Choose how detailed or smooth the time series should be before charts and forecasts are computed.",
        ["Daily", "Weekly", "Monthly"],
        container=st.sidebar,
        index=0,
    )

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

    render_help_heading("4. Filters", HELP_TEXT["filters"], container=st.sidebar, level="header")
    for column in filter_columns:
        if column not in filtered_df.columns:
            continue
        options = sorted(filtered_df[column].dropna().astype(str).unique().tolist())
        if not options:
            continue
        selected_values = help_multiselect(
            column,
            f"Filter the cleaned dataset by {column}. All charts, KPIs, forecasts, and exports update to match the values selected here.",
            options=options,
            container=st.sidebar,
            default=options,
        )
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
    render_help_heading("Overview", HELP_TEXT["overview"], level="header")
    if time_series_df.empty:
        st.warning("No aggregated data is available for the selected filters.")
        return

    render_help_heading("KPI Summary", HELP_TEXT["kpi_summary"], level="subheader")
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

    render_help_heading("Revenue Trend", HELP_TEXT["revenue_trend"], level="subheader")
    st.plotly_chart(revenue_trend_chart(time_series_df), width="stretch")

    render_help_heading("Revenue Growth Rate", HELP_TEXT["revenue_growth"], level="subheader")
    st.plotly_chart(revenue_growth_chart(time_series_df), width="stretch")

    available_dimensions = [col for col in filter_columns if col in filtered_df.columns]
    if available_dimensions:
        render_help_heading("Revenue Breakdown", HELP_TEXT["revenue_breakdown"], level="subheader")
        dimension = help_selectbox(
            "Revenue breakdown dimension",
            "Choose which category column should be compared in the bar chart below.",
            available_dimensions,
        )
        st.plotly_chart(revenue_by_dimension_chart(filtered_df, dimension), width="stretch")


def render_data_quality_tab(
    quality_report: DataQualityReport,
    cleaned_df: pd.DataFrame,
    filtered_df: pd.DataFrame,
) -> None:
    """Render data cleaning and validation details."""
    render_help_heading("Data Quality", HELP_TEXT["data_quality"], level="header")

    render_help_heading("Data Quality Summary", HELP_TEXT["data_quality_summary"], level="subheader")

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

    render_help_heading("Missing Values in Uploaded Data", HELP_TEXT["missing_values"], level="subheader")
    missing_df = pd.DataFrame(
        {
            "column": list(quality_report.missing_values_by_column.keys()),
            "missing_values": list(quality_report.missing_values_by_column.values()),
        }
    )
    st.dataframe(missing_df, width="stretch")

    render_help_heading("Cleaned Data Preview", HELP_TEXT["cleaned_preview"], level="subheader")
    st.dataframe(cleaned_df.head(50), width="stretch")

    render_help_heading("Filtered Data Preview", HELP_TEXT["filtered_preview"], level="subheader")
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
    render_help_heading("Forecasting", HELP_TEXT["forecasting"], level="header")
    if time_series_df.empty:
        st.warning("No data is available for forecasting.")
        return ForecastResult("", pd.DataFrame(), pd.DataFrame(), None, None, ["No data available."])

    available_methods = ["Moving Average", "Exponential Smoothing", "Linear Regression"]
    selected_methods = help_multiselect(
        "Models to evaluate",
        "Run one or more models on the same historical split so you can compare their accuracy fairly.",
        available_methods,
        default=available_methods,
    )
    if not selected_methods:
        st.warning("Select at least one forecasting method.")
        return ForecastResult("", pd.DataFrame(), pd.DataFrame(), None, None, ["No forecasting method selected."])

    summary_controls = st.columns(4)
    default_primary_index = selected_methods.index("Linear Regression") if "Linear Regression" in selected_methods else 0
    primary_method = help_selectbox(
        "Detailed model view",
        "Choose which model should drive the detailed chart and forecast tables below.",
        selected_methods,
        container=summary_controls[0],
        index=default_primary_index,
    )
    horizon = int(
        help_selectbox(
            "Future horizon",
            "How many future periods the forecast should project forward.",
            [7, 14, 30],
            container=summary_controls[1],
            index=0,
        )
    )
    confidence_level = float(
        help_selectbox(
            "Confidence level",
            "Higher confidence levels produce wider uncertainty bands around forecast values.",
            [0.8, 0.9, 0.95],
            container=summary_controls[2],
            index=2,
        )
    )
    segment_candidates = detect_categorical_columns(
        filtered_df,
        exclude_columns=[col for col in ["date", "revenue", "transactions", holiday_col, promotion_col] if col],
    )
    segment_dimension_selection = help_selectbox(
        "Segment comparison",
        "Optionally compare future forecasts across the top segments of one selected category column.",
        ["None", *segment_candidates],
        container=summary_controls[3],
        index=0,
    )

    option_columns = st.columns(3)
    max_window = max(2, min(30, len(time_series_df) - 1))
    default_window = min(7, max_window)
    window = int(
        help_slider(
            "Moving average window",
            "How many recent periods the Moving Average model should average when making each prediction.",
            2,
            max_window,
            default_window,
            container=option_columns[0],
        )
    )
    use_trend = help_checkbox(
        "Use trend",
        "Allow Exponential Smoothing to model steady upward or downward movement over time.",
        container=option_columns[1],
        value=True,
    )
    use_seasonality = help_checkbox(
        "Use seasonality",
        "Allow Exponential Smoothing to model repeating seasonal patterns when enough history exists.",
        container=option_columns[2],
        value=False,
    )
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
    render_help_heading("Model Comparison", HELP_TEXT["model_comparison"], level="subheader")
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

    render_help_heading("Forecast Chart", HELP_TEXT["forecast_chart"], level="subheader")
    st.plotly_chart(
        forecast_chart(time_series_df, result.test_forecast, result.future_forecast),
        width="stretch",
    )

    render_help_heading("Test Forecast", HELP_TEXT["test_forecast"], level="subheader")
    st.dataframe(result.test_forecast, width="stretch")

    render_help_heading("Future Forecast", HELP_TEXT["future_forecast"], level="subheader")
    st.dataframe(result.future_forecast, width="stretch")

    if result.model_details is not None and not result.model_details.empty:
        render_help_heading("Model Coefficients", HELP_TEXT["model_coefficients"], level="subheader")
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
    render_help_heading(
        f"Segment Comparison by {segment_dimension}",
        HELP_TEXT["segment_comparison"],
        level="subheader",
    )
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
    render_help_heading("Anomaly Detection", HELP_TEXT["anomaly"], level="header")
    if time_series_df.empty:
        st.warning("No data is available for anomaly detection.")
        return pd.DataFrame()

    max_window = max(2, min(90, len(time_series_df) - 1))
    control_columns = st.columns(2)
    window = int(
        help_slider(
            "Rolling window",
            "How many recent periods define normal behavior for anomaly detection.",
            2,
            max_window,
            min(14, max_window),
            container=control_columns[0],
        )
    )
    threshold = float(
        help_slider(
            "Anomaly threshold (absolute z-score)",
            "Higher thresholds flag fewer, more extreme anomalies; lower thresholds flag more potential anomalies.",
            1.0,
            5.0,
            3.0,
            0.1,
            container=control_columns[1],
        )
    )

    anomaly_df = detect_rolling_zscore_anomalies(
        time_series_df,
        window=window,
        threshold=threshold,
    )
    anomaly_count = count_anomalies(anomaly_df)
    st.metric("Anomalies Detected", format_number(anomaly_count))
    render_help_heading("Anomaly Chart", HELP_TEXT["anomaly_chart"], level="subheader")
    st.plotly_chart(anomaly_chart(anomaly_df), width="stretch")

    render_help_heading("Anomalous Rows", HELP_TEXT["anomalous_rows"], level="subheader")
    anomalies = anomaly_df[anomaly_df["is_anomaly"]]
    if anomalies.empty:
        st.info("No anomalies detected with the current settings.")
    else:
        st.dataframe(anomalies, width="stretch")

    render_help_heading("Full Anomaly Results", HELP_TEXT["full_anomaly_results"], level="subheader")
    st.dataframe(anomaly_df, width="stretch")
    return anomaly_df


def render_export_tab(
    grouped_export_df: pd.DataFrame,
    forecast_result: ForecastResult | None,
    anomaly_df: pd.DataFrame,
) -> None:
    """Render CSV export buttons."""
    render_help_heading("Export", HELP_TEXT["export"], level="header")
    st.download_button(
        "Download cleaned aggregated dataset",
        data=dataframe_to_csv_bytes(grouped_export_df),
        file_name="cleaned_aggregated_sales.csv",
        mime="text/csv",
        disabled=grouped_export_df.empty,
        help="Download the aggregated dataset that matches the current filters, mappings, and frequency settings.",
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
        help="Download the test and future forecast output for the currently selected detailed model.",
    )

    st.download_button(
        "Download anomaly results",
        data=dataframe_to_csv_bytes(anomaly_df),
        file_name="anomaly_results.csv",
        mime="text/csv",
        disabled=anomaly_df.empty,
        help="Download the anomaly detection table, including rolling statistics and anomaly flags.",
    )


if __name__ == "__main__":
    main()
