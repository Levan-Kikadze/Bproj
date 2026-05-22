import pandas as pd

from src.features import add_calendar_features, add_holiday_features, build_calendar_feature_matrix


def test_add_calendar_features_derives_expected_columns():
    df = pd.DataFrame({"date": pd.to_datetime(["2024-01-01", "2024-01-06"])})

    featured = add_calendar_features(df)

    assert featured["day_of_week"].tolist() == [0, 5]
    assert featured["is_weekend"].tolist() == [0, 1]
    assert featured["time_index"].tolist() == [0, 1]


def test_add_holiday_features_uses_provided_column_when_available():
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01", "2024-01-02"]),
            "holiday_flag": [1, 0],
        }
    )

    featured = add_holiday_features(df, holiday_col="holiday_flag")

    assert featured["is_holiday"].tolist() == [1.0, 0.0]


def test_build_calendar_feature_matrix_reuses_reference_columns_for_future_rows():
    train_dates = pd.Series(pd.date_range("2024-01-01", periods=5, freq="D"))
    train_matrix = build_calendar_feature_matrix(train_dates)

    future_dates = pd.Series(pd.date_range("2024-01-06", periods=2, freq="D"))
    future_matrix = build_calendar_feature_matrix(
        future_dates,
        start_index=len(train_dates),
        reference_columns=train_matrix.columns.tolist(),
    )

    assert future_matrix.columns.tolist() == train_matrix.columns.tolist()
    assert future_matrix["time_index"].tolist() == [5.0, 6.0]