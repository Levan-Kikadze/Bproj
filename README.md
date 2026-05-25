# Bachelor Project Submission

## Project Title

AI-Driven Demand and Revenue Forecasting Dashboard for SMEs

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
- `bachelors-demand-forecasting-dashboard/docs/final_eval_rubric_mapping.md`: committee-rubric mapping and final-evaluation preparation notes.
- `bachelors-demand-forecasting-dashboard/docs/final_presentation_outline.md`: slide-by-slide defense structure, demo plan, and backup checklist.
- `bachelors-demand-forecasting-dashboard/README.md`: main technical and usage overview.
- `bachelors-demand-forecasting-dashboard/requirements-validated.txt`: frozen package snapshot matching the latest validated local environment.
- `bachelors-demand-forecasting-dashboard/docs/reproducibility_snapshot.md`: exact validated environment snapshot for the latest local verification.
- `bachelors-demand-forecasting-dashboard/docs/technical_documentation.md`: architecture, methodology, and implementation details.
- `bachelors-demand-forecasting-dashboard/docs/user_manual.md`: end-user instructions and demo flow.
- `bachelors-demand-forecasting-dashboard/docs/viva_cheat_sheet.md`: short-answer defense preparation notes and key numbers to memorize.
- `bachelors-demand-forecasting-dashboard/docs/submission_checklist.md`: step-by-step plan for maximizing marks, final QA, demo preparation, and viva preparation.

## What This Project Demonstrates

- Modular Python design with a clear separation between UI and business logic.
- Explainable time-series forecasting using Moving Average and Exponential Smoothing.
- Transparent preprocessing with explicit reporting of removed rows and normalized transaction values.
- Automated regression coverage for preprocessing, forecasting, and anomaly detection.
- User-facing analytical outputs suitable for a bachelor-project demonstration.