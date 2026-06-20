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

### v0.2.2 — developer experience (no rule changes)

- `lint` accepts multiple paths, so it runs as a pre-commit hook over the set of changed files
- pre-commit hook (`.pre-commit-hooks.yaml`), a local-first `Dockerfile`, and copy-paste GitHub Actions / pre-commit / Docker recipes in [`docs/INTEGRATIONS.md`](docs/INTEGRATIONS.md)
- mypy added to the dev gate and CI; ruff enforced in CI
- README badges and an audience table; a no-terminal [`docs/QUICKSTART.md`](docs/QUICKSTART.md)

**Status: shipped in v0.2.2.**

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

## Deferred/private layers

Private enterprise, model-assisted, customer-ingestion, and maintenance-assistant
work is intentionally outside the public `mildoc-lint` roadmap. This repository
stays focused on deterministic local linting, public-source rule metadata, stable
JSON/SARIF output, and Archivist receipts over synthetic examples.

### `cds-maintainer` (deferred indefinitely, separate product)

A field troubleshooting assistant — Lance Corporal-grade, model-backed, with
ingestion of public technical-manual references — is conceptually planned as a
**distinct product** named `cds-maintainer`. It is not part of `mildoc-lint`
and is not on this roadmap.

`cds-maintainer` would, if ever built:

- live in a separate repository
- be model-assisted (LLM-backed) and explicitly out of scope for the
  deterministic-only `mildoc-lint` core
- never share `mildoc-lint`'s deterministic-rule guarantees

Status: deferred indefinitely. No timeline. No design work in this repo. Listed
here only so the boundary stays explicit and the public scope of `mildoc-lint`
does not drift toward conversational/field-assistant features.
