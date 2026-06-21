#!/usr/bin/env python3
"""Precision/recall harness for mildoc-lint rules.

Runs the linter over the labeled corpus in eval/corpus/, compares the ERROR/WARN
rule_ids it fires against the domain-truth labels in eval/labels.json, and
reports per-rule precision/recall plus every false positive (fired but not
expected) and false negative (expected but not fired). INFO findings are
advisory and reported separately, not scored.

Run from the repo root:

    python3 eval/score.py            # human report
    python3 eval/score.py --json     # machine receipt to stdout
    python3 eval/score.py --gate 0.85  # exit 1 if overall precision < 0.85

No network. Deterministic: same corpus + labels -> same numbers.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from cds_mildoc.engine import lint_path  # noqa: E402

SCORED = {"error", "warn", "blocker"}


def fired_rule_ids(doc_path: Path, profile: str) -> tuple[set[str], set[str]]:
    """Return (scored_rule_ids, info_rule_ids) for one document."""
    result = lint_path(str(doc_path), profile=profile)
    scored: set[str] = set()
    info: set[str] = set()
    for finding in result.findings:
        sev = str(finding.severity).split(".")[-1].lower()
        (scored if sev in SCORED else info).add(finding.rule_id)
    return scored, info


def evaluate(labels_path: Path) -> dict:
    spec = json.loads(labels_path.read_text(encoding="utf-8"))
    profile = spec.get("profile", "mildoc")
    corpus = labels_path.parent / "corpus"

    per_doc: list[dict] = []
    rule_tp: dict[str, int] = defaultdict(int)
    rule_fp: dict[str, int] = defaultdict(int)
    rule_fn: dict[str, int] = defaultdict(int)

    for name, meta in spec["docs"].items():
        doc_path = corpus / name
        if not doc_path.exists():
            raise SystemExit(f"missing corpus doc: {doc_path}")
        expected = set(meta.get("expect", []))
        scored, info = fired_rule_ids(doc_path, profile)
        tp = sorted(expected & scored)
        fp = sorted(scored - expected)
        fn = sorted(expected - scored)
        for r in tp:
            rule_tp[r] += 1
        for r in fp:
            rule_fp[r] += 1
        for r in fn:
            rule_fn[r] += 1
        per_doc.append(
            {
                "doc": name,
                "category": meta.get("category", "?"),
                "tp": tp,
                "false_positives": fp,
                "false_negatives": fn,
                "info_advisories": sorted(info),
            }
        )

    sum_tp = sum(rule_tp.values())
    sum_fp = sum(rule_fp.values())
    sum_fn = sum(rule_fn.values())
    precision = sum_tp / (sum_tp + sum_fp) if (sum_tp + sum_fp) else 1.0
    recall = sum_tp / (sum_tp + sum_fn) if (sum_tp + sum_fn) else 1.0

    rules = sorted(set(rule_tp) | set(rule_fp) | set(rule_fn))
    per_rule = []
    for r in rules:
        tp, fp, fn = rule_tp[r], rule_fp[r], rule_fn[r]
        per_rule.append(
            {
                "rule": r,
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "precision": round(tp / (tp + fp), 3) if (tp + fp) else None,
                "recall": round(tp / (tp + fn), 3) if (tp + fn) else None,
            }
        )

    return {
        "schema": "mildoc-eval-result/v1",
        "profile": profile,
        "docs_scored": len(per_doc),
        "overall": {
            "tp": sum_tp,
            "fp": sum_fp,
            "fn": sum_fn,
            "precision": round(precision, 3),
            "recall": round(recall, 3),
        },
        "per_rule": per_rule,
        "per_doc": per_doc,
    }


def print_report(res: dict) -> None:
    o = res["overall"]
    print(f"mildoc-lint precision/recall — profile '{res['profile']}', {res['docs_scored']} docs\n")
    print(f"  overall precision: {o['precision']:.3f}   recall: {o['recall']:.3f}   (TP={o['tp']} FP={o['fp']} FN={o['fn']})\n")

    fps = [(d["doc"], d["false_positives"]) for d in res["per_doc"] if d["false_positives"]]
    fns = [(d["doc"], d["false_negatives"]) for d in res["per_doc"] if d["false_negatives"]]
    if fps:
        print("FALSE POSITIVES (fired ERROR/WARN, not expected):")
        for doc, rules in fps:
            print(f"  {doc}: {', '.join(rules)}")
        print()
    if fns:
        print("FALSE NEGATIVES (expected, did not fire):")
        for doc, rules in fns:
            print(f"  {doc}: {', '.join(rules)}")
        print()
    if not fps and not fns:
        print("No false positives or false negatives against the labeled corpus.\n")

    print("per-rule (only rules with FP or FN shown):")
    for r in res["per_rule"]:
        if r["fp"] or r["fn"]:
            print(f"  {r['rule']:<42} tp={r['tp']} fp={r['fp']} fn={r['fn']} precision={r['precision']} recall={r['recall']}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true", help="emit the JSON receipt only")
    ap.add_argument("--gate", type=float, default=None, help="exit 1 if overall precision is below this")
    ap.add_argument("--labels", default=str(ROOT / "eval" / "labels.json"))
    args = ap.parse_args()

    res = evaluate(Path(args.labels))
    (ROOT / "eval" / "results.json").write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(res, indent=2))
    else:
        print_report(res)

    if args.gate is not None and res["overall"]["precision"] < args.gate:
        print(f"\nGATE FAIL: precision {res['overall']['precision']} < {args.gate}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
