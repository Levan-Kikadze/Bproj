# Technical Documentation

## Problem Statement

Small and medium-sized enterprises often have sales data in CSV files but lack a simple analytical system for validating data quality, monitoring revenue KPIs, forecasting future demand, and detecting unusual trends. This project provides a Streamlit dashboard that converts uploaded sales data into actionable business insights using explainable statistical methods.

## System Architecture

The application is organized as a small modular Python project:

- `app.py`: Streamlit user interface and workflow orchestration.
- `src/preprocessing.py`: CSV cleaning, validation, data quality reporting, and aggregation.
- `src/kpis.py`: KPI and revenue growth calculations.
- `src/forecasting.py`: Moving Average, Exponential Smoothing, train/test split, MAE, and MAPE.
- `src/anomaly_detection.py`: Rolling z-score anomaly detection.
- `src/visualization.py`: Plotly chart construction.
- `src/utils.py`: formatting, CSV export, and helper functions.
- `tests/`: pytest tests for the core business logic.

The Streamlit app receives user input, delegates reusable calculations to `src/`, and displays tables, metrics, charts, warnings, and downloads.

## Preprocessing Pipeline

The preprocessing pipeline performs the following steps:

1. Validate that the selected date and revenue columns exist.
2. Remove exact duplicate rows.
3. Rename selected fields to standardized names: `date`, `revenue`, and optionally `transactions`.
4. Convert the selected date column to pandas datetime.
5. Convert revenue and transaction columns to numeric values.
6. Remove rows with invalid dates.
7. Remove rows with missing or non-numeric revenue.
8. Remove negative revenue rows by default.
9. Sort rows chronologically.
10. Return a `DataQualityReport` with row counts, removed rows, missing values, and date range.

Negative revenue values are removed instead of forecasted because the dashboard is intended for simple revenue forecasting. In a real accounting dataset, negative rows could represent returns or refunds and may need a separate business rule.

## Aggregation

The dashboard supports:

- Daily aggregation.
- Weekly aggregation using week-start labels.
- Monthly aggregation using month-start labels.

Revenue is aggregated using sum. Transactions are also summed when a transaction column is selected.

## KPI Module

The KPI module calculates:

- Total revenue.
- Average revenue.
- Maximum revenue.
- Minimum revenue.
- Total transactions, if available.
- Average order value, if transactions are available.
- Latest period-over-period revenue growth.

Period-over-period growth compares the most recent aggregated period against the previous aggregated period. If the previous period has zero revenue, growth is reported as unavailable.

## Forecasting Module

The forecasting module uses a chronological train/test split:

- First 80% of observations for training.
- Last 20% for testing.
- No random shuffling, because this is time-series data.

### Moving Average

The Moving Average method uses a walk-forward evaluation. For each test period, it predicts revenue using the average of the most recent `window` values, then adds the actual test value to the history before predicting the next test period. Future forecasts are generated recursively.

### Exponential Smoothing

Exponential Smoothing is implemented with `statsmodels.tsa.holtwinters.ExponentialSmoothing`. The app supports:

- Optional additive trend.
- Optional additive seasonality when there are enough training observations.

The module catches model fitting errors and returns user-facing warnings instead of crashing the dashboard.

## Evaluation Metrics

### MAE

Mean Absolute Error is calculated with scikit-learn. It measures the average absolute difference between actual and predicted revenue.

### MAPE

Mean Absolute Percentage Error is calculated manually so zero actual values can be handled safely. Rows where actual revenue is zero are excluded from MAPE. If every actual value is zero, MAPE returns `NaN` and the app explains why.

## Missing Dates

Before forecasting, the module creates a regular time series for the selected aggregation frequency. Missing periods are filled with zero revenue and reported as warnings. This prevents model crashes but may not match every business interpretation of missing data.

## Anomaly Detection Method

The anomaly detection module uses rolling z-scores:

1. Shift revenue by one period so the current observation is compared only to previous observations.
2. Calculate rolling mean and rolling standard deviation.
3. Calculate z-score as `(current revenue - rolling mean) / rolling standard deviation`.
4. Flag rows where `abs(z-score)` is greater than the selected threshold.

The output includes:

- `rolling_mean`
- `rolling_std`
- `z_score`
- `is_anomaly`

This approach is interpretable and easy to explain, but it is sensitive to outliers, window size, and threshold selection.

## Testing Approach

Pytest tests cover the most important business logic:

- Invalid dates and missing revenue are removed.
- Duplicate rows are removed.
- Daily, weekly, and monthly aggregation preserves revenue and transaction totals.
- MAPE ignores zero actual values.
- MAPE returns `NaN` if all actual values are zero.
- Moving Average returns the expected output shape.
- Too-few-observation forecasting returns warnings instead of crashing.
- Anomaly detection returns required output columns.

The Streamlit interface itself is not unit-tested; the test suite focuses on reusable pure-Python logic in `src/`.

## Limitations

- Forecasts use only historical revenue and do not include causal features.
- The sample data is synthetic and should not be interpreted as real business performance.
- Missing dates are filled with zero revenue for forecasting.
- Exponential Smoothing may not be suitable for highly intermittent sales.
- The app is designed for interactive analysis, not automated production forecasting.
- There is no authentication, database, or real-time ingestion.

