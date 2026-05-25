from pathlib import Path

import pandas as pd
import pytest

from app import BUNDLED_DATASETS, get_bundled_dataset_path, load_bundled_dataset
from src.forecasting import prepare_forecast_frame, run_moving_average_forecast
from src.preprocessing import aggregate_sales_data, clean_sales_data


SAMPLE_DATA_DIR = Path(__file__).resolve().parents[1] / "sample_data"


def _load_and_clean(file_name: str) -> tuple[pd.DataFrame, object]:
    raw_df = pd.read_csv(SAMPLE_DATA_DIR / file_name)
    category_columns = [
        column
        for column in ["product_category", "store_id", "product_id"]
        if column in raw_df.columns
    ]
    extra_columns = [
        column
        for column in ["holiday_flag", "promotion_active"]
        if column in raw_df.columns
    ]
    return clean_sales_data(
        raw_df,
        date_col="date",
        revenue_col="revenue",
        transactions_col="transactions" if "transactions" in raw_df.columns else None,
        category_cols=category_columns,
        extra_cols=extra_columns,
    )


def test_bundled_sample_datasets_can_be_cleaned_and_aggregated() -> None:
    for file_name in [
        "sample_sales_data.csv",
        "sample_sales_data_quality_issues.csv",
        "sample_sales_data_event_features.csv",
        "sample_sales_data_anomalies.csv",
    ]:
        cleaned_df, report = _load_and_clean(file_name)

        assert not cleaned_df.empty
        assert report.final_row_count == len(cleaned_df)

        aggregated_df = aggregate_sales_data(
            cleaned_df,
            frequency="Daily",
            event_columns=[
                column
                for column in ["holiday_flag", "promotion_active"]
                if column in cleaned_df.columns
            ],
        )

        assert {"date", "revenue"}.issubset(aggregated_df.columns)
        assert not aggregated_df.empty


def test_showcase_datasets_have_enough_history_for_meaningful_forecast_slices() -> None:
    expectations = {
        "sample_sales_data_quality_issues.csv": {"min_periods": 55, "min_test_rows": 10},
        "sample_sales_data_event_features.csv": {"min_periods": 80, "min_test_rows": 15},
        "sample_sales_data_anomalies.csv": {"min_periods": 50, "min_test_rows": 10},
    }

    for file_name, expectation in expectations.items():
        cleaned_df, _ = _load_and_clean(file_name)
        aggregated_df = aggregate_sales_data(
            cleaned_df,
            frequency="Daily",
            event_columns=[
                column
                for column in ["holiday_flag", "promotion_active"]
                if column in cleaned_df.columns
            ],
        )

        assert aggregated_df["date"].nunique() >= expectation["min_periods"]

        forecast_result = run_moving_average_forecast(
            aggregated_df,
            horizon=7,
            frequency="Daily",
        )
        assert len(forecast_result.test_forecast) >= expectation["min_test_rows"]


def test_bundled_dataset_registry_points_to_existing_files() -> None:
    for dataset_name in BUNDLED_DATASETS:
        dataset_path = get_bundled_dataset_path(dataset_name)

        assert dataset_path.exists()
        assert not load_bundled_dataset(dataset_name).empty


def test_invalid_bundled_dataset_name_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Unknown bundled dataset"):
        get_bundled_dataset_path("not-a-real-dataset")


def test_quality_issues_sample_exercises_cleaning_paths() -> None:
    _, report = _load_and_clean("sample_sales_data_quality_issues.csv")

    assert report.duplicates_removed == 1
    assert report.invalid_date_rows_removed == 1
    assert report.invalid_revenue_rows_removed == 1
    assert report.negative_revenue_rows_removed == 1
    assert report.invalid_transaction_rows_normalized == 1
    assert report.negative_transaction_rows_clipped == 1


def test_anomaly_sample_triggers_missing_period_warning_in_forecast_frame() -> None:
    cleaned_df, _ = _load_and_clean("sample_sales_data_anomalies.csv")
    aggregated_df = aggregate_sales_data(
        cleaned_df,
        frequency="Daily",
        event_columns=["holiday_flag", "promotion_active"],
    )

    frame, warnings = prepare_forecast_frame(
        aggregated_df,
        frequency="Daily",
        event_columns=["holiday_flag", "promotion_active"],
    )

    assert not frame.empty
    assert warnings
    assert "missing period" in warnings[0].lower()