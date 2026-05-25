# Sample Data Guide

The `sample_data/` folder now contains several bundled CSV files so each dashboard feature can be demonstrated without editing the code or hunting for external data.

## Files

- `sample_sales_data.csv`: the large clean default dataset used for the main end-to-end dashboard demo.
- `sample_sales_data_quality_issues.csv`: intentionally includes duplicates, invalid dates, missing revenue, negative revenue, invalid transactions, negative transactions, and event columns, while still providing around two months of daily history.
- `sample_sales_data_event_features.csv`: includes holiday and promotion flags, multiple stores, and multiple categories for forecasting, coefficient, and segment-comparison demos across roughly one quarter of daily history.
- `sample_sales_data_anomalies.csv`: includes missing calendar periods, several strong spikes, and several sharp drops for anomaly-detection and missing-period forecasting demos across a much longer time range.

## Recommended Use

- Use `sample_sales_data.csv` for the overall project walkthrough.
- Use `sample_sales_data_quality_issues.csv` when presenting the Data Quality tab and still wanting a forecast slice that is large enough to read.
- Use `sample_sales_data_event_features.csv` when presenting Linear Regression, confidence intervals, or segment comparison.
- Use `sample_sales_data_anomalies.csv` when presenting anomaly detection or explaining why the forecasting module fills missing periods.

## Column Notes

- Required columns: `date`, `revenue`
- Optional columns used by the app: `transactions`, `product_category`, `store_id`, `product_id`, `holiday_flag`, `promotion_active`

The app sidebar now lets you choose between these bundled demo datasets whenever no external CSV is uploaded.