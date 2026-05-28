# Bachelor Project Submission

## Project Title

ForeSightSeer: AI-Driven Demand and Revenue Forecasting Dashboard for SMEs

## Repository Overview

This repository contains a bachelor-project Streamlit application that helps small and medium-sized enterprises:

- clean uploaded sales CSV data,
- inspect data quality,
- track revenue KPIs,
- forecast future demand and revenue with interpretable methods,
- detect anomalous sales behavior,
- export cleaned data and analytical results.

The implementation is intentionally focused on explainability, reproducibility, and a clear evaluation story rather than on black-box modeling.

## Main Project Folder

The application and project documentation are in:

`bachelors-demand-forecasting-dashboard/`

## Quick Start

```bash
cd bachelors-demand-forecasting-dashboard
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

To run the automated tests:

```bash
cd bachelors-demand-forecasting-dashboard
source .venv/bin/activate
pytest
```

## Included Documentation

- `bachelors-demand-forecasting-dashboard/docs/bachelor_report.md`: aligned bachelor report draft based on the implemented system.
- `bachelors-demand-forecasting-dashboard/README.md`: main technical and usage overview.
- `bachelors-demand-forecasting-dashboard/requirements-validated.txt`: frozen package snapshot matching the latest validated local environment.
- `bachelors-demand-forecasting-dashboard/docs/reproducibility_snapshot.md`: exact validated environment snapshot for the latest local verification.
- `bachelors-demand-forecasting-dashboard/docs/technical_documentation.md`: architecture, methodology, and implementation details.
- `bachelors-demand-forecasting-dashboard/docs/user_manual.md`: end-user instructions for operating the dashboard.

## What This Project Demonstrates

- Modular Python design with a clear separation between UI and business logic.
- Explainable time-series forecasting using Moving Average and Exponential Smoothing.
- Transparent preprocessing with explicit reporting of removed rows and normalized transaction values.
- Automated regression coverage for preprocessing, forecasting, and anomaly detection.
- User-facing analytical outputs suitable for a bachelor-project demonstration.