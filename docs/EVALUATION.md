# Rule evaluation — precision and recall

`mildoc-lint` ships a small evaluation harness so the rules' behavior is
*measured*, not asserted. It runs the linter over a labeled corpus of synthetic
documents and reports, per rule, how often it fires correctly versus how often
it over-fires or misses.

## What is measured

For each document, a reviewer records the ERROR/WARN findings that *should* fire
(`eval/labels.json`). The harness runs the linter and compares:

- **True positive** — an expected ERROR/WARN rule fired.
- **False positive** — a rule fired that the reviewer did not expect (noise).
- **False negative** — an expected rule did not fire (a miss).

INFO findings are advisory (for example, "no portion markings detected") and are
reported separately, not scored.

```text
overall precision = TP / (TP + FP)      # how much of what it flags is wanted
overall recall    = TP / (TP + FN)      # how much of what's wanted it flags
```

## Current results

Profile `mildoc`, 30 synthetic documents across the five rule families:
well-formed examples, seeded-defect examples, and precision probes (documents
that mention a domain term but should not be flagged):

| metric | value |
|---|---|
| precision | 0.973 |
| recall | 1.000 |
| true positives | 36 |
| false positives | 1 |
| false negatives | 0 |

Reproduce: `python3 eval/score.py` (writes `eval/results.json`).

### The one remaining false positive

`pii.ssn` fires on an SSN-shaped stock number (`123-45-6789`) in a supply
document. This is a deliberate high-recall choice: a PII check is more useful if
it flags an SSN-shaped value for a human to clear than if it stays silent and
misses a real one. It is recorded here so the trade-off is visible rather than
hidden.

### What the harness caught

The first run surfaced a real false-positive bug: when an order wrote its
mission or execution content on the same line as the section label
(`2. Mission. <statement>` — a common format), the section text was read as
empty, so the mission and execution heuristics fired even on well-formed orders.
The off-by-one in `osmeac._section_text` was fixed and pinned with a regression
test; precision over the first corpus moved from 0.840 to 0.955.

Expanding the corpus to 30 documents with precision probes per family surfaced
three more over-firing gates, each since tightened:

- `cui` context was established by the descriptive phrase "controlled
  unclassified information" in flowing prose, so a training bulletin *about* CUI
  drew "missing banner" errors. Context is now taken from CUI markings (a
  standalone or malformed CUI banner), not from prose.
- `namp` treated any two generic maintenance words (for example "maintenance"
  plus "quality assurance") as a maintenance record, so a break-room notice drew
  missing-field errors. A record-like signal (a discrepancy, finding, audit, or
  corrective action) is now also required.
- the mission heuristic flagged a FRAGORD whose mission read "No change" as
  incomplete; a deferred mission is no longer flagged.

Precision over the 30-document corpus is 0.973.

## Honest scope

These numbers are over a **synthetic, labeled corpus** authored alongside the
rules. They describe behavior on those examples; they are not a measurement of
real-world precision, and they are not a compliance or certification result.
Real documents — with their formatting variety — are the next input: the corpus
and `eval/labels.json` are designed so a new labeled document can be dropped in
and scored the same way.

## Extending the corpus

1. Add a document under `eval/corpus/`.
2. Add an entry to `eval/labels.json` with its `category` and the ERROR/WARN
   `expect` list a reviewer judges correct.
3. Run `python3 eval/score.py` and review any false positives or negatives.

The precision/recall floor is enforced in CI by `tests/test_eval_precision.py`.
