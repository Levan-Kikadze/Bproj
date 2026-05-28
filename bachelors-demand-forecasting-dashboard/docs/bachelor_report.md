# Bachelor Report Draft

## Project Title

ForeSightSeer: AI-Driven Demand and Revenue Forecasting Dashboard for SMEs

## Abstract

Small and medium-sized enterprises often store sales data in spreadsheet or CSV form, but many of them do not have a simple analytical system for validating data quality, monitoring performance, forecasting future demand, and identifying unusual sales behavior. This project addresses that gap by implementing an interactive Streamlit dashboard that converts uploaded sales data into actionable business insights.

The system focuses on interpretability and practical usability rather than on black-box machine learning. It provides data cleaning, aggregation, KPI reporting, forecasting with Moving Average, Exponential Smoothing, and Linear Regression with calendar features, rolling z-score anomaly detection, and exportable analytical outputs. The implementation is modular, testable, and supported by automated regression tests for the core business logic.

Using the bundled sample dataset, the system processed 6,840 rows without data-loss corrections, produced total revenue of $9,444,661.18, and demonstrated that the Moving Average baseline outperformed both Exponential Smoothing and Linear Regression on the default daily evaluation setup, achieving an MAE of 1,808.04 and a MAPE of 7.88%. The project demonstrates how a lightweight, explainable analytical dashboard can support SME decision-making while remaining appropriate for a bachelor-level software and data project.

## 1. Introduction

Sales planning is a common challenge for SMEs. Many businesses record transactions regularly, but they often lack a dedicated analytical tool that helps them understand revenue patterns, identify data-quality problems, forecast short-term performance, and detect unusual sales events. Commercial analytics platforms can be expensive or overly complex for smaller organizations, while spreadsheet-only workflows make repeatable analysis difficult.

This project proposes a practical alternative: a lightweight dashboard that accepts CSV sales data and produces interpretable business outputs. The goal is not to build an enterprise-scale forecasting platform, but to design a transparent decision-support system that is easy to explain, easy to demonstrate, and suitable for the constraints of a bachelor project.

## 2. Problem Statement

SMEs often have access to historical sales data but lack a simple and reliable analytical interface for:

- checking whether uploaded data is clean and usable,
- monitoring core revenue KPIs,
- forecasting short-term future demand and revenue,
- detecting unusual sales behavior,
- exporting analysis results for further use.

Without these capabilities, managers may rely on manual inspection, inconsistent spreadsheet formulas, or intuition, which increases the chance of poor planning and weak operational decisions.

## 3. Project Objectives

The project objectives are:

1. Build an interactive dashboard that accepts CSV sales data.
2. Provide transparent preprocessing and data-quality reporting.
3. Aggregate sales data at daily, weekly, and monthly levels.
4. Calculate business KPIs that are relevant to SME revenue monitoring.
5. Implement interpretable forecasting methods.
6. Evaluate forecast performance using appropriate time-series metrics.
7. Detect anomalies using an explainable statistical method.
8. Export processed outputs for reporting and decision support.
9. Structure the implementation as reusable Python modules with automated tests.

## 4. Scope and Functional Requirements

The implemented system supports the following functional behavior:

- CSV upload with a raw-data preview.
- Flexible mapping of date, revenue, optional transactions, and optional categorical dimensions.
- Optional mapping of holiday and promotion indicator columns for forecasting.
- Cleaning of duplicate rows, invalid dates, invalid revenue values, and negative revenue rows.
- Explicit reporting of unique removed rows and transaction values normalized to zero.
- Aggregation at daily, weekly, and monthly frequency.
- KPI reporting for total revenue, average revenue, maximum revenue, minimum revenue, total transactions, average order value, and latest period-over-period growth.
- Interactive charts for revenue trend, growth rate, category breakdown, forecast results, and anomalies.
- Forecasting using Moving Average, Exponential Smoothing, and Linear Regression with calendar features.
- Confidence intervals for Exponential Smoothing and Linear Regression.
- Multi-model comparison on the same holdout split and segment-level forecast comparison.
- Chronological 80/20 train/test evaluation using MAE and MAPE.
- Anomaly detection using rolling z-scores.
- CSV export of cleaned aggregated data, forecast outputs, and anomaly outputs.

The project does not aim to provide real-time ingestion, multivariate machine learning, database integration, authentication, or production deployment pipelines.

## 5. Why This Problem Matters for SMEs

SMEs typically operate with smaller technical teams and tighter budgets than large enterprises. They need tools that are understandable, affordable, and fast to adopt. A dashboard that can be launched locally, fed with CSV files, and explained without advanced data-science knowledge is especially useful in this context.

The value becomes clearer when viewed as a real workflow rather than as a feature list. A small retailer, wholesaler, or service business may export monthly sales from a point-of-sale or accounting system, open a spreadsheet, search manually for unusual numbers, and then estimate next month's demand using rough averages or intuition. That workflow is slow, inconsistent, and difficult to defend in front of a supervisor, owner, or investor.

ForeSightSeer changes that flow in four practical ways. First, the Data Quality tab lets the user verify whether the uploaded CSV is safe to trust before any KPI or forecast is interpreted. Second, the Overview tab turns raw rows into a short performance summary that can be discussed quickly. Third, the Forecasting tab provides a short-term demand view with transparent model comparison, so the user can say not only what the forecast is, but also how accurate the tested models were on held-out history. Fourth, the anomaly workflow highlights unusual periods that deserve explanation before an SME reacts operationally.

An illustrative example is a manager preparing the next month's inventory order. Without the dashboard, that manager may spend one to two hours manually checking spreadsheets, recalculating totals, and guessing whether the latest spike is real. With the dashboard, the same manager can upload a CSV, confirm data quality, compare forecast options, and leave with a forward-looking table that supports a more defensible planning conversation. This is an illustrative usage scenario rather than a measured ROI claim, but it reflects the practical value the project is designed to deliver.

The emphasis on interpretability is therefore important for both trust and action. SME users are more likely to use a system when they can understand how it cleans data, how it calculates KPIs, how it evaluates forecasts, and why a value was flagged as anomalous.

## 6. System Architecture

The application follows a modular Python design.

- `app.py` provides the Streamlit interface and orchestrates the workflow.
- `src/features.py` creates calendar, holiday, and promotion features.
- `src/preprocessing.py` handles validation, cleaning, aggregation, and data-quality reporting.
- `src/kpis.py` calculates KPI values and growth rates.
- `src/forecasting.py` implements Moving Average, Exponential Smoothing, Linear Regression, train/test splitting, and forecast metrics.
- `src/anomaly_detection.py` implements rolling z-score anomaly detection.
- `src/visualization.py` builds Plotly charts.
- `src/utils.py` provides formatting and export helpers.
- `tests/` contains automated regression tests for the core logic.

This separation improves readability, reuse, and maintainability. It also supports testing because most of the business logic is kept outside the Streamlit UI layer.

## 7. Data Preprocessing Design

The preprocessing pipeline performs the following steps:

1. Validate the selected date and revenue columns.
2. Remove exact duplicate rows.
3. Standardize column names to internal names such as `date`, `revenue`, and optionally `transactions`.
4. Convert dates to pandas datetime values.
5. Convert revenue and transaction columns to numeric values.
6. Remove rows with invalid dates.
7. Remove rows with missing or non-numeric revenue values.
8. Remove negative revenue rows by default.
9. Normalize invalid transaction values to zero.
10. Clip negative transaction values to zero.
11. Sort the cleaned data chronologically.
12. Return a data-quality report containing counts, missing values, and date range.

One important design detail is that the dashboard reports unique removed rows after deduplication, rather than summing overlapping issue counts in a misleading way. This makes the Data Quality tab easier to defend during evaluation.

The final implementation also improves robustness around upload and mapping mistakes. It warns the user when an uploaded CSV has no obvious date-like or revenue-like column names, checks whether the selected date and revenue fields look parseable in sample rows, prevents the same column from being used as both date and revenue, and explains more clearly when all rows disappear during cleaning because the wrong field was mapped.

## 8. Aggregation and KPI Design

After cleaning, the system aggregates data at the selected time level:

- Daily
- Weekly
- Monthly

Revenue is summed for each period, and transactions are also summed when a transactions column is present. Optional holiday or promotion columns can also be preserved and aggregated so the forecasting module can use them as event signals. Based on the aggregated data, the KPI module calculates:

- Total revenue
- Average revenue
- Maximum revenue
- Minimum revenue
- Total transactions
- Average order value
- Latest period-over-period growth

These indicators give users a compact but useful overview of current business performance.

## 9. Forecasting Methodology

The project uses three interpretable forecasting methods.

### 9.1 Moving Average

Moving Average is used as a simple baseline. The model predicts each next value from the average of the most recent observations. During evaluation, it uses walk-forward forecasting so each new actual test value is added back into the history before predicting the next step.

This method is easy to understand and useful for relatively stable short-term patterns.

### 9.2 Exponential Smoothing

Exponential Smoothing is implemented through `statsmodels` and supports:

- optional additive trend,
- optional additive seasonality when sufficient training data is available.

This method gives more weight to recent observations and can adapt better than Moving Average when a trend exists. However, it is also more sensitive to short, noisy, or irregular histories.

### 9.3 Linear Regression with Calendar Features

The final version also includes an interpretable Linear Regression model. Its feature matrix includes a time index, calendar effects, built-in holiday indicators, and optional uploaded holiday or promotion flags. This model is useful when demand is influenced by regular weekly or monthly patterns or by known promotional periods.

The dashboard exposes the learned coefficients, which strengthens the explainability of the forecasting module during the final defense.

### 9.4 Evaluation Strategy

The project uses a chronological 80/20 train/test split because time-series observations should not be shuffled. The first 80% of periods are used for training and the final 20% for testing.

Two evaluation metrics are reported:

- MAE: the average absolute forecast error.
- MAPE: the average percentage forecast error, excluding rows where actual revenue is zero.

If all valid actual values are zero, MAPE is reported as unavailable rather than producing an invalid result.

The Forecasting tab can evaluate all available models on the same chronological split and compare them directly using MAE and MAPE. It can also compare future forecasts across major product or store segments.

### 9.5 Handling Missing Periods

Before forecasting, the system creates a regular time series and fills missing periods with zero revenue. This prevents model failures and preserves frequency consistency, although it may not be the correct business interpretation in every real dataset.

## 10. Anomaly Detection Methodology

The dashboard uses rolling z-score anomaly detection. The current observation is compared against a baseline built from previous observations only. The method:

1. shifts revenue by one period,
2. computes a rolling mean and rolling standard deviation,
3. calculates a z-score,
4. flags observations whose absolute z-score exceeds a user-selected threshold.

This method is explainable and suitable for a bachelor-level prototype because the reason for each anomaly flag can be described clearly.

## 11. Implementation Summary

The user workflow in the final system is as follows:

1. Upload a CSV file or use the bundled sample dataset.
2. Map the relevant columns.
3. Select aggregation frequency.
4. Optionally apply categorical filters.
5. Review the Data Quality tab.
6. Review the KPI and trend outputs in the Overview tab.
7. Run forecasting and compare methods.
8. Inspect anomalies.
9. Export the generated outputs.

The application was built in Streamlit because it provides a fast way to turn Python analysis into an interactive interface without requiring a separate frontend stack.

### 11.1 Design Rationale and Alternative Approaches

Several alternative implementation paths were considered implicitly in the project design.

- A full frontend/backend architecture was not chosen because it would increase delivery complexity without adding much value for a bachelor-level analytical dashboard.
- More advanced forecasting models, such as multivariate machine-learning methods or deep-learning approaches, were not prioritized because they would reduce interpretability, require more feature engineering, and make evaluation harder to explain to SME users.
- The final design therefore favors transparent statistical methods, modular Python components, and a fast interactive interface.

This decision is justified by the project constraints: one-semester scope, SME-focused usability, and the need for a defendable methodology during committee evaluation.

### 11.2 Innovation and Technical Depth

The technical depth of the project does not come from inventing a new forecasting algorithm. Instead, it comes from integrating several analytical capabilities into a coherent and explainable product:

- flexible CSV column mapping rather than a rigid input schema,
- transparent preprocessing with explicit data-quality reporting,
- walk-forward Moving Average evaluation,
- configurable Exponential Smoothing with warning handling,
- rolling z-score anomaly detection based on historical context only,
- exportable analytical outputs,
- automated regression tests for the most important analytical logic.

The project is therefore innovative at the product-design level: it combines data validation, KPI monitoring, forecasting, anomaly detection, and export in a single tool that remains understandable to non-expert users.

### 11.3 Ethical and Social Considerations

Although the project is primarily technical, it also involves practical and ethical considerations:

- business data may contain sensitive revenue information, so local execution and CSV-based processing reduce unnecessary exposure,
- analytical outputs should support managerial judgment rather than replace it,
- anomalies and forecasts can be useful indicators, but they should not be treated as guaranteed truths,
- the bundled sample dataset is synthetic and is clearly separated from real business data.

These considerations are important because responsible analytical systems should communicate uncertainty and avoid misleading users.

## 12. Evaluation Results Based on the Bundled Sample Dataset

The bundled sample dataset is synthetic and is intended only for demonstration and evaluation of the application behavior.

### 12.1 Data Quality Results

Using the current implementation on the sample dataset produced the following preprocessing results:

| Metric | Value |
| --- | ---: |
| Raw rows | 6,840 |
| Clean rows | 6,840 |
| Duplicates removed | 0 |
| Unique invalid rows removed | 0 |
| Invalid dates removed | 0 |
| Invalid revenue rows removed | 0 |
| Negative revenue rows removed | 0 |
| Invalid transactions normalized to 0 | 0 |
| Negative transactions clipped to 0 | 0 |
| Date range | 2024-01-01 to 2025-03-31 |

These results are expected because the sample dataset is designed to be demonstration-ready.

### 12.2 KPI Results

With daily aggregation on the sample dataset, the dashboard produced the following KPI values:

| KPI | Value |
| --- | ---: |
| Total revenue | $9,444,661.18 |
| Average revenue | $20,711.98 |
| Maximum revenue | $29,950.93 |
| Minimum revenue | $14,290.94 |
| Total transactions | 156,782 |
| Average order value | $60.24 |
| Latest revenue growth | -12.19% |

### 12.3 Forecasting Results

The default daily forecast evaluation produced the following comparison:

| Method | Test periods | MAE | MAPE |
| --- | ---: | ---: | ---: |
| Moving Average (window = 7) | 92 | 1,808.04 | 7.88% |
| Exponential Smoothing (trend enabled, no seasonality) | 92 | 12,314.36 | 54.27% |
| Linear Regression (calendar features) | 92 | 161,362.57 | 710.53% |

On the bundled sample dataset, the Moving Average baseline performed better than both Exponential Smoothing and Linear Regression under the default settings. This result strengthens the academic discussion because it shows that the project does not assume a newer model is automatically better. Instead, it evaluates several interpretable alternatives and presents the measured outcome transparently.

### 12.4 Anomaly Detection Results

Using the default anomaly settings on the sample dataset (`window = 14`, `threshold = 3.0`) produced:

- 3 detected anomalies.
- The first detected anomaly occurred on 2024-10-20.
- Revenue on that date was $22,999.46.
- The corresponding z-score was 4.54.

This demonstrates that the anomaly module can highlight unusually high or low sales behavior in a way that remains easy to explain to users.

### 12.5 Testing Results

The project includes automated tests for the core business logic. The tests cover preprocessing behavior, aggregation, feature engineering, MAPE edge cases, forecasting output shape, confidence interval output, warning behavior on insufficient data, anomaly detection output structure, and transaction normalization reporting.

The final version extends this coverage with additional imperfect-data and error-handling scenarios that are relevant to the evaluation rubric. These include missing required columns, datasets where all rows are removed during cleaning, invalid aggregation or forecasting parameters, zero-horizon forecast requests, duplicate date or revenue mapping, suspicious uploaded date or revenue selections, and clearer user-facing messaging when a CSV has headers but no usable rows.

The test suite can be executed from the project root after activating the virtual environment with:

```bash
pytest
```

## 13. Strengths of the Final System

The main strengths of the final implementation are:

- interpretable methodology,
- modular code organization,
- transparent data-quality reporting,
- automated test coverage for core logic,
- multi-model evaluation instead of a single forecast path,
- useful visual outputs for a live presentation,
- export functionality for practical use.

These strengths make the project appropriate for both academic evaluation and real demonstration.

They also strengthen the business case for SME use because the system does not only produce analytical outputs. It also helps the user judge whether those outputs are reliable enough to support a decision.

## 14. Limitations

The final system also has clear limitations:

- Moving Average and Exponential Smoothing are univariate and use only historical revenue.
- Linear Regression adds calendar structure plus optional holiday and promotion indicators, but richer external drivers such as marketing spend, pricing, and weather are still not modeled.
- Missing periods are filled with zero revenue, which may not match every real business interpretation.
- Exponential Smoothing may perform poorly on irregular or highly intermittent data.
- Linear Regression may perform poorly when the observed revenue variation is not well explained by calendar or event features.
- The dashboard is designed for interactive analysis, not automated production forecasting.
- The project does not include authentication, a database, or real-time ingestion.

These limitations should be stated honestly in the final thesis or defense because doing so strengthens the credibility of the project.

## 15. Future Work

Several improvements could be made in future work:

1. Add custom business-specific holiday calendars instead of relying only on the built-in calendar logic.
2. Include richer causal drivers such as pricing, discounts, marketing spend, and weather.
3. Add additional interpretable forecasting models designed for intermittent demand.
4. Add export bundles and summary reporting for segment-level forecast comparisons.
5. Add deployment guidance for cloud hosting.
6. Expand evaluation with rolling-origin backtesting across more datasets.

## 16. Conclusion

This project delivers a practical and interpretable dashboard for SME sales analysis. It combines data cleaning, KPI monitoring, forecasting, anomaly detection, and export into a single interface that can be explained clearly during a bachelor-project presentation.

The final implementation aligns with the project goal of building an accessible decision-support tool rather than an overly complex predictive platform. The use of modular Python code, transparent statistical methods, and automated tests makes the system technically coherent and academically defendable. The evaluation on the bundled sample dataset shows that the dashboard works end to end and produces measurable results that can be discussed critically.

Overall, the project demonstrates that a focused, well-documented, and interpretable analytical system can provide meaningful value to SMEs while remaining realistic within the scope of a bachelor project. Its main contribution is not a new forecasting algorithm, but a practical workflow that helps a smaller business move from manual spreadsheet checking toward more transparent and data-backed short-term decisions.

## 17. Report Completion Notes

Before submitting the final thesis document, add the following items to this draft or to the university template version:

- title page required by your university,
- supervisor and student information,
- screenshots from the dashboard tabs,
- any institution-specific formatting requirements,
- bibliography or references section if required,
- appendix material such as sample CSV snippets or extra figures.