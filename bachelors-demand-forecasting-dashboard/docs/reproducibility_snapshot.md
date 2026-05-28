# Reproducibility Snapshot

ForeSightSeer environment validation notes.

## Purpose

This file records the exact local environment used for the latest validated project snapshot. The main `requirements.txt` keeps minimum compatible versions, while this file captures the concrete versions used during the current validation pass.

## Validated Environment

- Validation date: 2026-05-25.
- Operating system: macOS.
- Python: 3.14.2.
- Streamlit: 1.57.0.
- pandas: 3.0.3.
- NumPy: 2.4.6.
- Plotly: 6.7.0.
- scikit-learn: 1.8.0.
- statsmodels: 0.14.6.
- pytest: 9.0.3.

## Validation Commands

Run these commands from the project directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
.venv/bin/pytest -q
.venv/bin/streamlit run app.py
```

## Notes

- `requirements.txt` intentionally uses minimum compatible versions so the project stays installable on more than one machine.
- This snapshot is the exact tested stack used for the latest local verification.
- If you want a fully frozen submission archive, generate a lock-style dependency export from this environment just before final packaging.