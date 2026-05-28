# ForeSightSeer: User Manual

## Purpose

This dashboard helps SME users upload sales data, clean it, review data quality, monitor revenue KPIs, forecast future revenue, detect unusual sales trends, and export results.

The app also includes:

- a built-in `Guide` tab with a full explanation of charts, data, and interpretation,
- small `i` help popovers next to the main sections inside the app,
- help text on important sidebar controls and forecasting options.

## Business Questions This Dashboard Answers

1. Can I trust this dataset before I show numbers to anyone?
   Use the Data Quality tab. It shows what was removed, what was normalized, and whether the cleaned data still looks usable.
2. What is happening in the business right now?
   Use the Overview tab. It summarizes revenue level, growth, and segment contribution so you can describe current performance quickly.
3. What should I expect next week or next month?
   Use the Forecasting tab. Compare the models, inspect the future forecast table, and use the output to support inventory, staffing, or target-setting discussions.
4. Which periods need explanation before I act?
   Use the Anomaly Detection tab. It highlights unusual spikes or drops that may reflect promotions, outages, data issues, or real business events.

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

If you are new to the app, open the `Guide` tab before working with real data.

## Uploading Data

1. In `Dataset source`, choose either a bundled demo dataset or `Upload CSV`.
2. If you upload a file, use the file uploader to select your CSV.
3. Confirm that the raw preview looks correct.
4. Select the date column.
5. Select the revenue column.
6. Optionally select transactions, holiday, and promotion columns.
7. Optionally select filter columns such as product category, store, or product ID.
8. Choose the aggregation frequency: Daily, Weekly, or Monthly.

Use the small `i` popovers in the app whenever you are unsure how to read a section.

The app warns you when an uploaded CSV has no obvious date or revenue column, when the sampled date or revenue values do not parse cleanly, when the same column is selected for both date and revenue, or when the file has headers but no data rows.

## Using Filters

If filter columns are selected, the sidebar shows filter controls. Select the categories, stores, or products you want to analyze. If all values are selected, the dashboard analyzes the full cleaned dataset.

Remember that filters change all KPIs, charts, forecasts, anomalies, and exports.

## Overview Tab

Business use: this is the fastest way to answer, "How is the business performing right now?"

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

Use the `i` help popovers beside the chart sections for plain-language interpretation guidance.

## Data Quality Tab

Business use: this tab is the trust checkpoint before you present KPI or forecast results.

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

Business use: this tab answers the planning question, "What should demand or revenue look like next, and how uncertain is that estimate?"

The Forecasting tab lets you choose:

- one or more models to evaluate,
- which model should be shown in detailed view,
- future forecast horizon,
- confidence level,
- optional segment comparison,
- moving average window,
- trend and optional seasonality for Exponential Smoothing.

The tab reports:

- Model comparison table.
- MAE: average absolute forecast error.
- MAPE: average percentage forecast error, excluding zero actual revenue rows.
- Actual vs predicted revenue chart.
- Test forecast table.
- Future forecast table.
- Linear Regression coefficients, when that model is selected.
- Segment comparison output, when enabled.

If the dataset is too short or the model cannot be fitted, the app shows a warning instead of stopping.

New users should start with the model comparison table, then inspect the forecast chart, then read the future forecast table as the decision output, and finally check the test forecast table to understand past error behavior.

## Anomaly Detection Tab

Business use: this tab helps you decide which unusual periods need investigation before you change stock, staffing, or targets.

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

Use the `i` help beside the anomaly sections to understand what counts as unusual behavior and how to interpret the red markers.

## Export Tab

The Export tab provides downloads for:

- Cleaned aggregated dataset.
- Forecast results.
- Anomaly results.

These files can be opened in Excel, Google Sheets, or other reporting tools.

## Common Issues

- If the CSV does not load, check that it is a valid comma-separated file.
- If the app warns that no obvious date-like column was found, verify that the uploaded file includes a real date field before continuing.
- If the app warns that the selected date or revenue field does not parse in sampled values, change the mapping before trusting the analysis.
- If the file has headers but no data rows, add at least one valid sales row before uploading again.
- If the same field is selected as both date and revenue, choose two different columns; the app now blocks that invalid configuration.
- If dates are removed, check that the selected date column contains parseable dates.
- If revenue rows are removed, check for missing, text-based, or negative revenue values.
- If transaction values are corrected to zero, check for text entries, blanks, or negative values in the selected transactions column.
- If MAPE is unavailable, the test set likely has only zero actual revenue values.
- If Exponential Smoothing shows a warning, use Moving Average or provide more historical data.


