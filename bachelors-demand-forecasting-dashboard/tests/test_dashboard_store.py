from __future__ import annotations

import time

import pytest

from src.dashboard_store import DashboardStore


RAW_CSV_BYTES = b"date,revenue,store_id\n2024-01-01,100,A\n2024-01-02,150,B\n"
BASE_UI_STATE = {
    "source_mode": "Upload CSV",
    "dashboard_name": "Q1 Dashboard",
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
    "forecast_methods": ["Moving Average", "Linear Regression"],
    "forecast_primary_method": "Linear Regression",
    "forecast_horizon": 7,
    "forecast_confidence": 0.95,
    "forecast_segment_dimension": "store_id",
    "forecast_window": 7,
    "forecast_use_trend": True,
    "forecast_use_seasonality": False,
    "anomaly_window": 14,
    "anomaly_threshold": 3.0,
    "filter_values": {"store_id": ["A", "B"]},
}


def test_dashboard_store_round_trip_and_overwrite(tmp_path) -> None:
    store = DashboardStore(tmp_path / "saved_dashboards.db")

    first = store.save_dashboard(
        name="Q1 Dashboard",
        source_type="uploaded_csv",
        raw_csv_bytes=RAW_CSV_BYTES,
        ui_state=BASE_UI_STATE,
        raw_file_name="orders.csv",
    )

    loaded = store.load_dashboard("Q1 Dashboard")
    assert loaded.name == "Q1 Dashboard"
    assert loaded.source_type == "uploaded_csv"
    assert loaded.raw_file_name == "orders.csv"
    assert loaded.raw_csv_bytes == RAW_CSV_BYTES
    assert loaded.ui_state == BASE_UI_STATE
    assert loaded.schema_version == 1
    assert loaded.created_at == first.created_at
    assert loaded.updated_at == first.updated_at

    time.sleep(0.01)
    updated_ui_state = {
        **BASE_UI_STATE,
        "dashboard_name": "Q1 Dashboard - Updated",
        "forecast_horizon": 14,
    }
    second = store.save_dashboard(
        name="Q1 Dashboard",
        source_type="saved_dashboard",
        raw_csv_bytes=RAW_CSV_BYTES,
        ui_state=updated_ui_state,
        raw_file_name="orders.csv",
    )

    assert second.name == "Q1 Dashboard"
    assert second.created_at == first.created_at
    assert second.updated_at >= first.updated_at
    assert second.source_type == "saved_dashboard"
    assert second.ui_state["dashboard_name"] == "Q1 Dashboard - Updated"
    assert second.ui_state["forecast_horizon"] == 14


def test_dashboard_store_delete_removes_dashboard(tmp_path) -> None:
    store = DashboardStore(tmp_path / "saved_dashboards.db")
    store.save_dashboard(
        name="Delete Me",
        source_type="uploaded_csv",
        raw_csv_bytes=RAW_CSV_BYTES,
        ui_state=BASE_UI_STATE,
        raw_file_name="orders.csv",
    )

    assert store.delete_dashboard("Delete Me") is True

    with pytest.raises(KeyError):
        store.load_dashboard("Delete Me")

    assert store.delete_dashboard("Delete Me") is False


@pytest.mark.parametrize("invalid_name", ["", "   ", "bad\nname"])
def test_dashboard_store_rejects_invalid_names(tmp_path, invalid_name: str) -> None:
    store = DashboardStore(tmp_path / "saved_dashboards.db")

    with pytest.raises(ValueError):
        store.save_dashboard(
            name=invalid_name,
            source_type="uploaded_csv",
            raw_csv_bytes=RAW_CSV_BYTES,
            ui_state=BASE_UI_STATE,
            raw_file_name="orders.csv",
        )

