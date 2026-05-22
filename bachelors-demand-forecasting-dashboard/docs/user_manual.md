# User Manual

## Purpose

This dashboard helps SME users upload sales data, clean it, review data quality, monitor revenue KPIs, forecast future revenue, detect unusual sales trends, and export results.

## Starting the App

Open a terminal in the project folder and run:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Then start the dashboard:

```bash
streamlit run app.py
```

The app opens in a browser. If you do not upload a CSV file, the dashboard uses the bundled sample dataset.

## Uploading Data

1. Use the sidebar file uploader to select a CSV file.
2. Confirm that the raw preview looks correct.
3. Select the date column.
4. Select the revenue column.
5. Optionally select a transactions column.
6. Optionally select filter columns such as product category, store, or product ID.
7. Choose the aggregation frequency: Daily, Weekly, or Monthly.

## Using Filters

If filter columns are selected, the sidebar shows filter controls. Select the categories, stores, or products you want to analyze. If all values are selected, the dashboard analyzes the full cleaned dataset.

## Overview Tab

The Overview tab shows:

- Total revenue.
- Average revenue.
- Maximum revenue.
- Minimum revenue.
- Total transactions, if available.
- Average order value, if transactions are available.
- Latest revenue growth.

It also shows:

- Revenue trend over time.
- Revenue growth rate.
- Revenue breakdown by selected category, store, or product.

## Data Quality Tab

The Data Quality tab explains how the uploaded data was cleaned. It shows:

- Original row count.
- Final cleaned row count.
- Duplicate rows removed.
- Unique rows removed because of invalid dates, invalid revenue, or negative revenue.
- Invalid date rows removed.
- Missing or invalid revenue rows removed.
- Negative revenue rows removed.
- Invalid transaction values that were set to zero.
- Negative transaction values that were set to zero.
- Missing values per original column.
- Cleaned date range.
- Cleaned and filtered data previews.

Use this tab to confirm that the dataset is suitable before interpreting KPIs and forecasts. The total removed-row metric counts unique removed rows, while the issue-specific counters help explain why those rows were flagged.

## Forecasting Tab

The Forecasting tab lets you choose:

- Moving Average.
- Exponential Smoothing.
- Future forecast horizon: 7, 14, or 30 periods.

For Moving Average, choose the rolling window size.

For Exponential Smoothing, choose whether to use trend and optional seasonality.

The tab reports:

- MAE: average absolute forecast error.
- MAPE: average percentage forecast error, excluding zero actual revenue rows.
- Actual vs predicted revenue chart.
- Test forecast table.
- Future forecast table.

If the dataset is too short or the model cannot be fitted, the app shows a warning instead of stopping.

## Anomaly Detection Tab

The Anomaly Detection tab uses rolling z-scores to find unusual revenue values.

Controls:

- Rolling window: how many previous periods define normal behavior.
- Threshold: how extreme a z-score must be before it is flagged.

Outputs:

- Number of anomalies.
- Chart with anomalies highlighted in red.
- Table of anomalous rows.
- Full anomaly results table.

Higher thresholds detect fewer anomalies. Lower thresholds detect more anomalies.

## Export Tab

The Export tab provides downloads for:

- Cleaned aggregated dataset.
- Forecast results.
- Anomaly results.

These files can be opened in Excel, Google Sheets, or other reporting tools.

## Recommended Demo Flow

1. Start with the sample dataset.
2. Keep default column mappings.
3. Review the Data Quality tab and explain removed rows plus transaction corrections.
4. Review the Overview tab and describe the KPI cards.
5. Run Moving Average with a 7-period window.
6. Compare it with Exponential Smoothing and discuss MAE and MAPE.
7. Open Anomaly Detection and adjust the threshold to show sensitivity.
8. Export the results and explain how they could support a manager's decision-making.

## Common Issues

- If the CSV does not load, check that it is a valid comma-separated file.
- If dates are removed, check that the selected date column contains parseable dates.
- If revenue rows are removed, check for missing, text-based, or negative revenue values.
- If transaction values are corrected to zero, check for text entries, blanks, or negative values in the selected transactions column.
- If MAPE is unavailable, the test set likely has only zero actual revenue values.
- If Exponential Smoothing shows a warning, use Moving Average or provide more historical data.

## Running Tests

To verify the project before submission, activate the virtual environment and run:

```bash
pytest
```

