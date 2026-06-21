from __future__ import annotations

from pathlib import Path

import pytest

from cds_mildoc.engine import lint_document
from cds_mildoc.models import Document, Severity
from cds_mildoc.packs import BUILTIN_PACK_FILES, RulePackError, load_builtin_rule_packs, load_rule_packs
from cds_mildoc.rules import namp, osmeac


EXPECTED_RULE_IDS = {
    "cui.di_missing_category",
    "cui.di_missing_controlled_by",
    "cui.di_missing_ldc_or_distribution",
    "cui.di_missing_poc",
    "cui.do_not_prefix_unclassified",
    "cui.inconsistent_portion_marking",
    "cui.invalid_banner",
    "cui.legacy_marking",
    "cui.missing_bottom_banner",
    "cui.missing_designation_indicator",
    "cui.missing_top_banner",
    "cui.portion_marking_recommended",
    "cui.possible_unmarked_category",
    "naval.label_order",
    "naval.missing_from",
    "naval.missing_subj",
    "naval.missing_to",
    "naval.subject_label_not_subj",
    "naval.subject_not_uppercase",
    "naval.subject_punctuation",
    "namp.due_date_not_parseable",
    "namp.record_shape_ok",
    "namp.reference_absent",
    "osmeac.execution_missing_common_subelements",
    "osmeac.fragord_missing_base_order",
    "osmeac.fragord_no_change_absent",
    "osmeac.mission_incomplete_heuristic",
    "osmeac.mission_too_long",
    "osmeac.orientation_absent",
    "osmeac.warnord_prep_time_missing",
    "osmeac.warnord_too_sparse",
    "pii.dob",
    "pii.edipi",
    "pii.financial",
    "pii.passport",
    "pii.ssn",
} | {f"osmeac.missing_{key}" for key in osmeac.SECTION_DISPLAY if key != "orientation"} | {
    f"namp.missing_{name}" for name in namp.FIELD_PATTERNS
}


def _overlay(path: Path, *, severity: str = "warn") -> Path:
    path.write_text(
        f"""- rule_id: pii.ssn
  severity: {severity}
  profile: pii
  source:
    title: "Unit Privacy Review SOP"
    url: "https://example.invalid/unit-privacy-review"
    retrieved_at_utc: "2026-06-20T00:00:00Z"
  testimony: "Unit overlay changes only local severity for exposed SSN review."
  fail_closed: true
""",
        encoding="utf-8",
    )
    return path


def test_builtin_rule_pack_files_are_declared() -> None:
    assert set(BUILTIN_PACK_FILES) == {"cui.yaml", "pii.yaml", "osmeac.yaml", "naval.yaml", "namp.yaml"}


def test_builtin_rule_packs_parse_and_have_required_schema() -> None:
    catalog = load_builtin_rule_packs()

    assert set(catalog.records) == EXPECTED_RULE_IDS
    assert catalog.rule_pack_hash
    assert catalog.source_set_hash
    for record in catalog.records.values():
        assert record.fail_closed is True
        assert record.source.title
        assert record.source.url
        assert record.source.retrieved_at_utc.endswith("Z")
        assert record.testimony


def test_rule_pack_hash_is_deterministic() -> None:
    first = load_builtin_rule_packs()
    second = load_builtin_rule_packs()

    assert first.rule_pack_hash == second.rule_pack_hash
    assert first.source_set_hash == second.source_set_hash


def test_engine_applies_pack_source_and_testimony() -> None:
    doc = Document(text="Marine: Synthetic Example SSN 123-45-6789\n", path="synthetic.txt")
    finding = next(f for f in lint_document(doc, profile="pii") if f.rule_id == "pii.ssn")
    record = load_builtin_rule_packs().require("pii.ssn")

    assert finding.severity == record.severity
    assert finding.source == record.source_text
    assert finding.testimony == record.testimony


def test_overlay_can_override_existing_rule_severity(tmp_path: Path) -> None:
    overlay = _overlay(tmp_path / "unit.yaml", severity="warn")
    doc = Document(text="Marine: Synthetic Example SSN 123-45-6789\n", path="synthetic.txt")

    finding = next(
        f for f in lint_document(doc, profile="pii", rule_packs=[overlay]) if f.rule_id == "pii.ssn"
    )

    assert finding.severity == Severity.WARN
    assert finding.testimony == "Unit overlay changes only local severity for exposed SSN review."


def test_overlay_changes_catalog_hash(tmp_path: Path) -> None:
    overlay = _overlay(tmp_path / "unit.yaml", severity="warn")

    assert load_rule_packs([overlay]).rule_pack_hash != load_builtin_rule_packs().rule_pack_hash


def test_malformed_overlay_rejected_fail_closed(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        """- rule_id: pii.ssn
  severity: warn
  profile: pii
""",
        encoding="utf-8",
    )

    with pytest.raises(RulePackError):
        load_rule_packs([bad])
