# Dashboard Help Guide

## Purpose of This Guide

This page explains how to use the dashboard if you are new to data analysis, charts, or forecasting. It focuses on plain-language interpretation rather than technical formulas.

When you work inside the app, look for the small `i` buttons next to section titles. Those popovers give short explanations for the chart or table directly beside them. This guide is the full version.

## Before You Start

The dashboard can work with two kinds of data sources:

- Bundled demo datasets: built-in practice datasets designed to showcase specific features such as clean analysis, data quality problems, holiday or promotion effects, and anomalies.
- Uploaded CSV: your own file.

To get useful results, your dataset should have at least:

- one column containing dates,
- one column containing revenue or sales values.

Optional columns make the dashboard more informative:

- transactions or order count,
- holiday indicator,
- promotion indicator,
- category columns such as store, product, product category, or region.

## Dataset Source and Column Mapping

### Dataset Source

The `Dataset source` selector controls where the dashboard data comes from.

- `Bundled demo dataset`: use this when you want to learn the app or demonstrate features.
- `Upload CSV`: use this when you want to analyze your own business data.

If you are unsure how the app works, start with a bundled dataset before uploading your own file.

### Bundled Demo Dataset Selector

When bundled mode is active, choose one of the practice datasets:

- `Full clean sample`: best for the normal end-to-end demo.
- `Data quality issues showcase`: best for explaining duplicates, missing values, invalid dates, and row removal.
- `Holiday and promotion showcase`: best for explaining optional event features, confidence intervals, and segment comparison.
- `Anomalies and missing periods showcase`: best for explaining anomaly detection and forecasting with missing dates.

### Column Mapping

Column mapping tells the app what each field means.

- `Date column`: the time field used in charts and forecasting.
- `Revenue column`: the numeric value that represents sales or revenue.
- `Transactions column`: optional count of orders or transactions.
- `Holiday column`: optional yes or no style indicator for holiday periods.
- `Promotion column`: optional yes or no style indicator for promotions or campaigns.
- `Filter/group columns`: category fields used for filtering and breakdown charts.

If a chart looks strange, check the mapping first. Wrong mapping is one of the most common reasons for confusing output.

## Aggregation and Filters

### Aggregation Frequency

Aggregation controls the time granularity of analysis.

- `Daily`: most detailed, shows more noise and short-term movement.
- `Weekly`: smoother, good for medium-level trend inspection.
- `Monthly`: highest-level summary, best for broad planning.

Changing aggregation changes the meaning of every chart and KPI. For example, average revenue per daily period is not the same as average revenue per monthly period.

### Filters

Filters narrow the dataset before charts, KPIs, forecasts, and anomaly detection are calculated.

This means the dashboard is always answering the question:

"What do the results look like for the currently selected subset of the data?"

Use filters when you want to answer questions such as:

- How is one store performing?
- Which product category is strongest?
- What happens if I focus only on one product line?

If the results look unexpectedly low or high, check whether filters are active.

## Raw Data Preview

The raw preview shows the dataset before cleaning.

Use it to verify:

- the file loaded correctly,
- date values look real,
- revenue looks numeric,
- category names are spelled consistently,
- the expected columns exist.

This is not the final cleaned dataset. It is only the starting point.

## Overview Tab

The Overview tab is the best place to begin interpretation.

### KPI Summary

The KPI cards give a quick performance snapshot:

- `Total Revenue`: the total revenue across all currently selected rows.
- `Average Revenue`: average revenue per aggregated period.
- `Maximum Revenue`: highest revenue period in the selected view.
- `Minimum Revenue`: lowest revenue period in the selected view.
- `Total Transactions`: total count of transactions, if a transactions column exists.
- `Average Order Value`: revenue divided by transactions, if transactions are available.
- `Latest Revenue Growth`: the most recent period's growth compared with the previous period.

Interpretation tips:

- High total revenue does not always mean strong recent performance; check growth too.
- Large gaps between maximum and minimum revenue can indicate volatility or seasonality.
- Average order value is useful only if transaction data is accurate.

### Revenue Trend Chart

This line chart shows how revenue changes over time.

How to read it:

- move from left to right to follow time,
- read the height of the line to judge revenue level,
- look for upward drift, downward drift, repeating waves, or sudden breaks.

What it is good for:

- spotting trend direction,
- seeing whether revenue is stable or unstable,
- recognizing seasonality or shock events.

What not to do:

- do not compare it directly with the breakdown bar chart, because one is time-based and the other is segment-based.

### Revenue Growth Rate Chart

This chart shows change from one period to the next.

How to read it:

- above zero means revenue increased versus the previous period,
- below zero means revenue decreased,
- values far from zero mean stronger change.

What it is good for:

- detecting acceleration or slowdown,
- finding periods of instability,
- seeing whether trend changes happened gradually or suddenly.

### Revenue Breakdown Chart

This bar chart compares revenue across one selected category such as product category, store, or product.

How to read it:

- taller bar = higher revenue contribution,
- shorter bar = lower contribution.

What it is good for:

- comparing segments,
- identifying strongest and weakest contributors,
- supporting decisions about where revenue is concentrated.

What not to do:

- do not use it to judge trend over time.

## Data Quality Tab

This tab explains what happened to the data before analysis.

### Data Quality Summary Cards

Important fields:

- `Original Rows`: how many rows were in the source file.
- `Final Clean Rows`: how many rows remained after cleaning.
- `Duplicates Removed`: exact duplicate rows removed.
- `Rows Removed`: unique rows removed because of invalid or negative core values.
- `Invalid Dates`: rows removed because dates could not be parsed.
- `Invalid/Missing Revenue`: rows removed because revenue was missing or non-numeric.
- `Negative Revenue Removed`: rows removed because revenue was below zero.

If a transactions column exists, two more fields appear:

- `Invalid Transactions Set to 0`
- `Negative Transactions Set to 0`

Interpretation tips:

- A few removed rows are normal in messy business data.
- Large removal counts mean you should explain data quality before presenting forecasts.
- Transaction corrections matter because they affect average order value.

### Missing Values Table

This table counts missing cells by original column.

Use it to understand where the dataset is weak. Missing values in descriptive columns may be acceptable; missing values in core fields such as revenue or date are more serious.

### Cleaned Data Preview

This table shows what remained after cleaning.

Use it to confirm that:

- dates are valid,
- revenue is numeric,
- negative revenue rows are gone,
- corrected transaction values look reasonable.

### Filtered Data Preview

This table shows the final subset used in the dashboard after sidebar filters are applied.

If your charts or KPIs seem surprising, inspect this table first.

## Forecasting Tab

The Forecasting tab compares models and then shows one selected model in detail.

### Forecasting Controls

- `Models to evaluate`: choose which models to run.
- `Detailed model view`: pick the model whose chart and detailed tables you want to inspect.
- `Future horizon`: choose how many future periods to forecast.
- `Confidence level`: controls uncertainty band width for supported models.
- `Segment comparison`: optionally compare future forecasts across top segments.
- `Moving average window`: how many recent periods the Moving Average model uses.
- `Use trend`: whether Exponential Smoothing should model a steady rise or fall.
- `Use seasonality`: whether Exponential Smoothing should model repeating cycles.

### Model Comparison Table

This table is the most important forecasting summary.

Fields:

- `MAE`: average absolute error. Lower is better.
- `MAPE`: average percentage error. Lower is better.
- `test_periods`: number of historical periods used for evaluation.
- `future_periods`: number of forecasted future periods.
- `warnings`: problems or limitations that affected the model.

Interpretation tips:

- Start by comparing MAE across models.
- Use MAPE for relative error, but remember it can behave badly when actual values are small.
- A model with warnings may still run, but it needs more cautious interpretation.

### Forecast Chart

This chart overlays actual history, test predictions, and future forecasts.

How to read it:

- historical line = known actual revenue,
- test forecast = how the model performed on held-out history,
- future forecast = projected unknown periods,
- interval bands = uncertainty around forecast values.

What it is good for:

- judging whether the model follows real behavior,
- seeing whether the model is consistently too high or too low,
- understanding uncertainty in future predictions.

### Test Forecast Table

This table is best when you want exact row-level comparison between actual and predicted values.

Use it to inspect:

- which dates had the largest errors,
- whether the model systematically underpredicts or overpredicts,
- whether the interval contained the actual value.

### Future Forecast Table

This table is the actionable forecast output.

Use it to answer questions such as:

- What revenue range should I expect next week?
- Which future periods look strongest or weakest?
- How uncertain is the forecast?

### Model Coefficients

This section appears for Linear Regression.

How to read it:

- positive coefficient = feature tends to increase predicted revenue,
- negative coefficient = feature tends to decrease predicted revenue,
- larger absolute value = stronger directional influence inside that model.

This section is useful for explainability, but coefficients should be discussed carefully. They do not prove causation on their own.

### Segment Comparison

This section compares forecasts across top segments such as stores or categories.

Use it to answer:

- which segment is forecast to generate the most revenue,
- which segment is weaker,
- whether model accuracy differs by segment.

## Anomaly Detection Tab

This tab highlights unusual periods.

### Controls

- `Rolling window`: number of previous periods used to define normal behavior.
- `Anomaly threshold`: how extreme the z-score must be before a point is flagged.

Interpretation tips:

- lower threshold = more anomalies,
- higher threshold = fewer anomalies,
- shorter rolling window = more sensitive to short-term changes,
- longer rolling window = smoother baseline.

### Anomaly Chart

How to read it:

- the main line shows revenue,
- red markers show points flagged as unusual relative to recent history.

Important reminder:

An anomaly is not automatically an error. It may reflect:

- a promotion,
- a holiday,
- a supply issue,
- a data problem,
- a real business event.

### Anomalous Rows Table

This table lists only flagged periods. It is useful for reporting exact dates and values.

### Full Anomaly Results Table

This table includes rolling mean, rolling standard deviation, z-score, and anomaly flag.

Use it if you need to explain why a point was flagged.

## Export Tab

The export buttons download the results that match your current settings.

- `Download cleaned aggregated dataset`: cleaned and aggregated data used by the charts.
- `Download forecast results`: forecast rows for the currently selected detailed model.
- `Download anomaly results`: anomaly output table.

Always remember that exports reflect the active filters and settings at the moment you click download.

## Practical Interpretation Workflow

For a safe and clear workflow, follow this order:

1. Confirm the dataset source and column mapping.
2. Check the raw preview.
3. Review the Data Quality tab.
4. Read the KPI cards in the Overview tab.
5. Inspect the trend and growth charts.
6. Compare segments if needed.
7. Open Forecasting and compare models.
8. Inspect the anomaly results.
9. Export only after you are satisfied with filters and settings.

## Common Mistakes to Avoid

- Reading filtered results as if they represent the whole dataset.
- Comparing daily and monthly KPIs as if they mean the same thing.
- Treating forecasts as exact promises instead of estimates.
- Assuming anomalies are always data errors.
- Ignoring data quality problems before interpreting forecasts.
- Choosing a model only because it is more advanced, instead of because it performs better.