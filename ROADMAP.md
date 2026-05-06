# Roadmap

## Phase 0: Open-core credibility (v0.1)

Deliver a boring, local, deterministic linter that is useful without a model.

- CUI marking checks
- PII indicators
- O-SMEAC structure checks
- naval correspondence surface checks
- NAMP/CSEC record-shape checks
- text/JSON/SARIF reports
- synthetic fixtures only

**Status: shipped in v0.1.0.**

## Phase 0.5: Archivist receipt engine (v0.2)

Add a local SQLite-backed receipt and provenance ledger. Every lint run produces a deterministic, content-addressed receipt that can be chained, verified, and gated against. Fail-closed by design.

- SHA-256 hashing of documents, sections, claims, findings, rule packs, receipts
- SQLite ledger with PROV-shaped schema (documents/sections/claims/sources/rule_packs/findings/activities/receipts)
- `mildoc.receipt.v1` manifest schema
- 8 fail-closed gate conditions
- New `archivist` subcommand tree (`init`, `ingest`, `lint`, `status`, `gate`, `diff`)
- See [`docs/Archivist-Receipts.md`](docs/Archivist-Receipts.md)

**Status: shipped in v0.2.0.**

## Phase 1: Rule-pack engine

- signed JSON rule packs
- versioned authority mapping
- severity overrides
- local policy overlays
- rule test harness

## Phase 2: Workbench

- browser-local UI
- DOCX import/export improvements
- finding navigation
- report bundle export
- offline reference viewer for public docs

## Phase 3: Enterprise closed layer

- unit-specific rules
- NAMP/CSEC import/export adapters
- SharePoint packaging
- CMMC/RMF artifacts
- signed installer
- content-hash audit trail

## Phase 4: Model-assisted drafting

Only after deterministic rules are stable:

- local 7B/14B adapter for suggestions
- tool-calling locked behind schemas
- no direct submission authority
- human approval gate
- eval suite for hallucination, refusal, and tool misuse

## Future: cds-maintainer (separate product, deferred)

A field-grade, source-locked troubleshooting assistant for junior maintainers
working on technical equipment in austere conditions. The user story:
a Lance Corporal at 0200 with a non-starting generator should not have to
fight Ctrl+F across a 600-page PDF.

Scope sketch:
- ingestion of public/Distribution-Statement-A technical manuals
- procedure graph (symptom → equipment model → safety state → fault tree → next check → result → escalation)
- every step linked to a manual section and an Archivist receipt
- fail-closed: no source = no answer, escalate to supervisor
- enterprise: customer-authorized manual corpus, NAMP/CSEC integration, signed builds

This is **not** a `mildoc-lint` subcommand. It is a separate product
that will share the Archivist receipt model. It is not on the
`mildoc-lint` development critical path. Captured here so the architecture
stays consistent when the time comes.
