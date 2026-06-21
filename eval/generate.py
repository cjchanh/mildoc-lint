#!/usr/bin/env python3
"""Metamorphic stress-tester for mildoc-lint.

Scales validation past the hand-labeled corpus. The idea: start from a
verified-clean base document, inject exactly one known defect (so the expected
finding is known by construction), then reformat the result many ways. Two
properties must hold for every generated document:

  recall      — the injected defect's rule_id fires.
  no-noise    — because the base was clean, NOTHING fires except the injected
                defect (and INFO advisories, which are ignored).

Reformatting the same defect many ways (extra blank lines, indentation, CRLF,
tabs, trailing whitespace) directly stresses the regex/line parsing: a variant
that drops an expected finding is a robustness failure.

Run from the repo root:

    python3 eval/generate.py            # ~default scale
    python3 eval/generate.py --count 5000
    python3 eval/generate.py --json

No network. Deterministic for a given --count and --seed.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from cds_mildoc.engine import lint_document  # noqa: E402
from cds_mildoc.models import Document  # noqa: E402

CORPUS = ROOT / "eval" / "corpus"
SCORED = {"error", "warn", "blocker"}

CUI_BASES = ["good_cui_opord", "good_cui_portions", "itar_marked_cui"]
ORDER_BASES = ["good_cui_opord", "good_order_orientation", "order_alias_service_support", "good_warnord"]
NAVAL_BASES = ["good_naval_letter", "good_naval_full"]
NAMP_BASES = ["good_namp_record", "good_namp_ooma"]
# Banner-removal needs a doc long enough that the top-6 and bottom-6 line windows
# do not overlap; on a short doc one remaining CUI banner satisfies both (correct
# behavior, but it makes the single-defect label invalid).
LONG_CUI_BASES = ["good_cui_opord", "good_cui_portions"]
# Injecting an unmarked SSN line into a portion-marked doc also (correctly) trips
# inconsistent_portion_marking; keep the single-defect injection off those bases.
NON_PORTIONED_BASES = ["good_cui_opord", "good_order_orientation", "order_alias_service_support",
                       "good_warnord", "good_naval_letter", "good_naval_full",
                       "good_namp_record", "good_namp_ooma"]


def _drop_line(text: str, pattern: str) -> str:
    rx = re.compile(pattern, re.IGNORECASE)
    return "\n".join(ln for ln in text.split("\n") if not rx.search(ln))


def _replace_line(text: str, pattern: str, repl: str) -> str:
    rx = re.compile(pattern, re.IGNORECASE)
    out = []
    for ln in text.split("\n"):
        out.append(repl if rx.search(ln) else ln)
    return "\n".join(out)


# Each mutation: (name, applicable_bases, transform(text)->text, expected_rule_ids)
MUTATIONS = [
    ("inject_ssn", NON_PORTIONED_BASES, lambda t: t + "\nPoint of contact: SSgt Doe, SSN 123-45-6789.", {"pii.ssn"}),
    ("inject_fouo", None, lambda t: "FOUO\n" + t, {"cui.legacy_marking"}),
    ("bad_banner", CUI_BASES, lambda t: t + "\nCUI//CTI", {"cui.invalid_banner"}),
    ("remove_di", CUI_BASES, lambda t: _drop_line(t, r"^\s*(?:Controlled by|CUI Category|LDC|POC)\s*:"), {"cui.missing_designation_indicator"}),
    ("remove_top_cui", LONG_CUI_BASES, lambda t: _drop_cui_at(t, first=True), {"cui.missing_top_banner"}),
    ("remove_bottom_cui", LONG_CUI_BASES, lambda t: _drop_cui_at(t, first=False), {"cui.missing_bottom_banner"}),
    ("delete_command_signal", ORDER_BASES, lambda t: _drop_line(t, r"command\s+and\s+signal"), {"osmeac.missing_command_signal"}),
    # Bases whose Execution is a single line; deleting it leaves no orphan content
    # to be reabsorbed into Mission (which would inflate it to mission_too_long).
    ("delete_execution", ["good_order_orientation", "order_alias_service_support", "good_warnord"],
     lambda t: _drop_line(t, r"^\s*3\.?\s*Execution"), {"osmeac.missing_execution"}),
    ("vague_mission", ORDER_BASES, lambda t: _replace_line(t, r"^\s*2\.?\s*Mission", "2. Mission. Do the thing."), {"osmeac.mission_incomplete_heuristic"}),
    ("lowercase_subj", NAVAL_BASES, lambda t: _replace_line(t, r"^\s*Subj\s*:", "Subj: quarterly readiness summary"), {"naval.subject_not_uppercase"}),
    ("period_subj", NAVAL_BASES, lambda t: _replace_line(t, r"^\s*Subj\s*:", "Subj: ANNUAL READINESS SUMMARY."), {"naval.subject_punctuation"}),
    ("remove_subj", NAVAL_BASES, lambda t: _drop_line(t, r"^\s*Subj\s*:"), {"naval.missing_subj"}),
    ("remove_corrective", NAMP_BASES, lambda t: _drop_line(t, r"Corrective Action"), {"namp.missing_corrective_action"}),
    ("unparseable_date", NAMP_BASES, lambda t: _replace_line(t, r"^\s*Due", "Due / ECD: sometime next week"), {"namp.due_date_not_parseable"}),
]


def _drop_cui_at(text: str, first: bool) -> str:
    lines = text.split("\n")
    idxs = [i for i, ln in enumerate(lines) if ln.strip().upper() == "CUI"]
    if not idxs:
        return text
    target = idxs[0] if first else idxs[-1]
    return "\n".join(ln for i, ln in enumerate(lines) if i != target)


# Formatting variants applied AFTER mutation; must not change the findings.
def _v_identity(t: str) -> str:
    return t


def _v_blank_lines(t: str) -> str:
    return "\n\n".join(t.split("\n"))


def _v_trailing_ws(t: str) -> str:
    return "\n".join(ln + "   " for ln in t.split("\n"))


def _v_indent(t: str) -> str:
    return "\n".join("  " + ln if ln.strip() else ln for ln in t.split("\n"))


def _v_crlf(t: str) -> str:
    return t.replace("\n", "\r\n")


def _v_tabs(t: str) -> str:
    return "\n".join("\t" + ln if ln.strip() else ln for ln in t.split("\n"))


VARIANTS = [
    ("identity", _v_identity),
    ("blank_lines", _v_blank_lines),
    ("trailing_ws", _v_trailing_ws),
    ("indent", _v_indent),
    ("crlf", _v_crlf),
    ("tabs", _v_tabs),
]


def _rand_ws(t: str, rng: random.Random) -> str:
    """Seeded random whitespace perturbation to multiply variants to scale."""
    out = []
    for ln in t.split("\n"):
        pad = " " * rng.randint(0, 3)
        tail = " " * rng.randint(0, 3)
        out.append(pad + ln + tail if ln.strip() else ln)
    sep = "\r\n" if rng.random() < 0.3 else "\n"
    return sep.join(out)


def _fired(text: str) -> set[str]:
    doc = Document(path="<generated>", text=text)
    findings = lint_document(doc, profile="mildoc")
    return {f.rule_id for f in findings if str(f.severity).split(".")[-1].lower() in SCORED}


def generate(count: int, seed: int) -> dict:
    rng = random.Random(seed)
    base_text = {b: (CORPUS / f"{b}.md").read_text(encoding="utf-8").strip() for b in
                 set(CUI_BASES + ORDER_BASES + NAVAL_BASES + NAMP_BASES)}

    cases: list[tuple[str, str, frozenset, str]] = []  # (mutation, base, expected, variant)
    for mname, bases, _fn, expected in MUTATIONS:
        applicable = bases if bases is not None else list(base_text)
        for b in applicable:
            for vname, _vf in VARIANTS:
                cases.append((mname, b, frozenset(expected), vname))
    # Expand to the requested count with seeded random-whitespace variants.
    i = 0
    while len(cases) < count:
        mname, bases, _fn, expected = MUTATIONS[i % len(MUTATIONS)]
        applicable = bases if bases is not None else list(base_text)
        b = applicable[i % len(applicable)]
        cases.append((mname, b, frozenset(expected), f"rand#{i}"))
        i += 1
    cases = cases[:count]

    mut_by_name = {m[0]: m for m in MUTATIONS}
    var_by_name = {v[0]: v[1] for v in VARIANTS}

    total = 0
    recall_pass = 0
    noise_pass = 0
    robustness_failures: dict[str, int] = {}
    noise_examples: list[dict] = []

    for mname, b, expected, vname in cases:
        _, _, fn, _ = mut_by_name[mname]
        mutated = fn(base_text[b])
        if vname.startswith("rand#"):
            formatted = _rand_ws(mutated, rng)
        else:
            formatted = var_by_name[vname](mutated)
        fired = _fired(formatted)
        total += 1
        missing = expected - fired
        extra = fired - expected
        if not missing:
            recall_pass += 1
        else:
            key = f"{mname} x {vname}"
            robustness_failures[key] = robustness_failures.get(key, 0) + 1
        if not extra:
            noise_pass += 1
        elif len(noise_examples) < 10:
            noise_examples.append({"mutation": mname, "base": b, "variant": vname, "extra": sorted(extra)})

    return {
        "schema": "mildoc-stress/v1",
        "generated": total,
        "injection_recall": round(recall_pass / total, 4) if total else 1.0,
        "no_noise_rate": round(noise_pass / total, 4) if total else 1.0,
        "robustness_failures": dict(sorted(robustness_failures.items(), key=lambda kv: -kv[1])),
        "noise_examples": noise_examples,
        "mutations": len(MUTATIONS),
        "format_variants": len(VARIANTS),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=600)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    res = generate(args.count, args.seed)
    (ROOT / "eval" / "stress_results.json").write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(res, indent=2))
        return 0

    print(f"mildoc-lint metamorphic stress test — {res['generated']} generated documents")
    print(f"  ({res['mutations']} defect types x {res['format_variants']} format variants + random perturbations)\n")
    print(f"  injection recall (defect always detected): {res['injection_recall']:.4f}")
    print(f"  no-noise rate (no finding beyond the defect): {res['no_noise_rate']:.4f}\n")
    if res["robustness_failures"]:
        print("ROBUSTNESS FAILURES (defect dropped under reformatting):")
        for k, n in res["robustness_failures"].items():
            print(f"  {k}: {n}")
    else:
        print("No robustness failures: every injected defect fired under every format variant.")
    if res["noise_examples"]:
        print("\nNOISE EXAMPLES (unexpected finding on an otherwise-clean mutated doc):")
        for e in res["noise_examples"]:
            print(f"  {e['mutation']} on {e['base']} [{e['variant']}] -> {', '.join(e['extra'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
