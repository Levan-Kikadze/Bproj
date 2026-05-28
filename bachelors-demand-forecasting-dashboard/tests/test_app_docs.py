from app import DASHBOARD_GUIDE_PATH, PROJECT_ROOT, load_dashboard_guide_markdown


def test_dashboard_guide_file_exists_and_loads() -> None:
    assert DASHBOARD_GUIDE_PATH.exists()

    guide_markdown = load_dashboard_guide_markdown()

    assert "# Dashboard Help Guide" in guide_markdown
    assert "## Overview Tab" in guide_markdown
    assert "## Forecasting Tab" in guide_markdown
    assert "## Anomaly Detection Tab" in guide_markdown


def test_defense_and_reproducibility_docs_exist() -> None:
    expected_docs = {
        PROJECT_ROOT / "docs" / "reproducibility_snapshot.md": [
            "# Reproducibility Snapshot",
            "## Validated Environment",
            "## Validation Commands",
        ],
    }

    for path, required_sections in expected_docs.items():
        assert path.exists()

        content = path.read_text(encoding="utf-8")
        for required_section in required_sections:
            assert required_section in content


def test_validated_requirements_snapshot_exists() -> None:
    requirements_snapshot = PROJECT_ROOT / "requirements-validated.txt"

    assert requirements_snapshot.exists()

    content = requirements_snapshot.read_text(encoding="utf-8")
    assert "streamlit==1.57.0" in content
    assert "pytest==9.0.3" in content