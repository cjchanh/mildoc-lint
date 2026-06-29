# mildoc-lint demo

One command runs the linter over a **synthetic** draft operations order, flags
three structural failures **each cited to a public authority**, and exits
non-zero (fail-closed / cite-or-refuse).

```bash
bash demo/run_demo.sh
```

No flags, no network, no install step. The script prefers this repository's
source (`src/`) and falls back to an installed `mildoc-lint`. A captured run is
in [`expected_output.txt`](expected_output.txt).

## What it flags (and the authority each finding cites)

| # | Finding (rule id) | Defect planted in the sample | Cited public authority |
|---|---|---|---|
| 1 | `cui.invalid_banner` | Banner reads `CUI//SP-CTI`; categories belong in the designation block, not the banner line | DoD CUI Markings Training Aid, 2024 |
| 2 | `osmeac.missing_command_signal` | The five-paragraph order omits the **Command and Signal** paragraph | USMC FGHT 1004, Introduction to the Operations Order |
| 3 | `pii.ssn` | An SSN sits in the point-of-contact line (shown **redacted** as `***-**-****`) | NIST SP 800-171 Rev. 3 |

The same run also flags a missing CUI designation-indicator block and missing
top/bottom CUI banners (DoD CUI marking guidance). **Every** finding -- ERROR and
INFO alike -- carries a `source:` line. Run `mildoc-lint rules` for the full
authority list.

## Cited vs heuristic

Every built-in rule either cites a public authority in
[`src/cds_mildoc/references.py`](../src/cds_mildoc/references.py) or is named as
an in-house heuristic -- the tool never dresses a heuristic up as a standard. The
three findings above are mechanical checks against published marking and
order-format standards. Rules whose ids end in `_heuristic` (e.g.
`osmeac.mission_incomplete_heuristic`) and `INFO`-level "recommended" notes are
derived judgment, labeled as such. `show_citations.py` prints the authority (or
heuristic label) for every finding from the JSON output.

## Fail-closed (cite-or-refuse)

- `mildoc-lint lint ... --fail-on error` (the default) **exits 1** because the
  sample carries ERROR findings -- a CI step or pre-commit hook blocks here.
- `mildoc-lint archivist gate ... --require-no-pii` returns a **BLOCKED**
  decision and **exits 1** because the document carries PII -- the explicit
  refusal.

`run_demo.sh` ends with a self-check that asserts the three findings are present
and cited, that the SSN is redacted and never appears raw, and that both exits
are non-zero. The script itself exits 0 only if every assertion holds.

## A note on O-SMEAC vs SECNAV M-5216.5

O-SMEAC / the five-paragraph order is a USMC operations-order format; the tool
cites **USMC FGHT 1004** for it. **SECNAV M-5216.5** is the Department of the Navy
*correspondence* manual -- a different domain, checked by the separate `naval`
profile, not the order-format `osmeac` rules. Each finding is cited to the
authority that actually governs it.

## Safety

Synthetic sample only. The SSN is the well-known placeholder `123-45-6789` and is
**redacted in all tool output**; the self-check asserts the raw value never
appears. Zero network, zero telemetry, zero model calls. Do not place real
orders, rosters, CUI, or PII in this directory.

## Files

| File | Purpose |
|---|---|
| `run_demo.sh` | the one command: lint, print citations, run the fail-closed gate, self-check |
| `sample_draft_opord.md` | synthetic draft OPORD with the three planted defects |
| `show_citations.py` | prints `rule id / severity / cited authority` from `--format json` |
| `expected_output.txt` | captured transcript of a passing run |
