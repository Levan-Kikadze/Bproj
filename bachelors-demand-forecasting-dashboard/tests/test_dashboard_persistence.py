from __future__ import annotations

import pandas as pd

import app
from src.dashboard_store import DashboardStore


def test_saved_dashboard_record_restores_selected_source_and_controls(monkeypatch, tmp_path) -> None:
    fake_session_state: dict[str, object] = {}
    monkeypatch.setattr(app.st, "session_state", fake_session_state, raising=False)

    raw_csv_bytes = b"date,revenue,store_id\n2024-01-01,100,A\n2024-01-02,150,B\n"
    raw_df, warnings, error = app.read_uploaded_csv_bytes(raw_csv_bytes)

    assert error is None
    assert not warnings

    fake_session_state.update(
        {
            app.DATA_SOURCE_MODE_KEY: "Upload CSV",
            app.DASHBOARD_NAME_KEY: "Q1 Dashboard",
            app.SOURCE_NAME_KEY: "orders.csv",
            app.SOURCE_TYPE_KEY: "uploaded_csv",
            app.DATE_COL_KEY: "date",
            app.REVENUE_COL_KEY: "revenue",
            app.TRANSACTIONS_COL_KEY: "None",
            app.HOLIDAY_COL_KEY: "None",
            app.PROMOTION_COL_KEY: "None",
            app.FILTER_COLUMNS_KEY: ["store_id"],
            app._filter_selection_key("store_id"): ["A"],
            app.FREQUENCY_KEY: "Weekly",
            app.OVERVIEW_DIMENSION_KEY: "store_id",
            app.FORECAST_METHODS_KEY: ["Moving Average", "Linear Regression"],
            app.FORECAST_PRIMARY_METHOD_KEY: "Linear Regression",
            app.FORECAST_HORIZON_KEY: 14,
            app.FORECAST_CONFIDENCE_KEY: 0.9,
            app.FORECAST_SEGMENT_KEY: "store_id",
            app.FORECAST_WINDOW_KEY: 5,
            app.FORECAST_USE_TREND_KEY: True,
            app.FORECAST_USE_SEASONALITY_KEY: False,
            app.ANOMALY_WINDOW_KEY: 10,
            app.ANOMALY_THRESHOLD_KEY: 2.5,
            app.RAW_CSV_BYTES_KEY: raw_csv_bytes,
            app.RAW_DF_CACHE_KEY: raw_df,
            app.RAW_FILE_NAME_KEY: "orders.csv",
        }
    )

    snapshot = app.collect_dashboard_ui_state(["store_id"])
    assert snapshot["source_mode"] == "Upload CSV"
    assert snapshot["date_col"] == "date"
    assert snapshot["forecast_primary_method"] == "Linear Regression"

    store = DashboardStore(tmp_path / "saved_dashboards.db")
    record = store.save_dashboard(
        name="Q1 Dashboard",
        source_type=snapshot["source_mode"],
        raw_csv_bytes=raw_csv_bytes,
        ui_state=snapshot,
        raw_file_name="orders.csv",
    )

    fake_session_state.clear()
    app.apply_saved_dashboard_record(record, raw_df)

    assert fake_session_state[app.DATA_SOURCE_MODE_KEY] == "Saved dashboard"
    assert fake_session_state[app.SAVED_DASHBOARD_SELECTION_KEY] == "Q1 Dashboard"
    assert fake_session_state[app.DATE_COL_KEY] == "date"
    assert fake_session_state[app.REVENUE_COL_KEY] == "revenue"
    assert fake_session_state[app.FILTER_COLUMNS_KEY] == ["store_id"]
    assert fake_session_state[app._filter_selection_key("store_id")] == ["A"]
    assert fake_session_state[app.FORECAST_METHODS_KEY] == ["Moving Average", "Linear Regression"]
    assert fake_session_state[app.FORECAST_PRIMARY_METHOD_KEY] == "Linear Regression"
    assert fake_session_state[app.FORECAST_HORIZON_KEY] == 14
    assert fake_session_state[app.RAW_CSV_BYTES_KEY] == raw_csv_bytes
    assert isinstance(fake_session_state[app.RAW_DF_CACHE_KEY], pd.DataFrame)
    assert fake_session_state[app.RAW_DF_CACHE_KEY].equals(raw_df)

