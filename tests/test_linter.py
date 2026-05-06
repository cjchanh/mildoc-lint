from cds_mildoc.engine import lint_document
from cds_mildoc.models import Document, Severity
from cds_mildoc.rules.pii import check as pii_check


def ids(findings):
    return {finding.rule_id for finding in findings}


def test_cui_invalid_banner_and_missing_di_line():
    doc = Document(
        text="""CUI//CTI

Synthetic content.
Controlled by: CDS/SYNTHETIC
CUI Category: CTI
POC: synthetic@example.invalid
""",
        path="synthetic.md",
    )
    findings = lint_document(doc, profile="cui")
    got = ids(findings)
    assert "cui.invalid_banner" in got
    assert "cui.di_missing_ldc_or_distribution" in got
    assert any(f.severity == Severity.ERROR for f in findings)


def test_pii_redacts_ssn():
    doc = Document(text="Marine: Synthetic Example SSN 123-45-6789\n", path="synthetic.txt")
    findings = pii_check(doc)
    assert any(f.rule_id == "pii.ssn" for f in findings)
    assert all("123-45-6789" not in (f.snippet or "") for f in findings)


def test_osmeac_missing_sections():
    doc = Document(text="OPORD 1\n\n1. Situation\nSynthetic.\n\n2. Mission\nTeam conducts training.\n", path="opord.md")
    findings = lint_document(doc, profile="osmeac")
    got = ids(findings)
    assert "osmeac.missing_execution" in got
    assert "osmeac.missing_admin_logistics" in got
    assert "osmeac.missing_command_signal" in got


def test_namp_good_record_shape_info_only():
    doc = Document(
        text="""NAMP/CSEC Discrepancy Record
Reference: COMNAVAIRFORINST 4790.2 synthetic checklist
Discrepancy: Synthetic record gap.
Owner/OPR: Synthetic Work Center
Corrective Action: Update process.
Due Date: 2026-05-15
Status: Open
Evidence: SYN-001
""",
        path="namp.md",
    )
    findings = lint_document(doc, profile="namp")
    assert "namp.record_shape_ok" in ids(findings)
    assert not any(f.severity >= Severity.ERROR for f in findings)


def test_naval_subject_and_order():
    doc = Document(
        text="""To: Commanding Officer
From: Training Officer
Subject: Bad subject.
""",
        path="letter.md",
    )
    findings = lint_document(doc, profile="naval")
    got = ids(findings)
    assert "naval.label_order" in got
    assert "naval.subject_label_not_subj" in got
    assert "naval.missing_subj" in got
