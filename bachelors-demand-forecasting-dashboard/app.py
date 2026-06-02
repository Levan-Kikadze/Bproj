"""Streamlit app for SME demand and revenue forecasting."""

from __future__ import annotations

import csv
from io import BytesIO
from dataclasses import dataclass
from typing import Any
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
from src.dashboard_store import DashboardStore, SavedDashboardRecord, SavedDashboardSummary
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
RUNTIME_DIR = PROJECT_ROOT / "runtime"
DASHBOARD_GUIDE_PATH = PROJECT_ROOT / "docs" / "dashboard_help_guide.md"
SAVE_DASHBOARD_DB_PATH = RUNTIME_DIR / "saved_dashboards.db"
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

DATA_SOURCE_MODE_KEY = "dashboard_source_mode"
BUNDLED_DATASET_KEY = "dashboard_bundled_dataset"
SAVED_DASHBOARD_SELECTION_KEY = "dashboard_saved_dashboard_selection"
DASHBOARD_NAME_KEY = "dashboard_save_name"
DATE_COL_KEY = "dashboard_date_col"
REVENUE_COL_KEY = "dashboard_revenue_col"
TRANSACTIONS_COL_KEY = "dashboard_transactions_col"
HOLIDAY_COL_KEY = "dashboard_holiday_col"
PROMOTION_COL_KEY = "dashboard_promotion_col"
FILTER_COLUMNS_KEY = "dashboard_filter_columns"
FREQUENCY_KEY = "dashboard_frequency"
OVERVIEW_DIMENSION_KEY = "dashboard_overview_dimension"
FORECAST_METHODS_KEY = "dashboard_forecast_methods"
FORECAST_PRIMARY_METHOD_KEY = "dashboard_forecast_primary_method"
FORECAST_HORIZON_KEY = "dashboard_forecast_horizon"
FORECAST_CONFIDENCE_KEY = "dashboard_forecast_confidence"
FORECAST_SEGMENT_KEY = "dashboard_forecast_segment_dimension"
FORECAST_WINDOW_KEY = "dashboard_forecast_window"
FORECAST_USE_TREND_KEY = "dashboard_forecast_use_trend"
FORECAST_USE_SEASONALITY_KEY = "dashboard_forecast_use_seasonality"
ANOMALY_WINDOW_KEY = "dashboard_anomaly_window"
ANOMALY_THRESHOLD_KEY = "dashboard_anomaly_threshold"
RAW_CSV_BYTES_KEY = "dashboard_raw_csv_bytes"
RAW_DF_CACHE_KEY = "dashboard_raw_df_cache"
RAW_FILE_NAME_KEY = "dashboard_raw_file_name"
SOURCE_TYPE_KEY = "dashboard_source_type"
SOURCE_NAME_KEY = "dashboard_source_name"
ACTIVE_SAVED_DASHBOARD_KEY = "dashboard_active_saved_dashboard"
PENDING_SAVED_DASHBOARD_LOAD_KEY = "dashboard_pending_saved_dashboard_load"
PENDING_SAVED_DASHBOARD_DELETE_KEY = "dashboard_pending_saved_dashboard_delete"

AVAILABLE_FORECAST_METHODS = ["Moving Average", "Exponential Smoothing", "Linear Regression"]
AVAILABLE_HORIZONS = [7, 14, 30]
AVAILABLE_CONFIDENCE_LEVELS = [0.8, 0.9, 0.95]
AVAILABLE_FREQUENCIES = ["Daily", "Weekly", "Monthly"]


@dataclass(frozen=True)
class DashboardLoadResult:
    """Current raw dashboard source and its originating metadata."""

    raw_df: pd.DataFrame
    raw_csv_bytes: bytes
    source_type: str
    source_name: str
    raw_file_name: str | None


DATE_COLUMN_KEYWORDS = ["date", "day", "period", "week", "month", "time"]
REVENUE_COLUMN_KEYWORDS = ["revenue", "sales", "amount", "total", "income"]
MAPPING_SAMPLE_SIZE = 5
LIKELY_WRONG_DELIMITERS = {
    ";": "semicolon",
    "\t": "tab",
    "|": "pipe",
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
    widget_key = kwargs.get("key")
    if widget_key is not None and widget_key in st.session_state:
        kwargs.pop("index", None)
    return container.selectbox(label, options=options, help=help_text, **kwargs)


def help_multiselect(label: str, help_text: str, options, *, container=st, **kwargs):
    """Render a multiselect with Streamlit's native help tooltip."""
    widget_key = kwargs.get("key")
    if widget_key is not None and widget_key in st.session_state:
        kwargs.pop("default", None)
    return container.multiselect(label, options=options, help=help_text, **kwargs)


def help_slider(label: str, help_text: str, min_value, max_value, value, *slider_args, container=st, **kwargs):
    """Render a slider with Streamlit's native help tooltip."""
    widget_key = kwargs.get("key")
    slider_kwargs = dict(kwargs)
    if slider_args:
        slider_kwargs["step"] = slider_args[0]
    slider_kwargs["help"] = help_text
    if widget_key is not None and widget_key in st.session_state:
        return container.slider(
            label,
            min_value=min_value,
            max_value=max_value,
            **slider_kwargs,
        )
    return container.slider(
        label,
        min_value=min_value,
        max_value=max_value,
        value=value,
        **slider_kwargs,
    )


def help_checkbox(label: str, help_text: str, *, container=st, **kwargs):
    """Render a checkbox with Streamlit's native help tooltip."""
    widget_key = kwargs.get("key")
    if widget_key is not None and widget_key in st.session_state:
        kwargs.pop("value", None)
    return container.checkbox(label, help=help_text, **kwargs)


def help_file_uploader(label: str, help_text: str, *, container=st, **kwargs):
    """Render a file uploader with Streamlit's native help tooltip."""
    return container.file_uploader(label, help=help_text, **kwargs)


def first_non_empty_line(text: str) -> str | None:
    """Return the first non-empty line from a text blob."""
    for line in text.splitlines():
        if line.strip():
            return line
    return None


def parse_csv_header_line(header_line: str) -> list[str]:
    """Parse a CSV header line into raw column names."""
    try:
        return next(csv.reader([header_line]))
    except Exception:
        return [part.strip() for part in header_line.split(",")]


def build_duplicate_header_error(header_columns: list[str]) -> str | None:
    """Return a blocking error when header names are duplicated."""
    seen: dict[str, str] = {}
    duplicates: set[str] = set()

    for column in header_columns:
        normalized = column.strip().lower()
        label = column.strip()
        if not normalized:
            continue
        if normalized in seen:
            duplicates.add(seen[normalized])
            duplicates.add(label or seen[normalized])
            continue
        seen[normalized] = label

    if not duplicates:
        return None

    duplicate_labels = ", ".join(sorted(duplicates))
    return (
        "The uploaded CSV contains duplicate header names "
        f"({duplicate_labels}). Rename them so each column is unique before uploading."
    )


def build_blank_header_error(header_columns: list[str]) -> str | None:
    """Return a blocking error when the CSV header contains blank cells."""
    blank_positions = [str(index) for index, column in enumerate(header_columns, start=1) if not column.strip()]
    if not blank_positions:
        return None

    return (
        "The uploaded CSV has blank header cells in column position(s) "
        f"{', '.join(blank_positions)}. Fill in every header name before uploading."
    )


def build_wrong_delimiter_error(header_line: str, column_count: int) -> str | None:
    """Return a blocking error when the file looks delimited but not comma-separated."""
    if column_count != 1 or "," in header_line:
        return None

    for delimiter, label in LIKELY_WRONG_DELIMITERS.items():
        if delimiter in header_line:
            return (
                f"The uploaded file looks {label}-separated instead of comma-separated. "
                "Re-save it as a standard comma-separated CSV and upload it again."
            )
    return None


def build_minimum_column_error(column_count: int) -> str | None:
    """Return a blocking error when the parsed file cannot support required mapping."""
    if column_count >= 2:
        return None
    return (
        "The uploaded CSV produced fewer than two columns after parsing. "
        "The dashboard needs at least one date column and one revenue column."
    )


def build_upload_structure_warnings(raw_df: pd.DataFrame) -> list[str]:
    """Return non-blocking warnings for suspicious but still readable uploads."""
    warnings: list[str] = []

    unnamed_columns = [str(column) for column in raw_df.columns if str(column).startswith("Unnamed:")]
    if unnamed_columns:
        warnings.append(
            "The uploaded CSV includes unnamed columns, which usually means the source spreadsheet had blank header cells or trailing separators."
        )

    empty_columns = [str(column) for column in raw_df.columns if raw_df[column].dropna().empty]
    if empty_columns:
        displayed_columns = ", ".join(empty_columns[:5])
        suffix = "" if len(empty_columns) <= 5 else ", ..."
        warnings.append(
            f"These uploaded columns are completely empty: {displayed_columns}{suffix}. They will not help the analysis until they contain values."
        )

    return warnings


def read_uploaded_csv_bytes(file_bytes: bytes) -> tuple[pd.DataFrame, list[str], str | None]:
    """Parse uploaded CSV bytes and classify common upload failures."""
    if not file_bytes or not file_bytes.strip():
        return pd.DataFrame(), [], "The uploaded file is empty. Add a header row and at least one data row."

    if b"\x00" in file_bytes:
        return pd.DataFrame(), [], (
            "The uploaded file contains binary characters and does not look like a plain-text CSV. "
            "Export it again as a CSV file before uploading."
        )

    try:
        file_text = file_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        return pd.DataFrame(), [], (
            "Could not decode the uploaded CSV as UTF-8 text. Re-save the file as UTF-8 CSV and try again."
        )

    header_line = first_non_empty_line(file_text)
    if header_line is None:
        return pd.DataFrame(), [], "The uploaded file is empty. Add a header row and at least one data row."

    header_columns = parse_csv_header_line(header_line)
    duplicate_header_error = build_duplicate_header_error(header_columns)
    if duplicate_header_error:
        return pd.DataFrame(), [], duplicate_header_error

    blank_header_error = build_blank_header_error(header_columns)
    if blank_header_error:
        return pd.DataFrame(), [], blank_header_error

    try:
        raw_df = pd.read_csv(BytesIO(file_bytes), encoding="utf-8-sig")
    except pd.errors.EmptyDataError:
        return pd.DataFrame(), [], "The uploaded file is empty. Add a header row and at least one data row."
    except UnicodeDecodeError:
        return pd.DataFrame(), [], (
            "Could not decode the uploaded CSV as UTF-8 text. Re-save the file as UTF-8 CSV and try again."
        )
    except pd.errors.ParserError as exc:
        return pd.DataFrame(), [], f"Could not parse the uploaded CSV because the rows are malformed: {exc}"
    except Exception as exc:
        return pd.DataFrame(), [], f"Could not read uploaded CSV: {exc}"

    wrong_delimiter_error = build_wrong_delimiter_error(header_line, len(raw_df.columns))
    if wrong_delimiter_error:
        return pd.DataFrame(), [], wrong_delimiter_error

    minimum_column_error = build_minimum_column_error(len(raw_df.columns))
    if minimum_column_error:
        return pd.DataFrame(), [], minimum_column_error

    warnings = build_upload_column_warnings(raw_df)
    warnings.extend(build_upload_structure_warnings(raw_df))
    if raw_df.empty:
        warnings.append("The uploaded file has headers but no data rows. Add at least one row with a date and revenue value.")

    return raw_df, warnings, None


def find_column_keyword_matches(columns: list[str], keywords: list[str]) -> list[str]:
    """Return the columns whose names match any of the provided keywords."""
    return [column for column in columns if any(keyword in column.lower() for keyword in keywords)]


def build_upload_column_warnings(raw_df: pd.DataFrame) -> list[str]:
    """Return upload-time warnings when required business columns are hard to identify."""
    columns = list(raw_df.columns)
    warnings: list[str] = []

    if columns and not find_column_keyword_matches(columns, DATE_COLUMN_KEYWORDS):
        warnings.append(
            "No obvious date-like column name was detected. Upload a CSV with a real date field or map the correct date column before running forecasts."
        )
    if columns and not find_column_keyword_matches(columns, REVENUE_COLUMN_KEYWORDS):
        warnings.append(
            "No obvious revenue-like column name was detected. Choose the numeric sales or revenue column carefully before continuing."
        )
    return warnings


def build_mapping_selection_error(date_col: str, revenue_col: str) -> str | None:
    """Return a blocking error for invalid required-column selections."""
    if date_col == revenue_col:
        return "Date column and Revenue column must be different fields. Choose a real date field and a separate numeric revenue field."
    return None


def build_mapping_validation_warnings(
    raw_df: pd.DataFrame,
    *,
    date_col: str,
    revenue_col: str,
    sample_size: int = MAPPING_SAMPLE_SIZE,
) -> list[str]:
    """Return column-mapping warnings based on sample parseability checks."""
    warnings: list[str] = []

    date_sample = raw_df[date_col].dropna().head(sample_size)
    if date_sample.empty:
        warnings.append(
            f"The selected date column '{date_col}' is empty in the sampled rows. Choose a populated date field before continuing."
        )
    else:
        parsed_dates = pd.to_datetime(date_sample, errors="coerce", format="mixed")
        parsed_date_count = int(parsed_dates.notna().sum())
        if parsed_date_count == 0:
            warnings.append(
                f"The selected date column '{date_col}' did not parse as dates in the first {len(date_sample)} sampled values. Choose a real date field before running the analysis."
            )
        elif parsed_date_count < len(date_sample):
            warnings.append(
                f"The selected date column '{date_col}' only parsed {parsed_date_count} of the first {len(date_sample)} sampled values. Some rows may be removed during cleaning."
            )

    revenue_sample = raw_df[revenue_col].dropna().head(sample_size)
    if revenue_sample.empty:
        warnings.append(
            f"The selected revenue column '{revenue_col}' is empty in the sampled rows. Choose a populated numeric field before continuing."
        )
    else:
        parsed_revenue = pd.to_numeric(revenue_sample, errors="coerce")
        parsed_revenue_count = int(parsed_revenue.notna().sum())
        if parsed_revenue_count == 0:
            warnings.append(
                f"The selected revenue column '{revenue_col}' did not parse as numbers in the first {len(revenue_sample)} sampled values. Choose a numeric sales or revenue field."
            )
        elif parsed_revenue_count < len(revenue_sample):
            warnings.append(
                f"The selected revenue column '{revenue_col}' only parsed {parsed_revenue_count} of the first {len(revenue_sample)} sampled values. Some rows may be removed during cleaning."
            )

    return warnings


def build_empty_result_error_message(
    quality_report: DataQualityReport,
    *,
    date_col: str,
    revenue_col: str,
) -> str:
    """Explain why no rows remain after cleaning or filtering."""
    if quality_report.final_row_count > 0:
        return "No rows match the current filters. Clear or relax the filters to continue."

    original_row_count = quality_report.original_row_count
    if original_row_count > 0 and quality_report.invalid_date_rows_removed == original_row_count:
        return (
            f"No usable rows remain because the selected date column '{date_col}' could not be parsed as dates. "
            "Choose a different date field or upload a CSV with a real date column."
        )
    if original_row_count > 0 and quality_report.invalid_revenue_rows_removed == original_row_count:
        return (
            f"No usable rows remain because the selected revenue column '{revenue_col}' could not be parsed as numbers. "
            "Choose a numeric revenue field before continuing."
        )
    if original_row_count > 0 and quality_report.total_rows_removed_for_invalid_data == original_row_count:
        return (
            "All rows were removed during cleaning because the selected date or revenue values were invalid. "
            "Check the column mapping and the uploaded CSV contents, then try again."
        )
    return "No rows remain after cleaning. Check the selected date and revenue columns or upload a different CSV."


def get_dashboard_store() -> DashboardStore:
    """Return the local dashboard store, creating the runtime directory if needed."""
    return DashboardStore(SAVE_DASHBOARD_DB_PATH)


def rerun_app() -> None:
    """Trigger a Streamlit rerun with backward-compatible API support."""
    if hasattr(st, "rerun"):
        st.rerun()
        return
    st.experimental_rerun()


def _filter_selection_key(column: str) -> str:
    return f"dashboard_filter_values::{column}"


def _set_session_value(key: str, value: Any) -> None:
    st.session_state[key] = value


def _coerce_option(value: Any, options: list[Any], default: Any) -> Any:
    if value in options:
        return value
    return default


def _coerce_list(value: Any, options: list[str], default: list[str]) -> list[str]:
    if not isinstance(value, list):
        return default
    coerced = [str(item) for item in value if str(item) in options]
    if value and not coerced:
        return default
    return coerced


def clear_dynamic_filter_state() -> None:
    """Remove filter widget keys so a newly loaded dataset can rebuild them safely."""
    for key in [key for key in list(st.session_state.keys()) if key.startswith("dashboard_filter_values::")]:
        del st.session_state[key]


def normalize_loaded_ui_state(raw_df: pd.DataFrame, ui_state: dict[str, Any]) -> dict[str, Any]:
    """Coerce a saved UI state so it matches the current dataset and widget options."""
    columns = list(raw_df.columns)
    if not columns:
        return {
            "source_mode": _coerce_option(ui_state.get("source_mode"), ["Bundled demo dataset", "Upload CSV", "Saved dashboard"], "Saved dashboard"),
            "dashboard_name": ui_state.get("dashboard_name", "Untitled dashboard"),
            "source_name": ui_state.get("source_name"),
            "source_type": ui_state.get("source_type"),
            "date_col": ui_state.get("date_col"),
            "revenue_col": ui_state.get("revenue_col"),
            "transactions_col": ui_state.get("transactions_col", "None"),
            "holiday_col": ui_state.get("holiday_col", "None"),
            "promotion_col": ui_state.get("promotion_col", "None"),
            "filter_columns": [],
            "frequency": _coerce_option(ui_state.get("frequency"), AVAILABLE_FREQUENCIES, "Daily"),
            "overview_dimension": None,
            "forecast_methods": AVAILABLE_FORECAST_METHODS.copy(),
            "forecast_primary_method": ui_state.get("forecast_primary_method", AVAILABLE_FORECAST_METHODS[0]),
            "forecast_horizon": _coerce_option(ui_state.get("forecast_horizon"), AVAILABLE_HORIZONS, 7),
            "forecast_confidence": _coerce_option(ui_state.get("forecast_confidence"), AVAILABLE_CONFIDENCE_LEVELS, 0.95),
            "forecast_segment_dimension": "None",
            "forecast_window": ui_state.get("forecast_window", 7),
            "forecast_use_trend": bool(ui_state.get("forecast_use_trend", True)),
            "forecast_use_seasonality": bool(ui_state.get("forecast_use_seasonality", False)),
            "anomaly_window": ui_state.get("anomaly_window", 14),
            "anomaly_threshold": ui_state.get("anomaly_threshold", 3.0),
            "filter_values": {},
        }

    candidate_filter_columns = detect_categorical_columns(
        raw_df,
        exclude_columns=[
            col
            for col in [
                ui_state.get("date_col"),
                ui_state.get("revenue_col"),
                ui_state.get("transactions_col"),
                ui_state.get("holiday_col"),
                ui_state.get("promotion_col"),
            ]
            if isinstance(col, str)
        ],
    )
    filter_columns = _coerce_list(ui_state.get("filter_columns"), candidate_filter_columns, [])

    normalized_filter_values: dict[str, list[str]] = {}
    raw_filter_values = ui_state.get("filter_values", {})
    if isinstance(raw_filter_values, dict):
        for column in filter_columns:
            options = sorted(raw_df[column].dropna().astype(str).unique().tolist()) if column in raw_df.columns else []
            selected_values = [str(value) for value in raw_filter_values.get(column, []) if str(value) in options]
            if selected_values or not raw_filter_values.get(column):
                normalized_filter_values[column] = selected_values
            else:
                normalized_filter_values[column] = options

    selected_methods = _coerce_list(ui_state.get("forecast_methods"), AVAILABLE_FORECAST_METHODS, AVAILABLE_FORECAST_METHODS.copy())
    if not selected_methods:
        selected_methods = AVAILABLE_FORECAST_METHODS.copy()

    primary_method = ui_state.get("forecast_primary_method", selected_methods[0])
    if primary_method not in selected_methods:
        primary_method = selected_methods[0]

    segment_dimension = ui_state.get("forecast_segment_dimension", "None")
    available_segments = ["None", *candidate_filter_columns]
    if segment_dimension not in available_segments:
        segment_dimension = "None"

    frequency = _coerce_option(ui_state.get("frequency"), AVAILABLE_FREQUENCIES, "Daily")
    horizon = _coerce_option(ui_state.get("forecast_horizon"), AVAILABLE_HORIZONS, 7)
    confidence_level = _coerce_option(ui_state.get("forecast_confidence"), AVAILABLE_CONFIDENCE_LEVELS, 0.95)

    normalized_state: dict[str, Any] = {
        "source_mode": _coerce_option(ui_state.get("source_mode"), ["Bundled demo dataset", "Upload CSV", "Saved dashboard"], "Saved dashboard"),
        "dashboard_name": ui_state.get("dashboard_name", "Untitled dashboard"),
        "source_name": ui_state.get("source_name"),
        "source_type": ui_state.get("source_type"),
        "date_col": _coerce_option(ui_state.get("date_col"), columns, default_column(columns, ["date", "day", "period"])),
        "revenue_col": _coerce_option(ui_state.get("revenue_col"), columns, default_column(columns, ["revenue", "sales", "amount", "total"])),
        "transactions_col": _coerce_option(ui_state.get("transactions_col"), ["None", *columns], "None"),
        "holiday_col": _coerce_option(ui_state.get("holiday_col"), ["None", *columns], "None"),
        "promotion_col": _coerce_option(ui_state.get("promotion_col"), ["None", *columns], "None"),
        "filter_columns": filter_columns,
        "frequency": frequency,
        "overview_dimension": ui_state.get("overview_dimension") if ui_state.get("overview_dimension") in candidate_filter_columns else None,
        "forecast_methods": selected_methods,
        "forecast_primary_method": primary_method,
        "forecast_horizon": horizon,
        "forecast_confidence": confidence_level,
        "forecast_segment_dimension": segment_dimension,
        "forecast_window": ui_state.get("forecast_window", 7),
        "forecast_use_trend": bool(ui_state.get("forecast_use_trend", True)),
        "forecast_use_seasonality": bool(ui_state.get("forecast_use_seasonality", False)),
        "anomaly_window": ui_state.get("anomaly_window", 14),
        "anomaly_threshold": ui_state.get("anomaly_threshold", 3.0),
        "filter_values": normalized_filter_values,
    }

    return normalized_state


def apply_loaded_ui_state(raw_df: pd.DataFrame, ui_state: dict[str, Any]) -> None:
    """Apply a saved UI state to Streamlit session state before widgets render."""
    normalized = normalize_loaded_ui_state(raw_df, ui_state)
    clear_dynamic_filter_state()

    for key, value in [
        (DATA_SOURCE_MODE_KEY, normalized["source_mode"]),
        (DASHBOARD_NAME_KEY, normalized["dashboard_name"]),
        (SOURCE_NAME_KEY, normalized.get("source_name")),
        (SOURCE_TYPE_KEY, normalized.get("source_type")),
        (DATE_COL_KEY, normalized["date_col"]),
        (REVENUE_COL_KEY, normalized["revenue_col"]),
        (TRANSACTIONS_COL_KEY, normalized["transactions_col"]),
        (HOLIDAY_COL_KEY, normalized["holiday_col"]),
        (PROMOTION_COL_KEY, normalized["promotion_col"]),
        (FILTER_COLUMNS_KEY, normalized["filter_columns"]),
        (FREQUENCY_KEY, normalized["frequency"]),
        (OVERVIEW_DIMENSION_KEY, normalized.get("overview_dimension")),
        (FORECAST_METHODS_KEY, normalized["forecast_methods"]),
        (FORECAST_PRIMARY_METHOD_KEY, normalized["forecast_primary_method"]),
        (FORECAST_HORIZON_KEY, normalized["forecast_horizon"]),
        (FORECAST_CONFIDENCE_KEY, normalized["forecast_confidence"]),
        (FORECAST_SEGMENT_KEY, normalized["forecast_segment_dimension"]),
        (FORECAST_WINDOW_KEY, normalized["forecast_window"]),
        (FORECAST_USE_TREND_KEY, normalized["forecast_use_trend"]),
        (FORECAST_USE_SEASONALITY_KEY, normalized["forecast_use_seasonality"]),
        (ANOMALY_WINDOW_KEY, normalized["anomaly_window"]),
        (ANOMALY_THRESHOLD_KEY, normalized["anomaly_threshold"]),
    ]:
        _set_session_value(key, value)

    for column, selected_values in normalized["filter_values"].items():
        _set_session_value(_filter_selection_key(column), selected_values)


def apply_saved_dashboard_record(record: SavedDashboardRecord, raw_df: pd.DataFrame) -> None:
    """Restore a saved dashboard snapshot and mark it as the active saved source."""
    apply_loaded_ui_state(raw_df, record.ui_state)
    _set_session_value(DATA_SOURCE_MODE_KEY, "Saved dashboard")
    _set_session_value(SAVED_DASHBOARD_SELECTION_KEY, record.name)
    _set_session_value(RAW_CSV_BYTES_KEY, record.raw_csv_bytes)
    _set_session_value(RAW_DF_CACHE_KEY, raw_df)
    _set_session_value(RAW_FILE_NAME_KEY, record.raw_file_name)
    _set_session_value(SOURCE_TYPE_KEY, record.source_type)
    _set_session_value(SOURCE_NAME_KEY, record.name)
    _set_session_value(ACTIVE_SAVED_DASHBOARD_KEY, record.name)


def collect_dashboard_ui_state(filter_columns: list[str]) -> dict[str, Any]:
    """Capture the currently rendered widget state for persistence."""
    filter_values = {
        column: list(st.session_state.get(_filter_selection_key(column), []))
        for column in filter_columns
    }
    forecast_methods = st.session_state.get(FORECAST_METHODS_KEY, AVAILABLE_FORECAST_METHODS)
    if not isinstance(forecast_methods, list):
        forecast_methods = AVAILABLE_FORECAST_METHODS.copy()
    return {
        "source_mode": st.session_state.get(DATA_SOURCE_MODE_KEY, "Bundled demo dataset"),
        "dashboard_name": st.session_state.get(DASHBOARD_NAME_KEY, "Untitled dashboard"),
        "source_name": st.session_state.get(SOURCE_NAME_KEY),
        "source_type": st.session_state.get(SOURCE_TYPE_KEY),
        "date_col": st.session_state.get(DATE_COL_KEY),
        "revenue_col": st.session_state.get(REVENUE_COL_KEY),
        "transactions_col": st.session_state.get(TRANSACTIONS_COL_KEY),
        "holiday_col": st.session_state.get(HOLIDAY_COL_KEY),
        "promotion_col": st.session_state.get(PROMOTION_COL_KEY),
        "filter_columns": list(filter_columns),
        "frequency": st.session_state.get(FREQUENCY_KEY, "Daily"),
        "overview_dimension": st.session_state.get(OVERVIEW_DIMENSION_KEY),
        "forecast_methods": list(forecast_methods),
        "forecast_primary_method": st.session_state.get(FORECAST_PRIMARY_METHOD_KEY),
        "forecast_horizon": st.session_state.get(FORECAST_HORIZON_KEY, 7),
        "forecast_confidence": st.session_state.get(FORECAST_CONFIDENCE_KEY, 0.95),
        "forecast_segment_dimension": st.session_state.get(FORECAST_SEGMENT_KEY, "None"),
        "forecast_window": st.session_state.get(FORECAST_WINDOW_KEY, 7),
        "forecast_use_trend": bool(st.session_state.get(FORECAST_USE_TREND_KEY, True)),
        "forecast_use_seasonality": bool(st.session_state.get(FORECAST_USE_SEASONALITY_KEY, False)),
        "anomaly_window": st.session_state.get(ANOMALY_WINDOW_KEY, 14),
        "anomaly_threshold": st.session_state.get(ANOMALY_THRESHOLD_KEY, 3.0),
        "filter_values": filter_values,
    }


def _build_dashboard_load_result(
    *,
    raw_csv_bytes: bytes,
    source_type: str,
    source_name: str,
    raw_file_name: str | None,
) -> DashboardLoadResult:
    raw_df, warnings, error = read_uploaded_csv_bytes(raw_csv_bytes)
    if error:
        raise ValueError(error)
    for warning in warnings:
        st.sidebar.warning(warning)
    _set_session_value(RAW_CSV_BYTES_KEY, raw_csv_bytes)
    _set_session_value(RAW_DF_CACHE_KEY, raw_df)
    _set_session_value(RAW_FILE_NAME_KEY, raw_file_name)
    _set_session_value(SOURCE_TYPE_KEY, source_type)
    _set_session_value(SOURCE_NAME_KEY, source_name)
    _set_session_value(DATA_SOURCE_MODE_KEY, source_type_to_mode(source_type))
    return DashboardLoadResult(
        raw_df=raw_df,
        raw_csv_bytes=raw_csv_bytes,
        source_type=source_type,
        source_name=source_name,
        raw_file_name=raw_file_name,
    )


def source_type_to_mode(source_type: str) -> str:
    """Map a stored source type to the sidebar data-source label."""
    if source_type == "saved_dashboard":
        return "Saved dashboard"
    if source_type == "uploaded_csv":
        return "Upload CSV"
    return "Bundled demo dataset"


def build_dashboard_save_snapshot(filter_columns: list[str]) -> dict[str, Any]:
    """Build the JSON-serializable UI snapshot saved alongside the CSV bytes."""
    return collect_dashboard_ui_state(filter_columns)


def save_current_dashboard(
    *,
    dashboard_name: str,
    raw_csv_bytes: bytes,
    source_type: str,
    raw_file_name: str | None,
    filter_columns: list[str],
) -> SavedDashboardRecord:
    """Persist the current dashboard snapshot to SQLite."""
    store = get_dashboard_store()
    ui_state = build_dashboard_save_snapshot(filter_columns)
    return store.save_dashboard(
        name=dashboard_name,
        source_type=source_type,
        raw_csv_bytes=raw_csv_bytes,
        ui_state=ui_state,
        raw_file_name=raw_file_name,
    )


def load_saved_dashboard_record(dashboard_name: str) -> SavedDashboardRecord:
    """Load a saved dashboard snapshot from SQLite."""
    return get_dashboard_store().load_dashboard(dashboard_name)


def list_saved_dashboards() -> list[SavedDashboardSummary]:
    """Return the saved dashboards available for loading."""
    return get_dashboard_store().list_dashboards()


def delete_saved_dashboard(dashboard_name: str) -> bool:
    """Delete a saved dashboard by name."""
    return get_dashboard_store().delete_dashboard(dashboard_name)


def process_pending_saved_dashboard_actions() -> DashboardLoadResult | None:
    """Apply any deferred saved-dashboard action before widgets render."""
    pending_delete = st.session_state.get(PENDING_SAVED_DASHBOARD_DELETE_KEY)
    if pending_delete:
        removed = False
        try:
            removed = delete_saved_dashboard(str(pending_delete))
        except Exception as exc:
            st.sidebar.error(f"Could not delete saved dashboard '{pending_delete}': {exc}")
        finally:
            st.session_state.pop(PENDING_SAVED_DASHBOARD_DELETE_KEY, None)

        if removed:
            st.sidebar.success(f"Deleted saved dashboard '{pending_delete}'.")
        else:
            st.sidebar.warning(f"Could not find saved dashboard '{pending_delete}'.")

        if st.session_state.get(ACTIVE_SAVED_DASHBOARD_KEY) == pending_delete:
            _set_session_value(RAW_CSV_BYTES_KEY, b"")
            _set_session_value(RAW_DF_CACHE_KEY, pd.DataFrame())
            _set_session_value(RAW_FILE_NAME_KEY, None)
            _set_session_value(SOURCE_NAME_KEY, "")
            _set_session_value(ACTIVE_SAVED_DASHBOARD_KEY, "")
        return None

    pending_load = st.session_state.get(PENDING_SAVED_DASHBOARD_LOAD_KEY)
    if not pending_load:
        return None

    st.session_state.pop(PENDING_SAVED_DASHBOARD_LOAD_KEY, None)
    try:
        record = load_saved_dashboard_record(str(pending_load))
    except KeyError as exc:
        st.sidebar.error(str(exc))
        return None

    raw_df, warnings, error = read_uploaded_csv_bytes(record.raw_csv_bytes)
    if error:
        st.sidebar.error(error)
        return None

    for warning in warnings:
        st.sidebar.warning(warning)

    apply_saved_dashboard_record(record, raw_df)
    st.sidebar.success(f"Loaded saved dashboard '{record.name}' from {record.updated_at}.")
    return DashboardLoadResult(
        raw_df=raw_df,
        raw_csv_bytes=record.raw_csv_bytes,
        source_type=record.source_type,
        source_name=record.name,
        raw_file_name=record.raw_file_name,
    )


def prime_state_for_source(raw_df: pd.DataFrame, *, dashboard_name: str | None = None) -> None:
    """Set safe defaults for widgets tied to the current raw dataset."""
    clear_dynamic_filter_state()
    columns = list(raw_df.columns)
    _set_session_value(DATE_COL_KEY, default_column(columns, ["date", "day", "period"]))
    _set_session_value(REVENUE_COL_KEY, default_column(columns, ["revenue", "sales", "amount", "total"]))
    _set_session_value(TRANSACTIONS_COL_KEY, optional_default_column(columns, ["transaction", "orders", "quantity", "units"]))
    _set_session_value(HOLIDAY_COL_KEY, optional_default_column(columns, ["holiday", "festive", "event"]))
    _set_session_value(PROMOTION_COL_KEY, optional_default_column(columns, ["promotion", "promo", "campaign", "discount"]))

    candidate_filter_columns = detect_categorical_columns(
        raw_df,
        exclude_columns=[
            col
            for col in [
                st.session_state.get(DATE_COL_KEY),
                st.session_state.get(REVENUE_COL_KEY),
                st.session_state.get(TRANSACTIONS_COL_KEY) if st.session_state.get(TRANSACTIONS_COL_KEY) != "None" else None,
                st.session_state.get(HOLIDAY_COL_KEY) if st.session_state.get(HOLIDAY_COL_KEY) != "None" else None,
                st.session_state.get(PROMOTION_COL_KEY) if st.session_state.get(PROMOTION_COL_KEY) != "None" else None,
            ]
            if isinstance(col, str)
        ],
    )
    preferred_filter_columns = [col for col in ["product_category", "store_id", "product_id"] if col in candidate_filter_columns]
    _set_session_value(FILTER_COLUMNS_KEY, preferred_filter_columns)
    _set_session_value(FREQUENCY_KEY, "Daily")
    _set_session_value(FORECAST_METHODS_KEY, AVAILABLE_FORECAST_METHODS.copy())
    _set_session_value(FORECAST_PRIMARY_METHOD_KEY, "Linear Regression")
    _set_session_value(FORECAST_SEGMENT_KEY, "None")
    _set_session_value(OVERVIEW_DIMENSION_KEY, preferred_filter_columns[0] if preferred_filter_columns else None)
    _set_session_value(DASHBOARD_NAME_KEY, dashboard_name or "Untitled dashboard")


def render_dashboard_save_panel(filter_columns: list[str]) -> None:
    """Render the save controls for the current dashboard snapshot."""
    render_help_heading("Save Dashboard", "Name and save the current dashboard state so it can be reopened later.", container=st.sidebar, level="header")
    st.sidebar.caption("Saved dashboards are stored locally in the app runtime database.")
    _set_session_value(DASHBOARD_NAME_KEY, st.session_state.get(DASHBOARD_NAME_KEY, "Untitled dashboard"))
    dashboard_name = st.sidebar.text_input(
        "Dashboard name",
        key=DASHBOARD_NAME_KEY,
        help="Give the current dashboard a memorable name before saving it.",
    )

    can_save = bool(st.session_state.get(RAW_CSV_BYTES_KEY))
    if st.sidebar.button("Save dashboard", type="primary", disabled=not can_save):
        raw_csv_bytes = st.session_state.get(RAW_CSV_BYTES_KEY)
        if not raw_csv_bytes:
            st.sidebar.error("Load a CSV first before saving a dashboard.")
            return

        try:
            record = save_current_dashboard(
                dashboard_name=dashboard_name,
                raw_csv_bytes=raw_csv_bytes,
                source_type=str(st.session_state.get(DATA_SOURCE_MODE_KEY, "Bundled demo dataset")),
                raw_file_name=st.session_state.get(RAW_FILE_NAME_KEY),
                filter_columns=filter_columns,
            )
        except (ValueError, OSError) as exc:
            st.sidebar.error(str(exc))
            return

        st.sidebar.success(f"Saved '{record.name}' and updated the local dashboard store.")


def load_dashboard_source_from_sidebar() -> DashboardLoadResult:
    """Render the source selector and load the selected CSV payload."""
    render_help_heading("1. Data Source", HELP_TEXT["data_source"], container=st.sidebar, level="header")
    pending_result = process_pending_saved_dashboard_actions()
    if pending_result is not None:
        return pending_result

    available_source_modes = ["Bundled demo dataset", "Upload CSV", "Saved dashboard"]
    current_mode = st.session_state.get(DATA_SOURCE_MODE_KEY, available_source_modes[0])
    if current_mode not in available_source_modes:
        current_mode = available_source_modes[0]
        _set_session_value(DATA_SOURCE_MODE_KEY, current_mode)
    source_mode = help_selectbox(
        "Dataset source",
        "Choose bundled data for guided practice, upload your own CSV, or reopen a saved dashboard snapshot.",
        options=available_source_modes,
        container=st.sidebar,
        index=available_source_modes.index(current_mode),
        key=DATA_SOURCE_MODE_KEY,
    )

    if source_mode == "Saved dashboard":
        saved_dashboards = list_saved_dashboards()
        dashboard_names = [summary.name for summary in saved_dashboards]
        options = ["Select a saved dashboard", *dashboard_names]
        current_selection = st.session_state.get(SAVED_DASHBOARD_SELECTION_KEY, options[0])
        if current_selection not in options:
            current_selection = options[0]
            _set_session_value(SAVED_DASHBOARD_SELECTION_KEY, current_selection)

        saved_dashboard_name = help_selectbox(
            "Saved dashboard",
            "Pick a previously saved dashboard snapshot.",
            options=options,
            container=st.sidebar,
            index=options.index(current_selection),
            key=SAVED_DASHBOARD_SELECTION_KEY,
        )

        if not dashboard_names:
            st.sidebar.info("No saved dashboards yet. Save one after loading data.")
            return DashboardLoadResult(pd.DataFrame(), b"", "saved_dashboard", "", None)

        button_columns = st.sidebar.columns(2)
        load_clicked = button_columns[0].button("Load selected dashboard")
        delete_clicked = button_columns[1].button("Delete selected dashboard")
        if saved_dashboard_name == "Select a saved dashboard":
            st.sidebar.info("Choose a saved dashboard, then click Load.")
            return DashboardLoadResult(pd.DataFrame(), b"", "saved_dashboard", "", None)

        if delete_clicked:
            st.session_state[PENDING_SAVED_DASHBOARD_DELETE_KEY] = saved_dashboard_name
            rerun_app()

        active_saved_dashboard = st.session_state.get(ACTIVE_SAVED_DASHBOARD_KEY)
        raw_df_cache = st.session_state.get(RAW_DF_CACHE_KEY)
        current_raw_csv_bytes = st.session_state.get(RAW_CSV_BYTES_KEY, b"")
        has_cached_dashboard = (
            saved_dashboard_name == active_saved_dashboard
            and isinstance(raw_df_cache, pd.DataFrame)
            and not raw_df_cache.empty
            and bool(current_raw_csv_bytes)
        )

        if load_clicked:
            st.session_state[PENDING_SAVED_DASHBOARD_LOAD_KEY] = saved_dashboard_name
            rerun_app()

        if not has_cached_dashboard:
            st.sidebar.info("Select a saved dashboard and click Load to restore it.")
            return DashboardLoadResult(pd.DataFrame(), b"", "saved_dashboard", saved_dashboard_name, None)

        cached_raw_df = st.session_state.get(RAW_DF_CACHE_KEY)
        if isinstance(cached_raw_df, pd.DataFrame):
            return DashboardLoadResult(
                raw_df=cached_raw_df,
                raw_csv_bytes=current_raw_csv_bytes,
                source_type=str(st.session_state.get(SOURCE_TYPE_KEY, "saved_dashboard")),
                source_name=saved_dashboard_name,
                raw_file_name=st.session_state.get(RAW_FILE_NAME_KEY),
            )
        return DashboardLoadResult(pd.DataFrame(), b"", "saved_dashboard", saved_dashboard_name, None)

    if source_mode == "Upload CSV":
        uploaded_file = help_file_uploader(
            "Upload sales CSV",
            "Upload a comma-separated file that contains at least one date column and one revenue column.",
            container=st.sidebar,
            type=["csv"],
        )
        if uploaded_file is None:
            st.sidebar.info("Choose a CSV file to start working with uploaded data.")
            return DashboardLoadResult(pd.DataFrame(), b"", "uploaded_csv", "", None)

        raw_csv_bytes = uploaded_file.getvalue()
        cached_matches = (
            st.session_state.get(SOURCE_TYPE_KEY) == "uploaded_csv"
            and st.session_state.get(SOURCE_NAME_KEY) == uploaded_file.name
            and st.session_state.get(RAW_CSV_BYTES_KEY) == raw_csv_bytes
            and isinstance(st.session_state.get(RAW_DF_CACHE_KEY), pd.DataFrame)
            and not st.session_state.get(RAW_DF_CACHE_KEY).empty
        )
        if cached_matches:
            raw_df = st.session_state[RAW_DF_CACHE_KEY]
        else:
            raw_df, warnings, error = read_uploaded_csv_bytes(raw_csv_bytes)
            if error:
                st.sidebar.error(error)
                return DashboardLoadResult(pd.DataFrame(), b"", "uploaded_csv", uploaded_file.name, uploaded_file.name)

            for warning in warnings:
                st.sidebar.warning(warning)

            prime_state_for_source(raw_df, dashboard_name=uploaded_file.name.rsplit(".", 1)[0] if uploaded_file.name else None)
            _set_session_value(RAW_CSV_BYTES_KEY, raw_csv_bytes)
            _set_session_value(RAW_DF_CACHE_KEY, raw_df)
            _set_session_value(RAW_FILE_NAME_KEY, uploaded_file.name)
            _set_session_value(SOURCE_TYPE_KEY, "uploaded_csv")
            _set_session_value(SOURCE_NAME_KEY, uploaded_file.name)
            _set_session_value(ACTIVE_SAVED_DASHBOARD_KEY, "")
        return DashboardLoadResult(
            raw_df=raw_df,
            raw_csv_bytes=raw_csv_bytes,
            source_type="uploaded_csv",
            source_name=uploaded_file.name,
            raw_file_name=uploaded_file.name,
        )

    available_datasets = list(BUNDLED_DATASETS.keys())
    current_dataset = st.session_state.get(BUNDLED_DATASET_KEY, available_datasets[0])
    if current_dataset not in BUNDLED_DATASETS:
        current_dataset = available_datasets[0]
        _set_session_value(BUNDLED_DATASET_KEY, current_dataset)

    dataset_name = help_selectbox(
        "Bundled demo dataset",
        "Switch between curated demo datasets that highlight clean data, data quality issues, event features, or anomalies.",
        options=available_datasets,
        container=st.sidebar,
        index=available_datasets.index(current_dataset),
        key=BUNDLED_DATASET_KEY,
    )
    dataset_config = BUNDLED_DATASETS[dataset_name]

    st.sidebar.info("Using a bundled demo dataset.")
    st.sidebar.caption(dataset_config["description"])
    dataset_path = get_bundled_dataset_path(dataset_name)
    raw_csv_bytes = dataset_path.read_bytes()
    cached_matches = (
        st.session_state.get(SOURCE_TYPE_KEY) == "bundled_demo"
        and st.session_state.get(SOURCE_NAME_KEY) == dataset_name
        and st.session_state.get(RAW_CSV_BYTES_KEY) == raw_csv_bytes
        and isinstance(st.session_state.get(RAW_DF_CACHE_KEY), pd.DataFrame)
        and not st.session_state.get(RAW_DF_CACHE_KEY).empty
    )
    if cached_matches:
        raw_df = st.session_state[RAW_DF_CACHE_KEY]
    else:
        raw_df, warnings, error = read_uploaded_csv_bytes(raw_csv_bytes)
        if error:
            st.sidebar.error(str(error))
            return DashboardLoadResult(pd.DataFrame(), b"", "bundled_demo", dataset_name, dataset_config["file_name"])

        for warning in warnings:
            st.sidebar.warning(warning)

        prime_state_for_source(raw_df, dashboard_name=dataset_name)
        _set_session_value(RAW_CSV_BYTES_KEY, raw_csv_bytes)
        _set_session_value(RAW_DF_CACHE_KEY, raw_df)
        _set_session_value(RAW_FILE_NAME_KEY, dataset_config["file_name"])
        _set_session_value(SOURCE_TYPE_KEY, "bundled_demo")
        _set_session_value(SOURCE_NAME_KEY, dataset_name)
        _set_session_value(ACTIVE_SAVED_DASHBOARD_KEY, "")
    return DashboardLoadResult(
        raw_df=raw_df,
        raw_csv_bytes=raw_csv_bytes,
        source_type="bundled_demo",
        source_name=dataset_name,
        raw_file_name=dataset_config["file_name"],
    )


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
        page_title="ForeSightSeer Dashboard",
        layout="wide",
    )

    st.title("ForeSightSeer")
    st.subheader("AI-Driven Demand and Revenue Forecasting Dashboard")
    st.caption(
        "A practical dashboard for SMEs to clean sales data, monitor KPIs, forecast revenue, "
        "and detect unusual sales behavior."
    )

    load_result = load_sales_data()
    raw_df = load_result.raw_df
    if raw_df.empty:
        if len(raw_df.columns) > 0:
            st.error("The uploaded CSV has headers but no data rows. Add at least one row with a date and revenue value.")
        else:
            st.info(
                "Select a bundled dataset or upload a CSV file to begin. The guide below explains every chart and control."
            )
        guide_tabs = st.tabs(["Guide"])
        with guide_tabs[0]:
            render_guide_tab()
        return

    render_help_heading("Raw Data Preview", HELP_TEXT["raw_preview"], level="subheader")
    st.dataframe(raw_df.head(25), width="stretch")

    selections = render_sidebar_controls(raw_df)
    mapping_error = build_mapping_selection_error(selections["date_col"], selections["revenue_col"])
    if mapping_error:
        st.error(mapping_error)
        return

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
        st.error(
            build_empty_result_error_message(
                quality_report,
                date_col=selections["date_col"],
                revenue_col=selections["revenue_col"],
            )
        )
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

    render_dashboard_save_panel(selections["filter_columns"])


def load_sales_data() -> DashboardLoadResult:
    """Load uploaded CSV data or one of the bundled demo datasets."""
    load_result = load_dashboard_source_from_sidebar()
    return load_result


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

    default_date = default_column(columns, ["date", "day", "period"])
    if st.session_state.get(DATE_COL_KEY) not in columns:
        _set_session_value(DATE_COL_KEY, default_date)
    date_col = help_selectbox(
        "Date column",
        "Select the column that contains the sales dates or periods.",
        options=columns,
        container=st.sidebar,
        index=columns.index(st.session_state[DATE_COL_KEY]),
        key=DATE_COL_KEY,
    )
    default_revenue = default_column(columns, ["revenue", "sales", "amount", "total"])
    if st.session_state.get(REVENUE_COL_KEY) not in columns:
        _set_session_value(REVENUE_COL_KEY, default_revenue)
    revenue_col = help_selectbox(
        "Revenue column",
        "Select the numeric column that represents revenue or sales amount.",
        options=columns,
        container=st.sidebar,
        index=columns.index(st.session_state[REVENUE_COL_KEY]),
        key=REVENUE_COL_KEY,
    )
    mapping_error = build_mapping_selection_error(date_col, revenue_col)
    if mapping_error:
        st.sidebar.error(mapping_error)

    default_transactions = optional_default_column(columns, ["transaction", "orders", "quantity", "units"])
    optional_transaction_options = ["None", *columns]
    if st.session_state.get(TRANSACTIONS_COL_KEY) not in optional_transaction_options:
        _set_session_value(TRANSACTIONS_COL_KEY, default_transactions)
    for warning in build_mapping_validation_warnings(raw_df, date_col=date_col, revenue_col=revenue_col):
        st.sidebar.warning(warning)
    transactions_col_selection = help_selectbox(
        "Transactions column (optional)",
        "Choose transaction or order count if your CSV has one. It is used for transaction KPIs such as average order value.",
        options=optional_transaction_options,
        container=st.sidebar,
        index=optional_transaction_options.index(st.session_state[TRANSACTIONS_COL_KEY]),
        key=TRANSACTIONS_COL_KEY,
    )
    transactions_col = None if transactions_col_selection == "None" else transactions_col_selection
    default_holiday = optional_default_column(columns, ["holiday", "festive", "event"])
    if st.session_state.get(HOLIDAY_COL_KEY) not in optional_transaction_options:
        _set_session_value(HOLIDAY_COL_KEY, default_holiday)
    holiday_col_selection = help_selectbox(
        "Holiday column (optional)",
        "Optional binary or yes or no column used as an extra forecasting feature.",
        options=optional_transaction_options,
        container=st.sidebar,
        index=optional_transaction_options.index(st.session_state[HOLIDAY_COL_KEY]),
        key=HOLIDAY_COL_KEY,
    )
    holiday_col = None if holiday_col_selection == "None" else holiday_col_selection
    default_promotion = optional_default_column(columns, ["promotion", "promo", "campaign", "discount"])
    if st.session_state.get(PROMOTION_COL_KEY) not in optional_transaction_options:
        _set_session_value(PROMOTION_COL_KEY, default_promotion)
    promotion_col_selection = help_selectbox(
        "Promotion column (optional)",
        "Optional binary or yes or no promotion indicator used by Linear Regression.",
        options=optional_transaction_options,
        container=st.sidebar,
        index=optional_transaction_options.index(st.session_state[PROMOTION_COL_KEY]),
        key=PROMOTION_COL_KEY,
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
    current_filter_columns = st.session_state.get(FILTER_COLUMNS_KEY, preferred_filter_columns)
    if not isinstance(current_filter_columns, list):
        current_filter_columns = preferred_filter_columns
    current_filter_columns = [column for column in current_filter_columns if column in candidate_filter_columns]
    if not current_filter_columns and preferred_filter_columns:
        current_filter_columns = preferred_filter_columns
    _set_session_value(FILTER_COLUMNS_KEY, current_filter_columns)

    filter_columns = help_multiselect(
        "Filter/group columns (optional)",
        "Choose category columns such as product category, store, or product ID. These fields drive sidebar filters and comparison views.",
        options=candidate_filter_columns,
        container=st.sidebar,
        default=current_filter_columns,
        key=FILTER_COLUMNS_KEY,
    )
    render_help_heading("3. Aggregation", HELP_TEXT["aggregation"], container=st.sidebar, level="header")
    if st.session_state.get(FREQUENCY_KEY) not in AVAILABLE_FREQUENCIES:
        _set_session_value(FREQUENCY_KEY, "Daily")
    frequency = help_selectbox(
        "Aggregation frequency",
        "Choose how detailed or smooth the time series should be before charts and forecasts are computed.",
        ["Daily", "Weekly", "Monthly"],
        container=st.sidebar,
        index=AVAILABLE_FREQUENCIES.index(st.session_state[FREQUENCY_KEY]),
        key=FREQUENCY_KEY,
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
        current_values = st.session_state.get(_filter_selection_key(column), options)
        if not isinstance(current_values, list):
            current_values = options
        current_values = [value for value in current_values if value in options]
        if not current_values and st.session_state.get(_filter_selection_key(column)) not in ([], None):
            current_values = options
        _set_session_value(_filter_selection_key(column), current_values)
        selected_values = help_multiselect(
            column,
            f"Filter the cleaned dataset by {column}. All charts, KPIs, forecasts, and exports update to match the values selected here.",
            options=options,
            container=st.sidebar,
            default=current_values,
            key=_filter_selection_key(column),
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
        current_dimension = st.session_state.get(OVERVIEW_DIMENSION_KEY, available_dimensions[0])
        if current_dimension not in available_dimensions:
            current_dimension = available_dimensions[0]
            _set_session_value(OVERVIEW_DIMENSION_KEY, current_dimension)
        dimension = help_selectbox(
            "Revenue breakdown dimension",
            "Choose which category column should be compared in the bar chart below.",
            available_dimensions,
            key=OVERVIEW_DIMENSION_KEY,
            index=available_dimensions.index(current_dimension),
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
    st.caption(
        "Use this tab to answer the next planning question for the business: what should demand or revenue look like next, and how uncertain is that estimate?"
    )
    if time_series_df.empty:
        st.warning("No data is available for forecasting.")
        return ForecastResult("", pd.DataFrame(), pd.DataFrame(), None, None, ["No data available."])

    available_methods = AVAILABLE_FORECAST_METHODS
    current_methods = st.session_state.get(FORECAST_METHODS_KEY, available_methods)
    if not isinstance(current_methods, list):
        current_methods = available_methods.copy()
    current_methods = [method for method in current_methods if method in available_methods]
    if not current_methods:
        current_methods = available_methods.copy()
    _set_session_value(FORECAST_METHODS_KEY, current_methods)
    selected_methods = help_multiselect(
        "Models to evaluate",
        "Run one or more models on the same historical split so you can compare their accuracy fairly.",
        available_methods,
        default=current_methods,
        key=FORECAST_METHODS_KEY,
    )
    if not selected_methods:
        st.warning("Select at least one forecasting method.")
        return ForecastResult("", pd.DataFrame(), pd.DataFrame(), None, None, ["No forecasting method selected."])

    summary_controls = st.columns(4)
    current_primary_method = st.session_state.get(FORECAST_PRIMARY_METHOD_KEY, selected_methods[0])
    if current_primary_method not in selected_methods:
        current_primary_method = "Linear Regression" if "Linear Regression" in selected_methods else selected_methods[0]
        _set_session_value(FORECAST_PRIMARY_METHOD_KEY, current_primary_method)
    primary_method = help_selectbox(
        "Detailed model view",
        "Choose which model should drive the detailed chart and forecast tables below.",
        selected_methods,
        container=summary_controls[0],
        index=selected_methods.index(current_primary_method),
        key=FORECAST_PRIMARY_METHOD_KEY,
    )

    current_horizon = st.session_state.get(FORECAST_HORIZON_KEY, AVAILABLE_HORIZONS[0])
    if current_horizon not in AVAILABLE_HORIZONS:
        current_horizon = AVAILABLE_HORIZONS[0]
    _set_session_value(FORECAST_HORIZON_KEY, current_horizon)
    horizon = int(
        help_selectbox(
            "Future horizon",
            "How many future periods the forecast should project forward.",
            AVAILABLE_HORIZONS,
            container=summary_controls[1],
            index=AVAILABLE_HORIZONS.index(current_horizon),
            key=FORECAST_HORIZON_KEY,
        )
    )

    current_confidence = st.session_state.get(FORECAST_CONFIDENCE_KEY, AVAILABLE_CONFIDENCE_LEVELS[-1])
    if current_confidence not in AVAILABLE_CONFIDENCE_LEVELS:
        current_confidence = AVAILABLE_CONFIDENCE_LEVELS[-1]
    _set_session_value(FORECAST_CONFIDENCE_KEY, current_confidence)
    confidence_level = float(
        help_selectbox(
            "Confidence level",
            "Higher confidence levels produce wider uncertainty bands around forecast values.",
            AVAILABLE_CONFIDENCE_LEVELS,
            container=summary_controls[2],
            index=AVAILABLE_CONFIDENCE_LEVELS.index(current_confidence),
            key=FORECAST_CONFIDENCE_KEY,
        )
    )

    segment_candidates = detect_categorical_columns(
        filtered_df,
        exclude_columns=[col for col in ["date", "revenue", "transactions", holiday_col, promotion_col] if col],
    )
    current_segment_dimension = st.session_state.get(FORECAST_SEGMENT_KEY, "None")
    allowed_segments = ["None", *segment_candidates]
    if current_segment_dimension not in allowed_segments:
        current_segment_dimension = "None"
    _set_session_value(FORECAST_SEGMENT_KEY, current_segment_dimension)
    segment_dimension_selection = help_selectbox(
        "Segment comparison",
        "Optionally compare future forecasts across the top segments of one selected category column.",
        allowed_segments,
        container=summary_controls[3],
        index=allowed_segments.index(current_segment_dimension),
        key=FORECAST_SEGMENT_KEY,
    )

    option_columns = st.columns(3)
    max_window = max(2, min(30, len(time_series_df) - 1))
    default_window = min(7, max_window)
    current_window = st.session_state.get(FORECAST_WINDOW_KEY, default_window)
    if not isinstance(current_window, int) or current_window < 2 or current_window > max_window:
        current_window = default_window
    _set_session_value(FORECAST_WINDOW_KEY, current_window)
    window = int(
        help_slider(
            "Moving average window",
            "How many recent periods the Moving Average model should average when making each prediction.",
            2,
            max_window,
            current_window,
            container=option_columns[0],
            key=FORECAST_WINDOW_KEY,
        )
    )
    current_use_trend = bool(st.session_state.get(FORECAST_USE_TREND_KEY, True))
    _set_session_value(FORECAST_USE_TREND_KEY, current_use_trend)
    use_trend = help_checkbox(
        "Use trend",
        "Allow Exponential Smoothing to model steady upward or downward movement over time.",
        container=option_columns[1],
        value=current_use_trend,
        key=FORECAST_USE_TREND_KEY,
    )
    current_use_seasonality = bool(st.session_state.get(FORECAST_USE_SEASONALITY_KEY, False))
    _set_session_value(FORECAST_USE_SEASONALITY_KEY, current_use_seasonality)
    use_seasonality = help_checkbox(
        "Use seasonality",
        "Allow Exponential Smoothing to model repeating seasonal patterns when enough history exists.",
        container=option_columns[2],
        value=current_use_seasonality,
        key=FORECAST_USE_SEASONALITY_KEY,
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
    current_window = st.session_state.get(ANOMALY_WINDOW_KEY, min(14, max_window))
    if not isinstance(current_window, int) or current_window < 2 or current_window > max_window:
        current_window = min(14, max_window)
    _set_session_value(ANOMALY_WINDOW_KEY, current_window)
    window = int(
        help_slider(
            "Rolling window",
            "How many recent periods define normal behavior for anomaly detection.",
            2,
            max_window,
            current_window,
            container=control_columns[0],
            key=ANOMALY_WINDOW_KEY,
        )
    )
    current_threshold = st.session_state.get(ANOMALY_THRESHOLD_KEY, 3.0)
    if not isinstance(current_threshold, (int, float)) or current_threshold < 1.0 or current_threshold > 5.0:
        current_threshold = 3.0
    _set_session_value(ANOMALY_THRESHOLD_KEY, float(current_threshold))
    threshold = float(
        help_slider(
            "Anomaly threshold (absolute z-score)",
            "Higher thresholds flag fewer, more extreme anomalies; lower thresholds flag more potential anomalies.",
            1.0,
            5.0,
            float(current_threshold),
            0.1,
            container=control_columns[1],
            key=ANOMALY_THRESHOLD_KEY,
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
