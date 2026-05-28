import pandas as pd

from app import (
    build_empty_result_error_message,
    build_mapping_selection_error,
    build_mapping_validation_warnings,
    build_upload_column_warnings,
    read_uploaded_csv_bytes,
)
from src.preprocessing import DataQualityReport


def test_upload_column_warnings_flag_missing_date_like_columns() -> None:
    raw_df = pd.DataFrame({"store": ["A"], "sales_amount": [120.0]})

    warnings = build_upload_column_warnings(raw_df)

    assert any("date-like" in warning for warning in warnings)


def test_mapping_selection_error_requires_distinct_date_and_revenue_columns() -> None:
    assert build_mapping_selection_error("sales", "sales") is not None


def test_mapping_validation_warnings_flag_unparseable_date_selection() -> None:
    raw_df = pd.DataFrame(
        {
            "region": ["north", "south", "east"],
            "sales": [100, 120, 140],
        }
    )

    warnings = build_mapping_validation_warnings(raw_df, date_col="region", revenue_col="sales")

    assert any("did not parse as dates" in warning for warning in warnings)


def test_empty_result_error_message_explains_date_mapping_failure() -> None:
    report = DataQualityReport(
        original_row_count=3,
        final_row_count=0,
        duplicates_removed=0,
        invalid_date_rows_removed=3,
        invalid_revenue_rows_removed=0,
        negative_revenue_rows_removed=0,
        invalid_transaction_rows_normalized=0,
        negative_transaction_rows_clipped=0,
        missing_values_by_column={},
        date_range_start=None,
        date_range_end=None,
    )

    message = build_empty_result_error_message(report, date_col="region", revenue_col="sales")

    assert "could not be parsed as dates" in message


def test_empty_result_error_message_distinguishes_filter_removal() -> None:
    report = DataQualityReport(
        original_row_count=5,
        final_row_count=5,
        duplicates_removed=0,
        invalid_date_rows_removed=0,
        invalid_revenue_rows_removed=0,
        negative_revenue_rows_removed=0,
        invalid_transaction_rows_normalized=0,
        negative_transaction_rows_clipped=0,
        missing_values_by_column={},
        date_range_start=pd.Timestamp("2024-01-01"),
        date_range_end=pd.Timestamp("2024-01-05"),
    )

    message = build_empty_result_error_message(report, date_col="date", revenue_col="revenue")

    assert "current filters" in message


def test_read_uploaded_csv_bytes_rejects_empty_file() -> None:
    raw_df, warnings, error = read_uploaded_csv_bytes(b"")

    assert raw_df.empty
    assert not warnings
    assert error is not None and "empty" in error.lower()


def test_read_uploaded_csv_bytes_rejects_duplicate_headers() -> None:
    file_bytes = b"date,revenue,revenue\n2024-01-01,100,120\n"

    _, warnings, error = read_uploaded_csv_bytes(file_bytes)

    assert not warnings
    assert error is not None and "duplicate header names" in error.lower()


def test_read_uploaded_csv_bytes_rejects_blank_headers() -> None:
    file_bytes = b"date,,transactions\n2024-01-01,100,2\n"

    _, warnings, error = read_uploaded_csv_bytes(file_bytes)

    assert not warnings
    assert error is not None and "blank header cells" in error.lower()


def test_read_uploaded_csv_bytes_rejects_wrong_delimiter() -> None:
    file_bytes = b"date;revenue;transactions\n2024-01-01;100;2\n"

    _, warnings, error = read_uploaded_csv_bytes(file_bytes)

    assert not warnings
    assert error is not None and "comma-separated" in error.lower()


def test_read_uploaded_csv_bytes_rejects_binary_like_content() -> None:
    file_bytes = b"date,revenue\x00\n2024-01-01,100\n"

    _, warnings, error = read_uploaded_csv_bytes(file_bytes)

    assert not warnings
    assert error is not None and "binary characters" in error.lower()


def test_read_uploaded_csv_bytes_rejects_malformed_rows() -> None:
    file_bytes = b'date,revenue\n2024-01-01,"100\n2024-01-02,120\n'

    _, warnings, error = read_uploaded_csv_bytes(file_bytes)

    assert not warnings
    assert error is not None and "malformed" in error.lower()


def test_read_uploaded_csv_bytes_warns_for_header_only_file() -> None:
    raw_df, warnings, error = read_uploaded_csv_bytes(b"date,revenue,transactions\n")

    assert error is None
    assert raw_df.empty
    assert any("headers but no data rows" in warning.lower() for warning in warnings)