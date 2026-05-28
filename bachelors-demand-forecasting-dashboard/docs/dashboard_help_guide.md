# Dashboard Help Guide

ForeSightSeer user guide for dashboard reading and demo prep.

## Purpose of This Guide

Use this guide when you're new to data analysis, charts, or forecasting. It explains what each dashboard section means in plain language.

Inside the app, look for the small i buttons next to section titles. They give short explanations beside each chart or table. This guide gives you the full version.

## Before You Start

The dashboard works with two data sources.

1. Bundled demo datasets. Use these built in practice datasets to show clean analysis, data quality issues, holiday effects, promotion effects, and anomalies.
2. Uploaded CSV. Use your own file when you want to analyze real business data.

For useful results, your dataset needs at least these columns.

1. One date column.
2. One revenue or sales column.

These optional columns make the dashboard more useful.

1. Transactions or order count.
2. Holiday indicator.
3. Promotion indicator.
4. Category columns such as store, product, product category, or region.

## Dataset Source and Column Mapping

Dataset Source

The Dataset source selector decides where the dashboard gets data.

1. Bundled demo dataset. Choose this when you want to learn the app or show features.
2. Upload CSV. Choose this when you want to analyze your own business data.

Start with a bundled dataset if you're still learning how the app works.

Bundled Demo Dataset Selector

When you use bundled mode, choose the practice dataset that fits your goal.

1. Full clean sample. Use this for the normal full demo.
2. Data quality issues showcase. Use this to explain duplicates, missing values, invalid dates, and removed rows.
3. Holiday and promotion showcase. Use this to explain event features, confidence intervals, and segment comparison.
4. Anomalies and missing periods showcase. Use this to explain anomaly detection and forecasting when dates are missing.

Column Mapping

Column mapping tells the app what each field means.

1. Date column. The time field for charts and forecasts.
2. Revenue column. The numeric sales or revenue field.
3. Transactions column. An optional count of orders or transactions.
4. Holiday column. An optional yes or no indicator for holiday periods.
5. Promotion column. An optional yes or no indicator for promotions or campaigns.
6. Filter and group columns. Category fields for filters and breakdown charts.

Check the mapping first when a chart looks strange. Wrong mapping often causes confusing results.

The app warns you early when it cannot find clear date or revenue column names. It also warns you when sampled date or revenue values fail to parse, or when you select the same field as both date and revenue. Treat those warnings as stop signs. Fix them before you interpret results.

## Aggregation and Filters

Aggregation Frequency

Aggregation controls the time level of the analysis.

1. Daily. Use this for the most detail. You’ll see more noise and short changes.
2. Weekly. Use this for a smoother view and medium level trend checks.
3. Monthly. Use this for the highest level summary and broad planning.

When you change aggregation, you change every chart and KPI. Average revenue per day means something different from average revenue per month.

Filters

Filters narrow the data before the dashboard calculates charts, KPIs, forecasts, and anomalies.

The dashboard always answers this question.

What do the results look like for the data you've selected?

Use filters when you want to answer questions like these.

1. How is one store performing?
2. Which product category brings in the most revenue?
3. What changes when you focus on one product line?

Check active filters when results look too low or too high.

## Raw Data Preview

The raw preview shows your data before cleaning.

Use it to check these things.

1. The file loaded correctly.
2. Date values look real.
3. Revenue values look numeric.
4. Category names use consistent spelling.
5. The expected columns exist.

This preview shows the starting data. The dashboard still needs to clean it.

## Overview Tab

Start with the Overview tab.

Business question it answers. What is happening in the business right now?

KPI Summary

The KPI cards give you a fast performance snapshot.

1. Total Revenue. Total revenue across all selected rows.
2. Average Revenue. Average revenue per aggregated period.
3. Maximum Revenue. Highest revenue period in the selected view.
4. Minimum Revenue. Lowest revenue period in the selected view.
5. Total Transactions. Total transaction count when you provide a transactions column.
6. Average Order Value. Revenue divided by transactions when transaction data exists.
7. Latest Revenue Growth. Growth in the latest period compared with the previous period.

Use these tips when you read the KPIs.

1. Check growth as well as total revenue. High total revenue can still hide weak recent performance.
2. Look at the gap between maximum and minimum revenue. A large gap can point to volatility or seasonality.
3. Trust average order value only when transaction data looks accurate.

Revenue Trend Chart

This line chart shows how revenue changes over time.

Read it this way.

1. Move from left to right to follow time.
2. Use the height of the line to judge revenue level.
3. Look for upward movement, downward movement, repeating waves, or sudden breaks.

Use it to spot trend direction, stability, seasonality, and shock events.

Avoid direct comparison with the breakdown bar chart. The trend chart shows time. The bar chart shows segments.

Revenue Growth Rate Chart

This chart shows how revenue changes from one period to the next.

Read it this way.

1. Values above zero mean revenue increased from the previous period.
2. Values below zero mean revenue decreased.
3. Values far from zero mean the change was stronger.

Use it to find acceleration, slowdown, unstable periods, and sudden trend changes.

Revenue Breakdown Chart

This bar chart compares revenue across one selected category, such as product category, store, or product.

Read it this way.

1. A taller bar means higher revenue contribution.
2. A shorter bar means lower revenue contribution.

Use it to compare segments, find the strongest and weakest contributors, and see where revenue is concentrated.

Use the trend chart when you need to judge movement over time.

## Data Quality Tab

This tab explains how the dashboard cleaned your data before analysis.

Business question it answers. Can you trust this dataset enough to act on the results?

Data Quality Summary Cards

Watch these fields.

1. Original Rows. Rows in the source file.
2. Final Clean Rows. Rows left after cleaning.
3. Duplicates Removed. Exact duplicate rows removed.
4. Rows Removed. Unique rows removed because core values were invalid or negative.
5. Invalid Dates. Rows removed because the app could not parse the dates.
6. Invalid or Missing Revenue. Rows removed because revenue was missing or nonnumeric.
7. Negative Revenue Removed. Rows removed because revenue was below zero.

When you provide a transactions column, you also see these fields.

1. Invalid Transactions Set to 0.
2. Negative Transactions Set to 0.

Use these tips.

1. A few removed rows are normal in messy business data.
2. Explain data quality before forecasts when the dashboard removes many rows.
3. Check transaction corrections because they affect average order value.

Missing Values Table

This table counts missing cells by original column.

Use it to find weak parts of the dataset. Missing values in descriptive columns may be acceptable. Missing values in revenue or date columns are more serious.

Cleaned Data Preview

This table shows the rows left after cleaning.

Use it to confirm these things.

1. Dates are valid.
2. Revenue is numeric.
3. Negative revenue rows are gone.
4. Corrected transaction values look reasonable.

Filtered Data Preview

This table shows the final subset after sidebar filters.

Inspect this table first when charts or KPIs surprise you.

## Forecasting Tab

The Forecasting tab compares models and shows one selected model in detail.

Business question it answers. What should you expect next, and how uncertain is the forecast?

Forecasting Controls

Use these controls.

1. Models to evaluate. Choose which models to run.
2. Detailed model view. Pick the model you want to inspect in charts and tables.
3. Future horizon. Choose how many future periods to forecast.
4. Confidence level. Set the width of uncertainty bands for supported models.
5. Segment comparison. Compare future forecasts across top segments when needed.
6. Moving average window. Choose how many recent periods the Moving Average model uses.
7. Use trend. Tell Exponential Smoothing to model a steady rise or fall.
8. Use seasonality. Tell Exponential Smoothing to model repeating cycles.

Model Comparison Table

This table gives you the main forecasting summary.

Key fields.

1. MAE. Average absolute error. Lower is better.
2. MAPE. Average percentage error. Lower is better.
3. test periods. Number of historical periods used for evaluation.
4. future periods. Number of future periods in the forecast.
5. warnings. Problems or limits that affected the model.

Use these tips.

1. Compare MAE first.
2. Use MAPE for relative error, but watch out when actual values are small.
3. Read model warnings before you trust the forecast. A model can still run and still need careful interpretation.

Forecast Chart

This chart shows actual history, test predictions, and future forecasts together.

Read it this way.

1. Historical line means known actual revenue.
2. Test forecast shows how the model performed on held out history.
3. Future forecast shows projected unknown periods.
4. Interval bands show the forecast range.

Use it to check whether the model follows real behavior, whether it predicts too high or too low, and how wide the future range is.

Test Forecast Table

Use this table when you need exact comparisons between actual and predicted values.

Inspect these things.

1. Dates with the largest errors.
2. Patterns where the model underpredicts or overpredicts.
3. Whether the interval included the actual value.

Future Forecast Table

This table gives you the forecast you can act on.

Use it to answer questions like these.

1. What revenue range should you expect next week?
2. Which future periods look strongest or weakest?
3. How uncertain is the forecast?

This table works well in a live demo because it turns model evaluation into a planning discussion.

Model Coefficients

This section appears for Linear Regression.

Read it this way.

1. A positive coefficient means the feature tends to increase predicted revenue in that model.
2. A negative coefficient means the feature tends to decrease predicted revenue in that model.
3. A larger absolute value means a stronger directional effect inside that model.

Use coefficients for explanation. Discuss them carefully because they do not prove cause and effect.

Segment Comparison

This section compares forecasts across top segments, such as stores or categories.

Use it to answer these questions.

1. Which segment should generate the most revenue?
2. Which segment looks weaker?
3. Does model accuracy change by segment?

## Anomaly Detection Tab

This tab highlights unusual periods.

Business question it answers. Which periods need explanation before you make a business decision?

Controls

Use these controls.

1. Rolling window. Choose how many previous periods define normal behavior.
2. Anomaly threshold. Choose how extreme the z score must be before the dashboard flags a point.

Use these tips.

1. A lower threshold flags more anomalies.
2. A higher threshold flags fewer anomalies.
3. A shorter rolling window reacts more to short changes.
4. A longer rolling window gives you a smoother baseline.

Anomaly Chart

Read it this way.

1. The main line shows revenue.
2. Red markers show points that look unusual compared with recent history.

An anomaly does not always mean an error. It may come from a promotion, a holiday, a supply issue, a data problem, or a real business event.

Anomalous Rows Table

This table lists only flagged periods. Use it when you need exact dates and values for reporting.

Full Anomaly Results Table

This table includes rolling mean, rolling standard deviation, z score, and anomaly flag.

Use it when you need to explain why the dashboard flagged a point.

## Export Tab

Export buttons download results that match your current settings.

1. Download cleaned aggregated dataset. Downloads the cleaned and aggregated data used by the charts.
2. Download forecast results. Downloads forecast rows for the selected detailed model.
3. Download anomaly results. Downloads the anomaly output table.

Exports use the active filters and settings at the moment you click download. Check those settings first.

Practical Interpretation Workflow

Use this order for a clear workflow.

1. Confirm the dataset source and column mapping.
2. Check the raw preview.
3. Review the Data Quality tab.
4. Read the KPI cards in the Overview tab.
5. Inspect the trend and growth charts.
6. Compare segments when needed.
7. Open Forecasting, compare models, and show the future forecast table as the short term demand answer.
8. Turn the forecast into a clear action, such as inventory, staffing, or target planning.
9. Inspect the anomaly results.
10. Export results after you confirm filters and settings.

Common Mistakes to Avoid

1. Reading filtered results as if they represent the full dataset.
2. Comparing daily and monthly KPIs as if they mean the same thing.
3. Treating forecasts as exact promises.
4. Assuming anomalies are always data errors.
5. Ignoring data quality issues before you interpret forecasts.
6. Choosing a model because it sounds advanced instead of because it performs better.