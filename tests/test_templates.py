"""Tests validating presence and structure of research templates."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_adr_templates():
    adr_init = ROOT / "docs" / "decisions" / "0001-record-decisions.md"
    adr_tmpl = ROOT / "docs" / "decisions" / "_template.md"

    assert adr_init.exists(), "0001-record-decisions.md must exist"
    assert adr_tmpl.exists(), "ADR _template.md must exist"

    for path in (adr_init, adr_tmpl):
        text = path.read_text(encoding="utf-8")
        assert "Context" in text
        assert "Options Considered" in text
        assert "Decision" in text
        assert "Consequences" in text


def test_experiment_note_template():
    tmpl = ROOT / "experiments" / "_template.md"
    assert tmpl.exists(), "experiments/_template.md must exist"

    text = tmpl.read_text(encoding="utf-8")

    # Verify the five required fields exist in order
    idx_hypo = text.find("Hypothesis")
    idx_stop = text.find("Stop Rule")
    idx_conf = text.find("Config Hash")
    idx_res = text.find("Result")
    idx_dec = text.find("Decision")

    assert idx_hypo != -1, "Missing Hypothesis section"
    assert idx_stop != -1, "Missing Stop Rule section"
    assert idx_conf != -1, "Missing Config Hash section"
    assert idx_res != -1, "Missing Result section"
    assert idx_dec != -1, "Missing Decision section"

    assert idx_hypo < idx_stop < idx_conf < idx_res < idx_dec, (
        "Fields must appear in order: Hypothesis -> Stop Rule -> Config Hash -> Result -> Decision"
    )


def test_readme_references_templates():
    readme = ROOT / "README.md"
    assert readme.exists()
    text = readme.read_text(encoding="utf-8")
    assert "0001-record-decisions.md" in text or "docs/decisions" in text
    assert "experiments/_template.md" in text
