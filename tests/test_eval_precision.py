"""Precision/recall contract over the labeled eval corpus.

Runs the harness in eval/ and enforces a quality floor so a future rule change
that starts over-firing (precision regression) or missing real defects (recall
regression) fails CI. Also pins the specific off-by-one regression: order
content written on the section header line must not trip the mission/execution
heuristics.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "eval"))

from score import evaluate  # noqa: E402
from generate import generate  # noqa: E402

from cds_mildoc.engine import lint_path  # noqa: E402


def test_corpus_precision_and_recall_floor() -> None:
    res = evaluate(ROOT / "eval" / "labels.json")
    overall = res["overall"]
    # Recall is strict: the linter must catch every defect the corpus labels.
    assert overall["recall"] == 1.0, f"recall regressed: {overall}"
    # Precision floor guards against rules that start over-firing. Current
    # baseline is 0.955 (the only expected FP is the deliberately high-recall
    # pii.ssn on an SSN-shaped stock number).
    assert overall["precision"] >= 0.90, f"precision regressed: {overall}"


def test_mission_content_on_header_line_is_not_falsely_incomplete() -> None:
    """Regression: '2. Mission. <complete statement>' on one line must be read."""
    res = lint_path(str(ROOT / "eval" / "corpus" / "good_cui_opord.md"), profile="mildoc")
    fired = {f.rule_id for f in res.findings}
    assert "osmeac.mission_incomplete_heuristic" not in fired
    assert "osmeac.execution_missing_common_subelements" not in fired


def test_metamorphic_robustness_under_reformatting() -> None:
    """An injected defect must be detected under every formatting variant, with no
    finding beyond the injected defect (the bases are clean)."""
    res = generate(count=300, seed=1)
    assert res["injection_recall"] == 1.0, res["robustness_failures"]
    assert res["no_noise_rate"] == 1.0, res["noise_examples"]
    # Reformatting a clean document (including hard word-wrap and bullet numbering)
    # must not introduce findings.
    assert res["clean_preservation_rate"] == 1.0, res["clean_failures"]
