# mildoc-lint

[![CI](https://github.com/cjchanh/mildoc-lint/actions/workflows/ci.yml/badge.svg)](https://github.com/cjchanh/mildoc-lint/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)
[![Lint: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Network: zero calls](https://img.shields.io/badge/network-zero%20calls-2ea44f.svg)](THREAT_MODEL.md)

**Local-first document assurance for defense-adjacent administrative, CUI, O-SMEAC, naval correspondence, and NAMP/CSEC readiness records.**

`mildoc-lint` is a deterministic linter that catches structural failures in military-style documents *before* they leave the local machine.

## What it is not

In short: `mildoc-lint` does not generate tactical plans, does not certify compliance, does not determine classification, and does not call the network.

`mildoc-lint` does not:

- generate tactical plans
- determine classification
- determine whether information is actually CUI (that is a designating-authority decision)
- certify CMMC, RMF, NIST, or DoD compliance
- replace official review, QA, CSEC, command approval, or systems of record (OOMA, NALCOMIS, DECKPLATE)
- use network calls, telemetry, cloud APIs, or model calls

It is not affiliated with the U.S. Department of Defense, the U.S. Navy, the U.S. Marine Corps, NAVAIR, or any U.S. Government program office. See [`INTENT.md`](INTENT.md), [`docs/PUBLIC_BOUNDARY.md`](docs/PUBLIC_BOUNDARY.md), and [`docs/CLAIMS_MAP.md`](docs/CLAIMS_MAP.md).

## Who it's for

| If you… | mildoc-lint gives you |
|---|---|
| draft or review **CUI-marked** documents | deterministic banner, portion-marking, and designation-block shape checks before the file leaves your machine |
| write **O-SMEAC / OPORD / WARNORD / FRAGORD** orders | five-paragraph structure and execution sub-element checks |
| handle **naval correspondence** (SECNAV M-5216.5) | label-order and subject-line surface checks |
| maintain **NAMP / CSEC** readiness records | discrepancy and readiness record-shape checks |
| gate a **docs repo in CI** | SARIF 2.1.0 for GitHub code scanning and `--fail-on` exit codes |
| work **air-gapped or cleared** | zero network, zero telemetry, synthetic examples only, local provenance receipts |

New to the terminal? See [`docs/QUICKSTART.md`](docs/QUICKSTART.md). Adding it to CI or pre-commit? See [`docs/INTEGRATIONS.md`](docs/INTEGRATIONS.md).

## Install

For the full install matrix, see [`docs/INSTALL.md`](docs/INSTALL.md).

Install the CLI with `pipx`:

```bash
pipx install mildoc-lint
mildoc-lint --version
```

From source:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Optional PDF support:

```bash
pip install -e '.[pdf]'
```

## Run

```bash
mildoc-lint lint ./docs --profile mildoc
mildoc-lint lint ./docs --profile cui --format json
mildoc-lint lint ./docs --profile all --format sarif --out mildoc.sarif
mildoc-lint namp check ./maintenance-records
mildoc-lint new opord
mildoc-lint new warnord
mildoc-lint new fragord
mildoc-lint new cui-designation-block
mildoc-lint new namp-discrepancy
```

CI gate:

```bash
mildoc-lint lint ./docs --profile mildoc --format sarif --out mildoc.sarif --fail-on error
```

Ready-to-copy GitHub Actions, pre-commit, and Docker configs are in [`docs/INTEGRATIONS.md`](docs/INTEGRATIONS.md). `lint` accepts multiple paths, so it works as a pre-commit hook over changed files.

## Profiles

| Profile | Checks |
|---|---|
| `cui` | DoD CUI banner shape, designation indicator block, invalid banners, legacy markings (FOUO/SBU), portion-marking consistency, "do not prefix UNCLASSIFIED" rule, plus PII indicators |
| `pii` | SSN, EDIPI/DoD ID context, DOB, passport, financial-account indicators |
| `osmeac` | O-SMEAC five-paragraph structure, mission heuristics, execution subelements, OPORD/WARNORD/FRAGORD branching |
| `naval` | naval correspondence label order and subject-line shape (SECNAV M-5216.5 surface checks only) |
| `namp` | NAMP/CSEC discrepancy/readiness record shape: reference, discrepancy, owner, corrective action, due date, status, evidence |
| `mildoc` | auto-detecting combined profile: cui + pii + osmeac + naval + namp |
| `maildoc` | alias for cui + pii + naval correspondence framing |
| `all` | every rule, forced |

Supported input formats: `.txt`, `.md`, `.rst`, `.docx`. PDF supported when the optional `pypdf` dependency is installed.

Supported output formats: text, JSON, SARIF 2.1.0.

## Example output

```text
mildoc-lint: scanned 1 document(s), findings=6 blocker=0 error=4 warn=1 info=1

[ERROR] cui.invalid_banner @ examples/bad_cui_order.md:1:1
  Invalid or legacy CUI banner form detected.
  snippet: CUI//CTI
  fix: Use standalone "CUI" for the banner/footer. Put categories and dissemination controls in the designation indicator block.
```

A pre-generated SARIF example lives at [`examples/mildoc-example.sarif`](examples/mildoc-example.sarif).

## Why this shape

DoD CUI marking guidance requires `CUI` markings and a designation indicator block on documents containing CUI; it specifically says not to add CUI categories or LDCs to banner lines. USMC O-SMEAC training material frames the five-paragraph order format as a standard that prevents omissions and supports ready reference. NAVAIR's public NAMP/CSEC material describes CSEC as checklist/audit support for programs mandated within COMNAVAIRFORINST 4790.2.

`mildoc-lint` encodes the deterministic, mechanical parts of those standards as rules. Each finding cites a public authority. Run `mildoc-lint rules` to print the full list.

See [`docs/CUI-Compliance-Guide.md`](docs/CUI-Compliance-Guide.md), [`docs/OSMEAC-Compliance-Guide.md`](docs/OSMEAC-Compliance-Guide.md), [`docs/NAMP-CSEC-Notes.md`](docs/NAMP-CSEC-Notes.md), and [`docs/SOURCES.md`](docs/SOURCES.md) for per-rule explanations and references.

## Archivist receipts

`mildoc-lint` v0.2 ships with an optional local **Archivist** ledger that produces a deterministic, content-addressed receipt for every lint run. Each receipt records what was checked, against what rule pack, by what tool version, and what the decision was. Receipts are SQLite-persisted and append-only on disk.

```bash
mildoc-lint archivist init
mildoc-lint archivist lint docs/order.md --profile osmeac --write-receipt
mildoc-lint archivist status docs/order.md
mildoc-lint archivist gate docs/order.md --require-pass --require-sources --require-no-pii
```

The ledger is local-only. `.mildoc/` is gitignored. The Archivist does not certify compliance, determine classification, or replace official review — see [`docs/Archivist-Receipts.md`](docs/Archivist-Receipts.md) for the full receipt schema, fail-closed conditions, and workflow.

## Open-core boundary

See [`docs/OPEN_CORE.md`](docs/OPEN_CORE.md) for the full split.

**Open (this repo, Apache-2.0):**
- deterministic rule engine
- local CLI
- CUI / PII / O-SMEAC / naval / NAMP shape checks
- JSON and SARIF output
- synthetic examples
- public-source authority references

**Closed / future enterprise:**
- unit-specific rule packs
- NAMP/CSEC importers
- OOMA / NALCOMIS / DECKPLATE adapters
- SharePoint / NMCI packaging
- signed enterprise builds
- RMF / CMMC deployment package and artifacts

## Safety and handling

The repo ships **synthetic examples only**. Do not commit real orders, unit rosters, maintenance records, CUI, export-controlled technical data, or operational details.

Default operation is local. There is no telemetry, no network call, no model call, and no cloud dependency.

## Development

```bash
pip install -e '.[dev]'
python -m pytest
mildoc-lint lint examples --profile all
```

Release-readiness checklist: [`docs/RELEASE_CHECKLIST.md`](docs/RELEASE_CHECKLIST.md).
Packaging notes: [`docs/PACKAGING.md`](docs/PACKAGING.md) and [`docs/RELEASE_ARTIFACTS.md`](docs/RELEASE_ARTIFACTS.md).

## Roadmap

See [`ROADMAP.md`](ROADMAP.md).

## License

Apache-2.0. See [`LICENSE`](LICENSE).
