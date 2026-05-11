# AI-Driven Demand and Revenue Forecasting Dashboard for SMEs

This project is a Streamlit dashboard for small and medium-sized enterprises that want an interpretable way to analyze sales data, forecast future demand/revenue, evaluate forecast accuracy, and detect unusual sales behavior.

The focus is a reliable bachelor-project MVP: simple, explainable methods; clean data handling; useful visualizations; and exportable results.

## Features

- CSV upload with raw data preview.
- Flexible column mapping for date, revenue, optional transactions, and optional categorical filters.
- Automatic preprocessing for duplicates, invalid dates, invalid revenue, negative revenue, missing values, and date sorting.
- Daily, weekly, and monthly aggregation.
- KPI cards for total revenue, average revenue, maximum revenue, minimum revenue, total transactions, average order value, and latest period-over-period growth.
- Interactive Plotly charts for revenue trends, growth rates, categorical revenue breakdowns, actual vs predicted revenue, and anomaly highlighting.
- Forecasting with Moving Average and Exponential Smoothing.
- Chronological 80/20 train/test split with MAE and MAPE evaluation.
- Rolling z-score anomaly detection with configurable window and threshold.
- CSV downloads for cleaned aggregated data, forecast results, and anomaly results.
- Pytest tests for preprocessing, forecasting, and anomaly detection.

## Technologies

- Python
- Streamlit
- pandas
- NumPy
- Plotly
- scikit-learn
- statsmodels
- pytest

## Setup

Use Python 3.10 or newer.

```bash
cd /Users/levankikadze/Desktop/Bproj/Bproj/bachelors-demand-forecasting-dashboard
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run the App

```bash
streamlit run app.py
```

If no CSV is uploaded, the app automatically loads `sample_data/sample_sales_data.csv` for demonstration.

## Run Tests

```bash
python -m pytest
```

## Expected CSV Format

The app accepts flexible column names because the user maps columns in the sidebar. A typical CSV should contain:

```csv
date,revenue,transactions,product_category,store_id,product_id
2024-01-01,1234.56,42,Electronics,STORE_001,ELEC_001
```

Required fields:

- Date column: any parseable date format.
- Revenue column: numeric values.

Optional fields:

- Transactions column: numeric order or transaction count.
- Categorical filters: product category, store ID, product ID, region, channel, or similar fields.

## Forecasting Methods

### Moving Average

The Moving Average model predicts each future value using the average of the most recent observed values. It is simple, transparent, and useful as a baseline for stable sales patterns.

### Exponential Smoothing

Exponential Smoothing uses statsmodels to weight recent observations more heavily than older observations. The dashboard supports an additive trend and optional additive seasonality when enough training observations are available.

### Evaluation

The data is split chronologically:

- First 80%: training set.
- Last 20%: test set.

The app reports:

- MAE: average absolute forecast error.
- MAPE: average percentage error, ignoring test rows where actual revenue is zero.

## Anomaly Detection

The dashboard uses rolling z-score anomaly detection:

1. Calculate historical rolling mean.
2. Calculate historical rolling standard deviation.
3. Compare the current value against the rolling baseline.
4. Flag rows where the absolute z-score exceeds the selected threshold.

This method is explainable and works well for demo-ready sales monitoring, but it is sensitive to the chosen rolling window and threshold.

## Limitations

- Forecasting is univariate and uses only historical revenue.
- External drivers such as promotions, holidays, weather, and marketing spend are not modeled.
- Missing dates are filled with zero revenue for forecasting, which may not be appropriate for every business.
- Exponential Smoothing can fail on very short or irregular datasets; the app catches these errors and shows a warning.
- MAPE is unavailable when all actual test values are zero.
- The app is not a real-time production system and does not include authentication.

## Future Improvements

- Add holiday and promotion calendars.
- Add product-level or store-level forecast comparisons.
- Add confidence intervals.
- Add more interpretable models such as linear regression with calendar features.
- Add automated model comparison across multiple forecast methods.
- Add deployment documentation for Streamlit Community Cloud or a cloud VM.

