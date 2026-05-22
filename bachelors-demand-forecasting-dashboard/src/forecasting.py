"""Forecasting methods and accuracy metrics."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import NormalDist

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error
import statsmodels.api as sm
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from src.features import build_calendar_feature_matrix, normalize_event_flag


MIN_OBSERVATIONS = 5


@dataclass(frozen=True)
class ForecastResult:
    """Container for forecast outputs and evaluation metrics."""

    method: str
    test_forecast: pd.DataFrame
    future_forecast: pd.DataFrame
    mae: float | None
    mape: float | None
    warnings: list[str]
    confidence_level: float | None = None
    features_used: list[str] | None = None
    model_details: pd.DataFrame | None = None


def calculate_mape(actual: pd.Series | np.ndarray, predicted: pd.Series | np.ndarray) -> float:
    """Calculate MAPE while ignoring zero actual values.

    Returns NaN if all actual values are zero or invalid.
    """
    actual_arr = np.asarray(actual, dtype=float)
    predicted_arr = np.asarray(predicted, dtype=float)
    valid_mask = np.isfinite(actual_arr) & np.isfinite(predicted_arr) & (actual_arr != 0)
    if not valid_mask.any():
        return float("nan")
    return float(np.mean(np.abs((actual_arr[valid_mask] - predicted_arr[valid_mask]) / actual_arr[valid_mask])) * 100)


def chronological_train_test_split(
    series: pd.Series,
    train_ratio: float = 0.8,
) -> tuple[pd.Series, pd.Series]:
    """Split a time series chronologically without shuffling."""
    if len(series) < 2:
        raise ValueError("At least two observations are required for train/test splitting.")

    split_index = int(np.floor(len(series) * train_ratio))
    split_index = min(max(split_index, 1), len(series) - 1)
    return series.iloc[:split_index], series.iloc[split_index:]


def run_moving_average_forecast(
    aggregated_df: pd.DataFrame,
    value_col: str = "revenue",
    date_col: str = "date",
    window: int = 7,
    horizon: int = 7,
    frequency: str = "Daily",
) -> ForecastResult:
    """Forecast revenue using a walk-forward moving average."""
    method = f"Moving Average ({window})"
    warnings: list[str] = []
    series, prep_warnings = prepare_time_series(aggregated_df, date_col, value_col, frequency)
    warnings.extend(prep_warnings)

    if len(series) < MIN_OBSERVATIONS:
        warnings.append("Too few observations for forecasting. At least five periods are required.")
        return _empty_result(method, warnings)

    train, test = chronological_train_test_split(series)
    window = max(1, int(window))
    history = train.astype(float).tolist()
    predictions: list[float] = []

    for actual_value in test.astype(float):
        prediction = float(np.mean(history[-window:]))
        predictions.append(prediction)
        history.append(float(actual_value))

    test_forecast = _build_test_forecast(test.index, test.to_numpy(), predictions, method)
    future_values = _recursive_moving_average(series.astype(float).tolist(), window, horizon)
    future_forecast = _build_future_forecast(
        make_future_index(series.index[-1], horizon, frequency),
        future_values,
        method,
    )

    return ForecastResult(
        method=method,
        test_forecast=test_forecast,
        future_forecast=future_forecast,
        mae=float(mean_absolute_error(test, predictions)),
        mape=calculate_mape(test, predictions),
        warnings=warnings,
    )


def run_exponential_smoothing_forecast(
    aggregated_df: pd.DataFrame,
    value_col: str = "revenue",
    date_col: str = "date",
    horizon: int = 7,
    frequency: str = "Daily",
    use_trend: bool = True,
    seasonal_periods: int | None = None,
    confidence_level: float | None = None,
) -> ForecastResult:
    """Forecast revenue using statsmodels Exponential Smoothing."""
    method = "Exponential Smoothing"
    warnings: list[str] = []
    series, prep_warnings = prepare_time_series(aggregated_df, date_col, value_col, frequency)
    warnings.extend(prep_warnings)

    if len(series) < MIN_OBSERVATIONS:
        warnings.append("Too few observations for Exponential Smoothing. At least five periods are required.")
        return _empty_result(method, warnings)

    train, test = chronological_train_test_split(series)
    trend = "add" if use_trend and len(train) >= 4 else None
    seasonal = None
    if seasonal_periods:
        if len(train) >= seasonal_periods * 2:
            seasonal = "add"
        else:
            warnings.append(
                "Not enough training observations for seasonal Exponential Smoothing; seasonality was disabled."
            )

    try:
        fitted = _fit_exponential_smoothing(train, trend, seasonal, seasonal_periods)
        test_predictions = np.asarray(fitted.forecast(len(test)), dtype=float)
        test_interval = _build_prediction_interval(
            test_predictions,
            residual_scale=_residual_scale(train, fitted.fittedvalues),
            confidence_level=confidence_level,
        )
    except Exception as exc:
        warnings.append(f"Exponential Smoothing could not be fitted: {exc}")
        return _empty_result(method, warnings)

    try:
        full_fitted = _fit_exponential_smoothing(series, trend, seasonal, seasonal_periods)
        future_predictions = np.asarray(full_fitted.forecast(horizon), dtype=float)
        future_interval = _build_prediction_interval(
            future_predictions,
            residual_scale=_residual_scale(series, full_fitted.fittedvalues),
            confidence_level=confidence_level,
        )
    except Exception as exc:
        warnings.append(f"Future Exponential Smoothing forecast failed: {exc}")
        future_predictions = np.asarray([], dtype=float)
        future_interval = (None, None)

    test_forecast = _build_test_forecast(
        test.index,
        test.to_numpy(),
        test_predictions,
        method,
        lower_bound=test_interval[0],
        upper_bound=test_interval[1],
    )
    future_forecast = _build_future_forecast(
        make_future_index(series.index[-1], len(future_predictions), frequency),
        future_predictions,
        method,
        lower_bound=future_interval[0],
        upper_bound=future_interval[1],
    )

    return ForecastResult(
        method=method,
        test_forecast=test_forecast,
        future_forecast=future_forecast,
        mae=float(mean_absolute_error(test, test_predictions)),
        mape=calculate_mape(test, test_predictions),
        warnings=warnings,
        confidence_level=confidence_level,
    )


def run_linear_regression_forecast(
    aggregated_df: pd.DataFrame,
    value_col: str = "revenue",
    date_col: str = "date",
    horizon: int = 7,
    frequency: str = "Daily",
    holiday_col: str | None = None,
    promotion_col: str | None = None,
    confidence_level: float = 0.95,
) -> ForecastResult:
    """Forecast revenue using an interpretable linear regression with calendar features."""
    method = "Linear Regression"
    warnings: list[str] = []
    event_columns = [col for col in [holiday_col, promotion_col] if col]
    frame, prep_warnings = prepare_forecast_frame(
        aggregated_df,
        date_col=date_col,
        value_col=value_col,
        frequency=frequency,
        event_columns=event_columns,
    )
    warnings.extend(prep_warnings)

    if len(frame) < MIN_OBSERVATIONS:
        warnings.append("Too few observations for Linear Regression. At least five periods are required.")
        return _empty_result(method, warnings)

    split_index = int(np.floor(len(frame) * 0.8))
    split_index = min(max(split_index, 1), len(frame) - 1)
    train_frame = frame.iloc[:split_index].reset_index(drop=True)
    test_frame = frame.iloc[split_index:].reset_index(drop=True)

    train_X = build_calendar_feature_matrix(
        train_frame[date_col],
        start_index=0,
        holiday_values=train_frame[holiday_col] if holiday_col and holiday_col in train_frame.columns else None,
        promotion_values=train_frame[promotion_col] if promotion_col and promotion_col in train_frame.columns else None,
    )
    test_X = build_calendar_feature_matrix(
        test_frame[date_col],
        start_index=len(train_frame),
        holiday_values=test_frame[holiday_col] if holiday_col and holiday_col in test_frame.columns else None,
        promotion_values=test_frame[promotion_col] if promotion_col and promotion_col in test_frame.columns else None,
        reference_columns=train_X.columns.tolist(),
    )

    train_design = _add_constant_column(train_X)
    test_design = _add_constant_column(test_X, reference_columns=train_design.columns.tolist())

    try:
        fitted = sm.OLS(train_frame[value_col].astype(float), train_design.astype(float)).fit()
    except Exception as exc:
        warnings.append(f"Linear Regression could not be fitted: {exc}")
        return _empty_result(method, warnings)

    alpha = max(0.001, min(0.999, 1 - confidence_level))
    test_prediction = fitted.get_prediction(test_design.astype(float)).summary_frame(alpha=alpha)

    future_dates = make_future_index(frame[date_col].iloc[-1], horizon, frequency)
    future_X = build_calendar_feature_matrix(
        pd.Series(future_dates),
        start_index=len(frame),
        reference_columns=train_X.columns.tolist(),
    )
    future_design = _add_constant_column(future_X, reference_columns=train_design.columns.tolist())
    future_prediction = fitted.get_prediction(future_design.astype(float)).summary_frame(alpha=alpha)

    test_forecast = _build_test_forecast(
        test_frame[date_col],
        test_frame[value_col].to_numpy(),
        test_prediction["mean"].to_numpy(),
        method,
        lower_bound=test_prediction["obs_ci_lower"].to_numpy(),
        upper_bound=test_prediction["obs_ci_upper"].to_numpy(),
    )
    future_forecast = _build_future_forecast(
        future_dates,
        future_prediction["mean"].to_numpy(),
        method,
        lower_bound=future_prediction["obs_ci_lower"].to_numpy(),
        upper_bound=future_prediction["obs_ci_upper"].to_numpy(),
    )

    model_details = pd.DataFrame(
        {
            "feature": fitted.params.index,
            "coefficient": fitted.params.to_numpy(),
        }
    )

    if promotion_col is None:
        warnings.append("No promotion column selected; promotion features default to zero.")

    return ForecastResult(
        method=method,
        test_forecast=test_forecast,
        future_forecast=future_forecast,
        mae=float(mean_absolute_error(test_frame[value_col], test_prediction["mean"])),
        mape=calculate_mape(test_frame[value_col], test_prediction["mean"]),
        warnings=warnings,
        confidence_level=confidence_level,
        features_used=train_X.columns.tolist(),
        model_details=model_details,
    )


def prepare_time_series(
    aggregated_df: pd.DataFrame,
    date_col: str = "date",
    value_col: str = "revenue",
    frequency: str = "Daily",
) -> tuple[pd.Series, list[str]]:
    """Return a regular time series, filling missing periods with zero revenue."""
    warnings: list[str] = []
    if aggregated_df.empty:
        return pd.Series(dtype=float), ["Dataset is empty after filtering or aggregation."]
    if date_col not in aggregated_df.columns or value_col not in aggregated_df.columns:
        return pd.Series(dtype=float), [f"Dataset must contain `{date_col}` and `{value_col}` columns."]

    working = aggregated_df[[date_col, value_col]].copy()
    working[date_col] = pd.to_datetime(working[date_col], errors="coerce")
    working[value_col] = pd.to_numeric(working[value_col], errors="coerce")
    working = working.dropna(subset=[date_col, value_col])
    if working.empty:
        return pd.Series(dtype=float), ["No valid dated revenue observations are available."]

    working = working.groupby(date_col, as_index=True)[value_col].sum().sort_index()
    pandas_frequency = frequency_to_pandas(frequency)
    full_index = pd.date_range(working.index.min(), working.index.max(), freq=pandas_frequency)
    missing_period_count = len(full_index.difference(working.index))
    if missing_period_count > 0:
        warnings.append(f"{missing_period_count} missing period(s) were filled with zero revenue for forecasting.")

    regular_series = working.reindex(full_index, fill_value=0).astype(float)
    regular_series.index.name = date_col
    return regular_series, warnings


def prepare_forecast_frame(
    aggregated_df: pd.DataFrame,
    date_col: str = "date",
    value_col: str = "revenue",
    frequency: str = "Daily",
    event_columns: list[str] | None = None,
) -> tuple[pd.DataFrame, list[str]]:
    """Return a regular forecast frame with optional event columns preserved."""
    warnings: list[str] = []
    if aggregated_df.empty:
        return pd.DataFrame(columns=[date_col, value_col]), ["Dataset is empty after filtering or aggregation."]
    if date_col not in aggregated_df.columns or value_col not in aggregated_df.columns:
        return pd.DataFrame(columns=[date_col, value_col]), [f"Dataset must contain `{date_col}` and `{value_col}` columns."]

    event_columns = [col for col in (event_columns or []) if col in aggregated_df.columns]
    selected_columns = [date_col, value_col, *event_columns]
    working = aggregated_df[selected_columns].copy()
    working[date_col] = pd.to_datetime(working[date_col], errors="coerce")
    working[value_col] = pd.to_numeric(working[value_col], errors="coerce")
    for column in event_columns:
        working[column] = normalize_event_flag(working[column])

    working = working.dropna(subset=[date_col, value_col])
    if working.empty:
        return pd.DataFrame(columns=[date_col, value_col, *event_columns]), ["No valid dated revenue observations are available."]

    aggregation_map: dict[str, str] = {value_col: "sum"}
    for column in event_columns:
        aggregation_map[column] = "max"

    grouped = working.groupby(date_col, as_index=False).agg(aggregation_map).sort_values(date_col)
    pandas_frequency = frequency_to_pandas(frequency)
    full_index = pd.date_range(grouped[date_col].min(), grouped[date_col].max(), freq=pandas_frequency)
    missing_period_count = len(full_index.difference(pd.DatetimeIndex(grouped[date_col])))
    if missing_period_count > 0:
        warnings.append(f"{missing_period_count} missing period(s) were filled with zero revenue for forecasting.")

    regular_frame = grouped.set_index(date_col).reindex(full_index)
    regular_frame[value_col] = regular_frame[value_col].fillna(0).astype(float)
    for column in event_columns:
        regular_frame[column] = regular_frame[column].fillna(0).astype(float)

    regular_frame = regular_frame.reset_index().rename(columns={"index": date_col})
    return regular_frame, warnings


def frequency_to_pandas(frequency: str) -> str:
    """Map dashboard frequency labels to pandas frequencies."""
    frequency_normalized = frequency.lower()
    if frequency_normalized == "daily":
        return "D"
    if frequency_normalized == "weekly":
        return "W-MON"
    if frequency_normalized == "monthly":
        return "MS"
    raise ValueError("frequency must be one of: Daily, Weekly, Monthly")


def make_future_index(last_date: pd.Timestamp, horizon: int, frequency: str) -> pd.DatetimeIndex:
    """Create future period labels after the last observed date."""
    if horizon <= 0:
        return pd.DatetimeIndex([])

    pandas_frequency = frequency_to_pandas(frequency)
    start = pd.Timestamp(last_date) + pd.tseries.frequencies.to_offset(pandas_frequency)
    return pd.date_range(start=start, periods=horizon, freq=pandas_frequency)


def _fit_exponential_smoothing(
    series: pd.Series,
    trend: str | None,
    seasonal: str | None,
    seasonal_periods: int | None,
):
    return ExponentialSmoothing(
        series,
        trend=trend,
        seasonal=seasonal,
        seasonal_periods=seasonal_periods if seasonal else None,
        initialization_method="estimated",
    ).fit(optimized=True)


def _recursive_moving_average(history: list[float], window: int, horizon: int) -> list[float]:
    values = list(history)
    predictions: list[float] = []
    for _ in range(max(0, int(horizon))):
        prediction = float(np.mean(values[-window:]))
        predictions.append(prediction)
        values.append(prediction)
    return predictions


def _build_test_forecast(
    dates: pd.Index,
    actual: np.ndarray,
    predicted: list[float] | np.ndarray,
    method: str,
    lower_bound: list[float] | np.ndarray | None = None,
    upper_bound: list[float] | np.ndarray | None = None,
) -> pd.DataFrame:
    data: dict[str, object] = {
        "date": pd.to_datetime(dates),
        "actual": np.asarray(actual, dtype=float),
        "predicted": np.asarray(predicted, dtype=float),
        "method": method,
    }
    if lower_bound is not None and upper_bound is not None:
        data["lower_bound"] = np.asarray(lower_bound, dtype=float)
        data["upper_bound"] = np.asarray(upper_bound, dtype=float)
    return pd.DataFrame(data)


def _build_future_forecast(
    dates: pd.Index,
    predicted: list[float] | np.ndarray,
    method: str,
    lower_bound: list[float] | np.ndarray | None = None,
    upper_bound: list[float] | np.ndarray | None = None,
) -> pd.DataFrame:
    data: dict[str, object] = {
        "date": pd.to_datetime(dates),
        "predicted": np.asarray(predicted, dtype=float),
        "method": method,
    }
    if lower_bound is not None and upper_bound is not None:
        data["lower_bound"] = np.asarray(lower_bound, dtype=float)
        data["upper_bound"] = np.asarray(upper_bound, dtype=float)
    return pd.DataFrame(data)


def _empty_result(method: str, warnings: list[str]) -> ForecastResult:
    return ForecastResult(
        method=method,
        test_forecast=pd.DataFrame(columns=["date", "actual", "predicted", "method"]),
        future_forecast=pd.DataFrame(columns=["date", "predicted", "method"]),
        mae=None,
        mape=None,
        warnings=warnings,
    )


def _add_constant_column(frame: pd.DataFrame, reference_columns: list[str] | None = None) -> pd.DataFrame:
    design = sm.add_constant(frame, has_constant="add")
    if reference_columns is not None:
        design = design.reindex(columns=reference_columns, fill_value=0.0)
        if "const" in design.columns:
            design["const"] = 1.0
    return design.astype(float)


def _build_prediction_interval(
    predictions: np.ndarray,
    residual_scale: float,
    confidence_level: float | None,
) -> tuple[np.ndarray | None, np.ndarray | None]:
    if confidence_level is None or len(predictions) == 0 or residual_scale <= 0:
        return None, None

    horizon_scale = np.sqrt(np.arange(1, len(predictions) + 1, dtype=float))
    margin = _z_value_for_confidence_level(confidence_level) * residual_scale * horizon_scale
    return predictions - margin, predictions + margin


def _residual_scale(actual: pd.Series | np.ndarray, fitted_values: pd.Series | np.ndarray) -> float:
    residuals = np.asarray(actual, dtype=float) - np.asarray(fitted_values, dtype=float)
    if residuals.size <= 1:
        return 0.0
    return float(np.nanstd(residuals, ddof=1))


def _z_value_for_confidence_level(confidence_level: float) -> float:
    bounded_level = min(max(float(confidence_level), 0.5), 0.999)
    return float(NormalDist().inv_cdf(0.5 + bounded_level / 2))

