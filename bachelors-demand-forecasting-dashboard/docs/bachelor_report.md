## Bachelor Report:

# ForeSightSeer: AI Driven Demand and Revenue Forecasting Dashboard for SMEs

## Abstract

Small and medium sized enterprises often keep sales data in spreadsheets or CSV files. Many still need a simple way to check data quality, track sales performance, forecast demand, and find unusual sales behavior.

This project solves that problem with an interactive Streamlit dashboard. You upload sales data, map the key columns, review the cleaned dataset, and turn raw rows into useful business outputs.

The system uses clear methods that you can explain. It supports data cleaning, aggregation, KPI reporting, forecasting with Moving Average, Exponential Smoothing, and Linear Regression, rolling z score anomaly detection, and CSV export. The code uses reusable Python modules. Automated regression tests check the main business logic.

With the bundled sample dataset, the system processed 6,840 rows and did not need any data loss corrections. It produced total revenue of $9,444,661.18. In the default daily evaluation setup, the Moving Average baseline performed best. It reached an MAE of 1,808.04 and a MAPE of 7.88%. These results show that a lightweight and explainable dashboard can support SME decisions while staying realistic for a bachelor level software and data project.

## Introduction

Sales planning creates regular problems for SMEs. Many businesses record transactions every day, but they still need a simple analytical tool that helps them understand revenue patterns, find data quality issues, forecast short term performance, and detect unusual sales events.

Commercial analytics platforms can cost too much or add too much complexity for smaller organizations. Spreadsheet only workflows also make repeatable analysis harder. They often depend on manual checks, copied formulas, and personal judgment.

This project offers a practical alternative. ForeSightSeer is a lightweight dashboard that accepts CSV sales data and returns clear business outputs. The goal is to build a transparent decision support system that you can explain, test, and demonstrate within the scope of a bachelor project.

## Problem Statement

SMEs often have historical sales data, but they need a simple and reliable interface that helps them complete five tasks.

1. Check whether uploaded data is clean and usable.
2. Monitor core revenue KPIs.
3. Forecast short term future demand and revenue.
4. Detect unusual sales behavior.
5. Export analysis results for further use.

Without these features, managers rely on manual inspection, inconsistent spreadsheet formulas, or intuition. That creates poor planning risk and weak operational decisions.

## Project Objectives

This project has these objectives.

1. Build an interactive dashboard that accepts CSV sales data.
2. Provide clear preprocessing and data quality reporting.
3. Aggregate sales data at daily, weekly, and monthly levels.
4. Calculate business KPIs that help SMEs monitor revenue.
5. Use forecasting methods that users can understand.
6. Evaluate forecast performance with suitable time series metrics.
7. Detect anomalies with a clear statistical method.
8. Export processed outputs for reporting and decision support.
9. Organize the implementation as reusable Python modules with automated tests.

## Scope and Functional Requirements

The implemented system supports these functions.

1. CSV upload with a raw data preview.
2. Flexible mapping of date, revenue, optional transactions, and optional categorical dimensions.
3. Optional mapping of holiday and promotion indicator columns for forecasting.
4. Cleaning of duplicate rows, invalid dates, invalid revenue values, and negative revenue rows.
5. Clear reporting of unique removed rows and transaction values normalized to zero.
6. Aggregation at daily, weekly, and monthly frequency.
7. KPI reporting for total revenue, average revenue, maximum revenue, minimum revenue, total transactions, average order value, and latest period over period growth.
8. Interactive charts for revenue trend, growth rate, category breakdown, forecast results, and anomalies.
9. Forecasting with Moving Average, Exponential Smoothing, and Linear Regression with calendar features.
10. Confidence intervals for Exponential Smoothing and Linear Regression.
11. Multi model comparison on the same holdout split and segment level forecast comparison.
12. Chronological 80/20 train and test evaluation with MAE and MAPE.
13. Anomaly detection with rolling z scores.
14. CSV export of cleaned aggregated data, forecast outputs, and anomaly outputs.

The project excludes real time ingestion, multivariate machine learning, database integration, authentication, and production deployment pipelines.

## Why This Problem Matters for SMEs

SMEs usually work with smaller technical teams and tighter budgets than large enterprises. They need tools that are easy to understand, affordable, and quick to adopt. A dashboard that runs locally, accepts CSV files, and explains its outputs in plain terms fits that need.

You can see the value through a simple workflow. A small retailer, wholesaler, or service business may export monthly sales from a point of sale or accounting system. Then a manager opens a spreadsheet, searches for unusual values, and estimates next month’s demand from rough averages or intuition. That workflow takes time, changes from person to person, and becomes hard to defend in front of an owner, supervisor, or investor.

ForeSightSeer improves that workflow in four practical ways.

1. The Data Quality tab helps you check whether the uploaded CSV is safe to trust before you read any KPI or forecast.
2. The Overview tab turns raw rows into a short performance summary.
3. The Forecasting tab gives you a short term demand view with transparent model comparison. You can explain the forecast and show how each model performed on held out history.
4. The anomaly workflow highlights unusual periods that deserve review before an SME makes operational decisions.

Consider a manager preparing next month’s inventory order. Without the dashboard, that manager may spend one to two hours checking spreadsheets, recalculating totals, and guessing whether the latest spike reflects real demand. With the dashboard, the manager uploads a CSV, confirms data quality, compares forecast options, and exports a forward looking table for a planning discussion. This example shows the practical value the project aims to deliver. It does not claim measured ROI.

Interpretability matters because users need trust before they act. SME users are more likely to use a system when they can see how it cleans data, calculates KPIs, evaluates forecasts, and flags anomalies.

## System Architecture

The application uses a modular Python design.

Files and folders

app.py
Provides the Streamlit interface and controls the user workflow.

src/features.py
Creates calendar, holiday, and promotion features.

src/preprocessing.py
Handles validation, cleaning, aggregation, and data quality reporting.

src/kpis.py
Calculates KPI values and growth rates.

src/forecasting.py
Implements Moving Average, Exponential Smoothing, Linear Regression, train and test splitting, and forecast metrics.

src/anomaly_detection.py
Implements rolling z score anomaly detection.

src/visualization.py
Builds Plotly charts.

src/utils.py
Provides formatting and export helpers.

tests/
Contains automated regression tests for the core logic.

This structure keeps the code readable and reusable. It also makes testing easier because most business logic sits outside the Streamlit UI layer.

## Data Preprocessing Design

The preprocessing pipeline follows these steps.

1. Validate the selected date and revenue columns.
2. Remove exact duplicate rows.
3. Standardize column names to internal names such as date, revenue, and transactions when available.
4. Convert dates to pandas datetime values.
5. Convert revenue and transaction columns to numeric values.
6. Remove rows with invalid dates.
7. Remove rows with missing or non numeric revenue values.
8. Remove negative revenue rows by default.
9. Normalize invalid transaction values to zero.
10. Clip negative transaction values to zero.
11. Sort the cleaned data by date.
12. Return a data quality report with counts, missing values, and the date range.

One design choice improves clarity. The dashboard reports unique removed rows after deduplication. It avoids misleading totals caused by overlapping issue counts. This makes the Data Quality tab easier to explain during evaluation.

The final implementation also handles upload and mapping mistakes more safely. It warns you when an uploaded CSV has no obvious date like or revenue like column names. It checks whether the selected date and revenue fields look parseable in sample rows. It blocks the same column from being used as both date and revenue. It also explains the issue clearly when all rows disappear during cleaning because you mapped the wrong field.

## Aggregation and KPI Design

After cleaning, the system aggregates data at the selected time level.

1. Daily.
2. Weekly.
3. Monthly.

For each period, the system sums revenue. When the dataset includes a transactions column, it also sums transactions. Optional holiday or promotion columns can stay in the aggregated dataset, so the forecasting module can use them as event signals.

The KPI module then calculates these indicators.

1. Total revenue.
2. Average revenue.
3. Maximum revenue.
4. Minimum revenue.
5. Total transactions.
6. Average order value.
7. Latest period over period growth.

These indicators give you a compact view of business performance.

## Forecasting Methodology

The project uses three forecasting methods that users can understand and explain.

### 9.1 Moving Average

Moving Average acts as a simple baseline. The model predicts the next value from the average of the most recent observations.

During evaluation, it uses walk forward forecasting. After each test period, the actual value joins the history before the model predicts the next period. This setup reflects a realistic forecasting process because the model only uses information that would already be available at prediction time.

This method works well for stable short term patterns and gives users a clear baseline for comparison.

### 9.2 Exponential Smoothing

The system implements Exponential Smoothing with statsmodels. It supports two options.

1. Additive trend.
2. Additive seasonality when the training data has enough history.

This method gives more weight to recent observations and can adapt when a trend exists. It can struggle with short, noisy, or irregular histories. The dashboard handles these cases with warnings and fallback behavior where needed.

### 9.3 Linear Regression with Calendar Features

The final version also includes an interpretable Linear Regression model. Its feature matrix includes a time index, calendar effects, built in holiday indicators, and optional uploaded holiday or promotion flags.

This model helps when demand follows weekly or monthly patterns, or when known promotional periods affect sales. The dashboard exposes the learned coefficients, which improves explainability during the final defense.

### 9.4 Evaluation Strategy

The project uses a chronological 80/20 train and test split because time series observations must keep their order. The first 80% of periods train the model. The final 20% test it.

The dashboard reports two evaluation metrics.

1. MAE, which measures the average absolute forecast error.
2. MAPE, which measures the average percentage forecast error and excludes rows where actual revenue equals zero.

If all valid actual values equal zero, the system reports MAPE as unavailable. This avoids an invalid percentage result.

The Forecasting tab can evaluate all available models on the same chronological split and compare them directly with MAE and MAPE. It can also compare future forecasts across major product or store segments.

### 9.5 Handling Missing Periods

Before forecasting, the system creates a regular time series and fills missing periods with zero revenue. This prevents model failures and keeps frequency consistent. You still need to interpret this carefully. In some real datasets, a missing period may mean missing data rather than zero sales.

## 10. Anomaly Detection Methodology

The dashboard uses rolling z score anomaly detection. It compares the current observation with a baseline built only from previous observations.

The method follows these steps.

1. Shift revenue by one period.
2. Compute a rolling mean from previous periods.
3. Compute a rolling standard deviation from previous periods.
4. Calculate a z score for the current observation.
5. Flag observations where the absolute z score exceeds the selected threshold.

This method fits the project because users can understand why each point was flagged. It also avoids using future observations to judge the current period.

## 11. Implementation Summary

The final user workflow works like this.

1. Upload a CSV file or use the bundled sample dataset.
2. Map the relevant columns.
3. Select the aggregation frequency.
4. Apply categorical filters when needed.
5. Review the Data Quality tab.
6. Review KPI and trend outputs in the Overview tab.
7. Run forecasting and compare methods.
8. Inspect anomalies.
9. Export the generated outputs.

The project uses Streamlit because it turns Python analysis into an interactive dashboard quickly. It also avoids the extra complexity of a separate frontend stack.

### 11.1 Design Rationale and Alternative Approaches

The project considered several implementation paths.

A full frontend and backend architecture would add delivery complexity without enough value for a bachelor level analytical dashboard. Advanced forecasting models would require more feature engineering, reduce transparency, and make evaluation harder to explain to SME users.

The final design uses clear statistical methods, modular Python components, and a fast interactive interface. This choice matches the project constraints: one semester of work, SME focused usability, and a methodology that you can defend during committee evaluation.

### 11.2 Innovation and Technical Depth

The project does not depend on a new forecasting algorithm. Its technical depth comes from combining several analytical capabilities into one clear product.

1. Flexible CSV column mapping instead of a rigid input schema.
2. Transparent preprocessing with explicit data quality reporting.
3. Walk forward Moving Average evaluation.
4. Configurable Exponential Smoothing with warning handling.
5. Rolling z score anomaly detection based only on historical context.
6. Exportable analytical outputs.
7. Automated regression tests for the most important analytical logic.

The project contributes at the product design level. It combines data validation, KPI monitoring, forecasting, anomaly detection, and export in one tool while keeping the workflow understandable for non expert users.

### 11.3 Ethical and Social Considerations

The project includes practical and ethical considerations.

1. Business data may contain sensitive revenue information, so local execution and CSV based processing reduce unnecessary exposure.
2. Analytical outputs should support managerial judgment.
3. Anomalies and forecasts give useful signals, but users should review them before making decisions.
4. The bundled sample dataset is synthetic and clearly separated from real business data.

Responsible analytical systems should show uncertainty and avoid misleading users. This project follows that approach through clear metrics, warnings, and explainable methods.

## 12. Evaluation Results Based on the Bundled Sample Dataset

The bundled sample dataset is synthetic. It exists only for demonstration and application evaluation.

### 12.1 Data Quality Results

Using the current implementation on the sample dataset produced these preprocessing results.

Raw rows: 6,840
Clean rows: 6,840
Duplicates removed: 0
Unique invalid rows removed: 0
Invalid dates removed: 0
Invalid revenue rows removed: 0
Negative revenue rows removed: 0
Invalid transactions normalized to 0: 0
Negative transactions clipped to 0: 0
Date range: 2024-01-01 to 2025-03-31

These results match expectations because the sample dataset was designed for demonstration.

### 12.2 KPI Results

With daily aggregation on the sample dataset, the dashboard produced these KPI values.

Total revenue: $9,444,661.18
Average revenue: $20,711.98
Maximum revenue: $29,950.93
Minimum revenue: $14,290.94
Total transactions: 156,782
Average order value: $60.24
Latest revenue growth: -12.19%

### 12.3 Forecasting Results

The default daily forecast evaluation produced this comparison.

Moving Average, window = 7
Test periods: 92
MAE: 1,808.04
MAPE: 7.88%

Exponential Smoothing, trend enabled, no seasonality
Test periods: 92
MAE: 12,314.36
MAPE: 54.27%

Linear Regression, calendar features
Test periods: 92
MAE: 161,362.57
MAPE: 710.53%

On the bundled sample dataset, Moving Average performed better than Exponential Smoothing and Linear Regression under the default settings. This result strengthens the academic discussion because it shows that the project evaluates models instead of assuming that a more complex method will perform better.

### 12.4 Anomaly Detection Results

Using the default anomaly settings on the sample dataset, with window = 14 and threshold = 3.0, the system produced these results.

1. It detected 3 anomalies.
2. The first detected anomaly occurred on 2024-10-20.
3. Revenue on that date was $22,999.46.
4. The corresponding z score was 4.54.

This shows that the anomaly module can highlight unusual sales behavior in a way users can explain.

### 12.5 Testing Results

The project includes automated tests for the core business logic. The tests cover preprocessing behavior, aggregation, feature engineering, MAPE edge cases, forecasting output shape, confidence interval output, warning behavior on insufficient data, anomaly detection output structure, and transaction normalization reporting.

The final version adds more coverage for imperfect data and error handling. These tests cover missing required columns, datasets where all rows disappear during cleaning, invalid aggregation or forecasting parameters, zero horizon forecast requests, duplicate date or revenue mapping, suspicious uploaded date or revenue selections, and clearer user facing messages when a CSV has headers but no usable rows.

You can run the test suite from the project root after activating the virtual environment.

pytest

### 13. Strengths of the Final System

The final implementation has these main strengths.

1. Clear and explainable methodology.
2. Modular code organization.
3. Transparent data quality reporting.
4. Automated test coverage for core logic.
5. Multi model evaluation instead of one forecast path.
6. Useful visual outputs for a live presentation.
7. Export functionality for practical use.

These strengths make the project suitable for academic evaluation and live demonstration. They also support the business case for SME use because the system helps users judge whether the outputs are reliable enough for a decision.

14. Limitations

The final system has clear limitations.

1. Moving Average and Exponential Smoothing use only historical revenue.
2. Linear Regression adds calendar structure plus optional holiday and promotion indicators, but it still excludes richer external drivers such as marketing spend, pricing, and weather.
3. Filling missing periods with zero revenue may not match every real business case.
4. Exponential Smoothing can perform poorly on irregular or highly intermittent data.
5. Linear Regression can perform poorly when calendar or event features do not explain revenue variation.
6. The dashboard supports interactive analysis instead of automated production forecasting.
7. The project does not include authentication, a database, or real time ingestion.

Stating these limitations strengthens the final thesis or defense because it shows that the project treats results carefully.

15. Future Work

Future work can improve the system in these ways.

1. Add custom business specific holiday calendars instead of relying only on built in calendar logic.
2. Include richer causal drivers such as pricing, discounts, marketing spend, and weather.
3. Add more interpretable forecasting models for intermittent demand.
4. Add export bundles and summary reports for segment level forecast comparisons.
5. Add guidance for cloud hosting.
6. Expand evaluation with rolling origin backtesting across more datasets.

16. Conclusion

This project delivers a practical and explainable dashboard for SME sales analysis. It combines data cleaning, KPI monitoring, forecasting, anomaly detection, and export in one interface. You can explain the workflow clearly during a bachelor project presentation.

The final implementation matches the project goal: build an accessible decision support tool with clear methods and measurable outputs. Modular Python code, transparent statistical methods, and automated tests make the system technically coherent and academically defensible.

The evaluation on the bundled sample dataset shows that the dashboard works end to end and produces results that you can discuss critically. The main contribution is a practical workflow that helps a smaller business move from manual spreadsheet checking to clearer and more data backed short term decisions.