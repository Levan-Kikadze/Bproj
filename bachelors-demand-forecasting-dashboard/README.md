# ForeSightSeer: AI-Driven Demand and Revenue Forecasting Dashboard for SMEs

## Project Summary

This project is a Streamlit dashboard for small and medium-sized enterprises that need an interpretable, practical way to validate sales data, monitor business KPIs, forecast future demand and revenue, and detect unusual behavior.

The implementation focuses on explainability and a clear evaluation story rather than on complex black-box modeling. The dashboard includes:

- modular and readable Python code,
- explainable statistical methods instead of opaque models,
- transparent data cleaning and reporting,
- useful visual outputs for a live demo,
- automated tests for the main business logic.

## Business Value for SMEs

ForeSightSeer is designed for small teams that still rely on spreadsheets, manual checks, and judgment calls when planning stock, staffing, or sales targets. In a typical SME workflow, a manager can upload a CSV, confirm that the data is trustworthy, review the latest KPI trend, compare several short-term forecasts, and export the result for a meeting or planning discussion in one session.

Without a tool like this, the same workflow is often fragmented across spreadsheets and manual formulas:

- data-quality issues can stay hidden until late in the analysis,
- KPI definitions can differ from person to person,
- short-term planning depends too heavily on intuition,
- unusual sales spikes or drops are harder to investigate quickly.

With ForeSightSeer, each feature supports a concrete decision:

- Data Quality helps the user decide whether the uploaded dataset is safe to trust.
- Overview helps the user decide whether performance is improving or weakening.
- Forecasting helps the user estimate near-term demand and defend inventory or target-setting decisions.
- Anomaly Detection helps the user decide which periods need investigation before acting.

The value is not only in charts. It is in making SME analysis faster, more consistent, and easier to explain to non-technical stakeholders.

## Core Features

- CSV upload with raw data preview, upload-time column warnings, and clearer empty-data feedback.
- Flexible column mapping for date, revenue, optional transactions, and optional business dimensions, with validation warnings when selected date or revenue fields look suspicious.
- Optional holiday and promotion column mapping for forecast features.
- Preprocessing that removes duplicates, invalid dates, invalid revenue values, and negative revenue rows.
- Explicit reporting of unique removed rows and transaction values that were normalized to zero.
- Daily, weekly, and monthly aggregation.
- KPI cards for total revenue, average revenue, maximum revenue, minimum revenue, transactions, average order value, and latest growth.
- Interactive Plotly charts for revenue trend, growth, breakdown by dimension, forecast output, and anomalies.
- Forecasting with Moving Average, Exponential Smoothing, and Linear Regression with calendar features.
- Multi-model forecast comparison in the same UI.
- Confidence intervals for Exponential Smoothing and Linear Regression.
- Segment-level forecast comparison by product, store, or another categorical dimension.
- Chronological 80/20 train/test evaluation with MAE and MAPE.
- Rolling z-score anomaly detection with configurable sensitivity.
- CSV exports for cleaned aggregated data, forecast outputs, and anomaly results.
- Pytest regression coverage for preprocessing, forecasting, and anomaly detection.

## Technology Stack

- Python
- Streamlit
- pandas
- NumPy
- Plotly
- scikit-learn
- statsmodels
- pytest

## Validated Environment

The project is documented as supporting Python 3.10 or newer.

For the exact dependency versions used in the latest validated local snapshot, see `docs/reproducibility_snapshot.md`.
If you want the same package set that was used for that validation pass, use `requirements-validated.txt`.

## Local Installation

Use Python 3.10 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running the Application

From the project folder:

```bash
streamlit run app.py
```

If no CSV is uploaded, the app automatically loads `sample_data/sample_sales_data.csv`, which makes the dashboard demo-ready without extra setup.

The sidebar also includes additional bundled demo datasets for targeted scenarios such as data quality issues, holiday and promotion forecasting, and anomaly detection with missing periods. See `sample_data/README.md` for a quick guide.

## Running the Tests

From the project folder with the virtual environment activated:

```bash
pytest
```

The latest local validation snapshot also passed with:

```bash
.venv/bin/pytest -q
```

## Expected Input Data

The dashboard supports flexible column names because the user maps columns in the sidebar. A typical CSV can look like this:

```csv
date,revenue,transactions,product_category,store_id,product_id
2024-01-01,1234.56,42,Electronics,STORE_001,ELEC_001
```

Required fields:

- Date column with parseable date values.
- Revenue column with numeric values.

Optional fields:

- Transactions column with numeric order or transaction counts.
- Holiday indicator column with binary or yes/no values.
- Promotion indicator column with binary or yes/no values.
- Categorical dimensions such as product category, store, product, region, or sales channel.

## Methodology Overview

### Preprocessing

The preprocessing pipeline standardizes selected columns, removes duplicate rows, converts date and revenue values, filters invalid observations, sorts the data chronologically, and reports the cleaning decisions to the user. Invalid or negative transaction values are normalized to zero and surfaced in the Data Quality tab so KPI outputs remain transparent.

### Forecasting

Three interpretable forecasting methods are included:

- Moving Average as a simple baseline.
- Exponential Smoothing for trend-aware forecasting, with optional seasonality when enough data exists.
- Linear Regression with time trend, calendar effects, built-in holiday flags, and optional uploaded holiday/promotion indicators.

The evaluation uses a chronological train/test split:

- first 80% for training,
- last 20% for testing.

Reported metrics:

- MAE: mean absolute error.
- MAPE: mean absolute percentage error, excluding test rows where actual revenue is zero.

The Forecasting tab can run several models at once, compare their MAE and MAPE, show prediction intervals where available, and compare future forecasts across major product or store segments.

### Anomaly Detection

The dashboard applies rolling z-score anomaly detection:

1. Build a historical rolling baseline from previous observations.
2. Compare the current revenue value to that baseline.
3. Flag values whose absolute z-score exceeds the selected threshold.

This approach is easy to explain during a presentation and appropriate for an SME-focused decision-support prototype.

## Recommended Demo Narrative

1. Start with the sample dataset so the app opens with valid data immediately.
2. Show the raw preview and column mapping, and explain that bad date or revenue mapping would now trigger warnings before the analysis continues.
3. Open the Data Quality tab and explain why an SME should validate trust in the data before trusting the KPI or forecast output.
4. Present the KPI cards and revenue trend as the current-state business snapshot.
5. Open the Forecasting tab and answer the key planning question: what should demand or revenue look like next week or next month?
6. Compare Moving Average, Exponential Smoothing, and Linear Regression on the same holdout split, then show the future forecast table and confidence intervals.
7. Translate the forecast into a business action such as inventory planning, staffing, or target setting.
8. Compare a store or product segment forecast using the segment comparison section if you need a richer decision story.
9. Show the anomaly view and explain threshold sensitivity.
10. Export the outputs.

## Limitations

- Moving Average and Exponential Smoothing remain univariate and rely only on historical revenue.
- Linear Regression includes calendar effects plus optional holiday and promotion indicators, but richer external drivers such as weather, price changes, and marketing spend are still not modeled.
- Missing dates are filled with zero revenue for forecasting to preserve a regular time series.
- Exponential Smoothing can be unstable on short or irregular histories, so the app returns warnings instead of crashing.
- Linear Regression can underperform on datasets whose variation is not well explained by calendar effects or uploaded event flags.
- MAPE is unavailable when every valid test-period actual value is zero.
- The project is designed for interactive analysis, not real-time production deployment.

## Future Improvements

- Add custom holiday calendars for different countries or business-specific events.
- Add richer causal features such as price, weather, and marketing spend.
- Add automated model selection and segment-specific export bundles.
- Add additional interpretable models for intermittent demand, such as Croston-style baselines.
- Add deployment instructions for Streamlit Community Cloud or a cloud VM.
- Extend evaluation with cross-validation style backtesting across several forecast origins.

## Additional Project Documents

- `docs/bachelor_report.md`
- `docs/final_eval_rubric_mapping.md`
- `docs/final_presentation_outline.md`
- `docs/reproducibility_snapshot.md`
- `docs/technical_documentation.md`
- `docs/user_manual.md`
- `docs/viva_cheat_sheet.md`
- `docs/submission_checklist.md`

