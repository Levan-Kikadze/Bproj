import pandas as pd

from src.anomaly_detection import detect_rolling_zscore_anomalies


def test_anomaly_detection_output_columns():
    aggregated_df = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=10, freq="D"),
            "revenue": [100, 101, 99, 102, 98, 100, 101, 300, 99, 100],
        }
    )

    result = detect_rolling_zscore_anomalies(aggregated_df, window=3, threshold=2.5)

    assert {"rolling_mean", "rolling_std", "z_score", "is_anomaly"}.issubset(result.columns)
    assert result["is_anomaly"].dtype == bool

