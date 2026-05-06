# mildoc-lint

**Local-first document assurance for defense-adjacent administrative, CUI, O-SMEAC, naval correspondence, and NAMP/CSEC readiness records.**

`mildoc-lint` is a deterministic linter that catches structural failures in military-style documents *before* they leave the local machine. It is the open-core wedge: rules engine first, model-assisted drafting later.

## What it is not

- It does **not** generate tactical plans.
- It does **not** certify CMMC, RMF, or NIST compliance.
- It does **not** replace OOMA, NALCOMIS, DECKPLATE, CSEC, official QA, classification review, legal review, or command approval.
- It does **not** determine whether information is actually CUI. That is a designating-authority decision.
- It does **not** call the network, a model, or any cloud service.

## Install

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

A pre-generated SARIF example lives at [`examples/cds-mildoc-example.sarif`](examples/cds-mildoc-example.sarif).

## Why this shape

DoD CUI marking guidance requires `CUI` markings and a designation indicator block on documents containing CUI; it specifically says not to add CUI categories or LDCs to banner lines. USMC O-SMEAC training material frames the five-paragraph order format as a standard that prevents omissions and supports ready reference. NAVAIR's public NAMP/CSEC material describes CSEC as checklist/audit support for programs mandated within COMNAVAIRFORINST 4790.2.

`mildoc-lint` encodes the deterministic, mechanical parts of those standards as rules. Each finding cites a public authority. Run `mildoc-lint rules` to print the full list.

See [`docs/CUI-Compliance-Guide.md`](docs/CUI-Compliance-Guide.md), [`docs/OSMEAC-Compliance-Guide.md`](docs/OSMEAC-Compliance-Guide.md), [`docs/NAMP-CSEC-Notes.md`](docs/NAMP-CSEC-Notes.md), and [`docs/SOURCES.md`](docs/SOURCES.md) for per-rule explanations and references.

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
- local LLM drafting adapter
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

## Roadmap

See [`ROADMAP.md`](ROADMAP.md). Rust core and WASM browser surface are roadmap items, not v0.1 implementation.

## License

Apache-2.0. See [`LICENSE`](LICENSE).
