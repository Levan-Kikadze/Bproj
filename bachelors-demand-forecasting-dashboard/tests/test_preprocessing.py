import pandas as pd
import pytest

from src.preprocessing import aggregate_sales_data, clean_sales_data


def test_preprocessing_removes_invalid_dates_missing_revenue_and_negative_revenue():
    raw_df = pd.DataFrame(
        {
            "sale_date": ["2024-01-01", "not-a-date", "2024-01-03", "2024-01-04"],
            "sales": [100, 200, None, -10],
            "transactions": [5, 8, 2, 1],
            "category": ["A", "A", "B", "B"],
        }
    )

    cleaned_df, report = clean_sales_data(
        raw_df,
        date_col="sale_date",
        revenue_col="sales",
        transactions_col="transactions",
        category_cols=["category"],
    )

    assert len(cleaned_df) == 1
    assert report.invalid_date_rows_removed == 1
    assert report.invalid_revenue_rows_removed == 1
    assert report.negative_revenue_rows_removed == 1
    assert report.total_rows_removed_for_invalid_data == 3
    assert cleaned_df.iloc[0]["revenue"] == 100


def test_preprocessing_removes_duplicate_rows():
    raw_df = pd.DataFrame(
        {
            "date": ["2024-01-01", "2024-01-01", "2024-01-02"],
            "revenue": [100, 100, 150],
        }
    )

    cleaned_df, report = clean_sales_data(raw_df, date_col="date", revenue_col="revenue")

    assert len(cleaned_df) == 2
    assert report.duplicates_removed == 1


def test_preprocessing_counts_unique_removed_rows_when_issues_overlap():
    raw_df = pd.DataFrame(
        {
            "date": ["not-a-date"],
            "revenue": [None],
        }
    )

    _, report = clean_sales_data(raw_df, date_col="date", revenue_col="revenue")

    assert report.invalid_date_rows_removed == 1
    assert report.invalid_revenue_rows_removed == 1
    assert report.total_rows_removed_for_invalid_data == 1


def test_preprocessing_raises_clear_error_when_required_date_column_is_missing():
    raw_df = pd.DataFrame(
        {
            "sales": [100, 120],
            "transactions": [2, 3],
        }
    )

    with pytest.raises(ValueError, match=r"Missing required column\(s\): date"):
        clean_sales_data(raw_df, date_col="date", revenue_col="sales")


def test_preprocessing_returns_empty_dataframe_when_all_rows_are_removed():
    raw_df = pd.DataFrame(
        {
            "date": ["bad-date", None],
            "revenue": ["bad-number", -10],
        }
    )

    cleaned_df, report = clean_sales_data(raw_df, date_col="date", revenue_col="revenue")

    assert cleaned_df.empty
    assert report.final_row_count == 0
    assert report.total_rows_removed_for_invalid_data == 2


def test_preprocessing_reports_transaction_values_normalized_to_zero():
    raw_df = pd.DataFrame(
        {
            "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "revenue": [100, 120, 140],
            "transactions": ["bad", -5, None],
        }
    )

    cleaned_df, report = clean_sales_data(
        raw_df,
        date_col="date",
        revenue_col="revenue",
        transactions_col="transactions",
    )

    assert cleaned_df["transactions"].tolist() == [0.0, 0.0, 0.0]
    assert report.invalid_transaction_rows_normalized == 1
    assert report.negative_transaction_rows_clipped == 1
    assert report.missing_values_by_column["transactions"] == 1


def test_aggregation_daily_weekly_and_monthly():
    cleaned_df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-08", "2024-02-01"]),
            "revenue": [100, 150, 200, 300],
            "transactions": [5, 7, 10, 15],
        }
    )

    daily = aggregate_sales_data(cleaned_df, frequency="Daily")
    weekly = aggregate_sales_data(cleaned_df, frequency="Weekly")
    monthly = aggregate_sales_data(cleaned_df, frequency="Monthly")

    assert daily["revenue"].sum() == 750
    assert weekly.loc[weekly["date"] == pd.Timestamp("2024-01-01"), "revenue"].iloc[0] == 250
    assert monthly.loc[monthly["date"] == pd.Timestamp("2024-01-01"), "transactions"].iloc[0] == 22


def test_aggregation_rejects_invalid_frequency():
    cleaned_df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01", "2024-01-02"]),
            "revenue": [100, 120],
        }
    )

    with pytest.raises(ValueError, match="frequency must be one of"):
        aggregate_sales_data(cleaned_df, frequency="Quarterly")


def test_preprocessing_preserves_extra_event_columns():
    raw_df = pd.DataFrame(
        {
            "date": ["2024-01-01", "2024-01-02"],
            "revenue": [100, 120],
            "promotion_active": [1, 0],
            "holiday_flag": [0, 1],
        }
    )

    cleaned_df, _ = clean_sales_data(
        raw_df,
        date_col="date",
        revenue_col="revenue",
        extra_cols=["promotion_active", "holiday_flag"],
    )

    assert {"promotion_active", "holiday_flag"}.issubset(cleaned_df.columns)


def test_aggregation_keeps_event_columns_with_max_signal():
    cleaned_df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01", "2024-01-01", "2024-01-02"]),
            "revenue": [100, 50, 200],
            "promotion_active": [0, 1, 0],
            "holiday_flag": [0, 0, 1],
        }
    )

    aggregated = aggregate_sales_data(
        cleaned_df,
        frequency="Daily",
        event_columns=["promotion_active", "holiday_flag"],
    )

    assert aggregated.loc[aggregated["date"] == pd.Timestamp("2024-01-01"), "promotion_active"].iloc[0] == 1
    assert aggregated.loc[aggregated["date"] == pd.Timestamp("2024-01-02"), "holiday_flag"].iloc[0] == 1

