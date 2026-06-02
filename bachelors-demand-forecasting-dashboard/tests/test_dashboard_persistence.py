from __future__ import annotations

import pandas as pd

import app
from src.dashboard_store import DashboardStore


class _NoOpSidebar:
    def success(self, *args, **kwargs):
        return None

    def warning(self, *args, **kwargs):
        return None

    def error(self, *args, **kwargs):
        return None

    def info(self, *args, **kwargs):
        return None


def test_saved_dashboard_record_restores_selected_source_and_controls(monkeypatch, tmp_path) -> None:
    fake_session_state: dict[str, object] = {}
    monkeypatch.setattr(app.st, "session_state", fake_session_state, raising=False)
    monkeypatch.setattr(app.st, "sidebar", _NoOpSidebar(), raising=False)

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


def test_pending_saved_dashboard_load_applies_before_widgets(monkeypatch, tmp_path) -> None:
    fake_session_state: dict[str, object] = {}
    monkeypatch.setattr(app.st, "session_state", fake_session_state, raising=False)
    monkeypatch.setattr(app.st, "sidebar", _NoOpSidebar(), raising=False)

    raw_csv_bytes = b"date,revenue,store_id\n2024-01-01,100,A\n2024-01-02,150,B\n"
    store = DashboardStore(tmp_path / "saved_dashboards.db")
    store.save_dashboard(
        name="Pending Dashboard",
        source_type="Upload CSV",
        raw_csv_bytes=raw_csv_bytes,
        ui_state={
            "source_mode": "Upload CSV",
            "dashboard_name": "Pending Dashboard",
            "source_name": "orders.csv",
            "source_type": "uploaded_csv",
            "date_col": "date",
            "revenue_col": "revenue",
            "transactions_col": "None",
            "holiday_col": "None",
            "promotion_col": "None",
            "filter_columns": ["store_id"],
            "frequency": "Daily",
            "overview_dimension": "store_id",
            "forecast_methods": ["Moving Average"],
            "forecast_primary_method": "Moving Average",
            "forecast_horizon": 7,
            "forecast_confidence": 0.95,
            "forecast_segment_dimension": "None",
            "forecast_window": 7,
            "forecast_use_trend": True,
            "forecast_use_seasonality": False,
            "anomaly_window": 14,
            "anomaly_threshold": 3.0,
            "filter_values": {"store_id": ["A"]},
        },
        raw_file_name="orders.csv",
    )
    monkeypatch.setattr(app, "get_dashboard_store", lambda: store)

    fake_session_state[app.PENDING_SAVED_DASHBOARD_LOAD_KEY] = "Pending Dashboard"

    result = app.process_pending_saved_dashboard_actions()

    assert result is not None
    assert result.source_name == "Pending Dashboard"
    assert fake_session_state[app.DATA_SOURCE_MODE_KEY] == "Saved dashboard"
    assert fake_session_state[app.SAVED_DASHBOARD_SELECTION_KEY] == "Pending Dashboard"
    assert fake_session_state[app.DATE_COL_KEY] == "date"
    assert fake_session_state[app.REVENUE_COL_KEY] == "revenue"
    assert fake_session_state[app.RAW_CSV_BYTES_KEY] == raw_csv_bytes
