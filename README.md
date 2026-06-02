# Bachelor Project Submission

## Project Title

ForeSightSeer: AI-Driven Demand and Revenue Forecasting Dashboard for SMEs

## Repository Overview

This repository contains a bachelor-project Streamlit app for small and medium-sized enterprises.

You can use it to:

* clean uploaded sales CSV data,
* check data quality,
* track revenue KPIs,
* forecast future demand and revenue with clear methods,
* detect unusual sales behavior,
* save named dashboards locally and reopen them later without uploading the CSV again,
* export cleaned data and analysis results.

The project focuses on explainability, reproducibility, and a clear evaluation story. It uses methods you can explain and test.

## Main Project Folder

You’ll find the application and project documentation here:

`bachelors-demand-forecasting-dashboard/`

## Quick Start

Run the app with these commands:

```bash
cd bachelors-demand-forecasting-dashboard
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Saved dashboards use a local SQLite file under `bachelors-demand-forecasting-dashboard/runtime/saved_dashboards.db`, so a deployment needs persistent disk if you want saved dashboards to survive restarts.

Run the automated tests with these commands:

```bash
cd bachelors-demand-forecasting-dashboard
source .venv/bin/activate
pytest
```

## Included Documentation

The project includes these files:

* `bachelors-demand-forecasting-dashboard/docs/bachelor_report.md`: bachelor report draft based on the implemented system.
* `bachelors-demand-forecasting-dashboard/README.md`: main technical and usage overview.
* `bachelors-demand-forecasting-dashboard/requirements-validated.txt`: frozen package snapshot from the latest validated local environment.
* `bachelors-demand-forecasting-dashboard/docs/reproducibility_snapshot.md`: exact environment snapshot from the latest local verification.
* `bachelors-demand-forecasting-dashboard/docs/technical_documentation.md`: architecture, methodology, and implementation details.
* `bachelors-demand-forecasting-dashboard/docs/user_manual.md`: user instructions for operating the dashboard.

## What This Project Shows

This project shows that you can build a practical analytical dashboard with:

* modular Python code that separates the UI from business logic,
* explainable time-series forecasting with Moving Average and Exponential Smoothing,
* clear preprocessing that reports removed rows and normalized transaction values,
* automated regression tests for preprocessing, forecasting, and anomaly detection,
* user-facing analytical outputs that support a bachelor-project demo.
