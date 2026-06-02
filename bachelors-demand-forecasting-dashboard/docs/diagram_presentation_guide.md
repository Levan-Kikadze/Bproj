# UML Diagram Reading and Presentation Guide

This guide explains how to read each diagram and how to present it during the bachelor defense.

## 1. Component Diagram

Diagram file:
- docs/assets/uml_diagrams/component_diagram.svg

How to read it:
1. Start from the left: SME analyst and browser represent user entry points.
2. Move to the center: app.py is the orchestration layer, not the business logic owner.
3. Read the module cluster: each src module has one clear responsibility.
4. Follow arrows between modules to explain dependency direction.
5. End at the right side and bottom: visual outputs and CSV exports.

How to present it in defense:
- Say this diagram proves modular architecture and separation of concerns.
- Emphasize that app.py coordinates, while domain logic is isolated in src modules.
- Mention testability: isolated modules are easier to test and debug.

Suggested speaking script (40-60 seconds):
"This component diagram shows a layered architecture. The user interacts with the Streamlit interface in app.py. The app delegates all core work to dedicated modules: preprocessing for data quality, forecasting for model evaluation, anomaly detection for outlier discovery, and visualization for reporting. This design keeps responsibilities separated and makes the system maintainable and testable."

## 2. Deployment Diagram

Diagram file:
- docs/assets/uml_diagrams/deployment_diagram.svg

How to read it:
1. Read the outer boundary first: all execution is on one local machine.
2. Read the runtime box: Streamlit process plus Python analytics modules.
3. Track data flow: local CSV input to analytics runtime to local CSV export.

How to present it in defense:
- Say the system is intentionally local-first for simplicity and privacy.
- Explain that no external database or cloud dependency is required.
- Highlight reproducibility: same runtime can be recreated from requirements.

Suggested speaking script (30-45 seconds):
"The deployment architecture is local by design. The user runs the Streamlit process inside a Python virtual environment, all analytics modules execute locally, and both input and export files stay on the same machine. This supports privacy, ease of setup, and reproducibility for SME use and academic evaluation."

## 3. Sequence Diagram

Diagram file:
- docs/assets/uml_diagrams/sequence_diagram.svg

How to read it:
1. Read top-to-bottom: execution order over time.
2. Point out the alt branch: upload CSV vs use bundled sample.
3. Continue with processing sequence: preprocessing, forecasting, anomaly detection, visualization.
4. End with export interaction and file delivery.

How to present it in defense:
- Use it to explain end-to-end workflow in one pass.
- Show that the flow is deterministic and easy to reason about.
- Link each major call to the corresponding module responsibility.

Suggested speaking script (45-70 seconds):
"This sequence diagram captures the runtime workflow. After the user opens the app, there are two entry paths: upload a CSV or select sample data. The app then performs cleaning and aggregation, runs forecasting models, executes anomaly detection, and finally renders charts and KPIs. If the user requests an export, the app generates CSV outputs and returns them for download."

## 4. Slide Strategy for Defense

Recommended order:
1. Deployment diagram first: where system runs.
2. Component diagram second: how system is structured.
3. Sequence diagram third: how one user request is executed.

Timing recommendation:
- Deployment: 30-45 seconds
- Component: 40-60 seconds
- Sequence: 45-70 seconds
- Total UML section: around 2.5 to 3 minutes

## 5. Q&A Readiness Prompts

Prepare answers for these likely questions:
1. Why is app.py orchestrator-only instead of storing business logic there?
2. Why do you run local-only deployment instead of cloud deployment?
3. How does this architecture improve testing and maintainability?
4. Which module would you change first if new business features are requested?

## 6. Regenerating Diagram Files

Run this command in the project root:

```bash
python render_uml.py
```

The script reads .mmd sources and regenerates both .svg and .png versions in docs/assets/uml_diagrams.
