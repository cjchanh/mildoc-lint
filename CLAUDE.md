# mildoc-lint — Guide for AI Coding Agents

This file orients automated coding agents and new contributors working in this
repository. `CLAUDE.md` and `AGENTS.md` are byte-for-byte mirrors for cross-tool
compatibility — edit both together. On any conflict, `README.md`,
`CONTRIBUTING.md`, `SECURITY.md`, `THREAT_MODEL.md`, and
`docs/PUBLIC_BOUNDARY.md` are authoritative.

## Folder Purpose

`mildoc-lint` — deterministic, local-first document assurance linter for defense-adjacent administrative records. Catches structural failures in CUI markings, PII indicators, USMC O-SMEAC orders, naval correspondence (SECNAV M-5216.5 surface checks), and NAMP/CSEC readiness records. Python 3.10+, Apache 2.0.

## Module Boundaries

- `src/cds_mildoc/rules/` — lint rule implementations: `cui/`, `pii/`, `osmeac/`, `naval/`, `namp/`. Each module is self-contained; rules may not import from other rule modules.
- `src/cds_mildoc/engine.py` — orchestration layer: profile expansion, document loading, rule dispatch, finding aggregation. The only module that imports from all rule modules.
- `src/cds_mildoc/cli.py` — argument parsing and subcommand dispatch. No lint logic. No document I/O beyond path resolution.
- `src/cds_mildoc/parsers.py` — document format parsers (txt, md, rst, docx, pdf via optional `pypdf`). Parser errors are surfaced, not swallowed.
- `src/cds_mildoc/reporters.py` — output formatters: text, JSON, SARIF 2.1.0. Deterministic: same input → same output.
- `src/cds_mildoc/models.py` — data models: `Document`, `Finding`, `LintResult`, `Severity`. No behavior; pure data.
- `src/cds_mildoc/templates.py` — document skeleton templates for `mildoc-lint new`.
- `src/cds_mildoc/references.py` — public authority references. Read-only; cited by rule modules.
- `src/cds_mildoc/archivist/` — local receipt and provenance ledger. Separate subsystem; no lint engine dependency.
- `tests/` — pytest suite.
- `docs/` — public documentation, boundary docs, claims map.
- `constraints/` — constraint definitions (format, domain rules).
- `examples/` — example documents for testing and demonstration.

## Local Invariants

- Zero network calls. The tool operates entirely on the local filesystem. No telemetry, no cloud, no model calls.
- The tool does NOT generate tactical plans, determine classification, or certify compliance. These denials are structural, not aspirational — they must remain true by design.
- Parser errors are surfaced as ERROR-severity findings, never silently skipped.
- SARIF output must conform to SARIF 2.1.0 schema. Non-conforming output is a bug.
- Profile aliases in `engine.py` `PROFILE_ALIASES` are the single source of truth for profile expansion. Adding a rule to a profile means updating the alias map.
- Document paths are the user's data. The tool never copies, transmits, or persists document content beyond the in-memory lint run.
- Rule modules must cite a public authority in `references.py` `AUTHORITIES` when claiming a standard (e.g., SECNAV M-5216.5, DoD CUI marking guidance). Rules without cited authorities are in-house heuristics and must be labeled as such.

## Security Surface

None for this folder. No `crypto/`, `auth/`, `gates/`, `licensing/`, or `keys/` subdirectories.

The tool has a `THREAT_MODEL.md` and `SECURITY.md`. These are documentation, not security-surface code. The PII detection rules (`src/cds_mildoc/rules/pii/`) are data-classification heuristics, not security mechanisms.

## Voice Register

- Code & comments: clear and conventional; no cleverness for its own sake.
- Public docs (`README.md`, `docs/`, `INTENT.md`): professional register with explicit denial framing — the tool says what it does NOT do as prominently as what it does.
- `THREAT_MODEL.md`, `SECURITY.md`: formal security-documentation register.
- No marketing register. Avoid promotional adjectives and unverifiable superlatives. Every claim about the tool must be checkable against source code and public authorities.

## Verification Bar

Defense-adjacent document assurance tool with public claims about CUI, NAMP/CSEC, and naval correspondence standards. Every claim about what the tool checks, what standards it references, and what it explicitly does NOT do must be verifiable from source code and public authorities. Self-reported health is not evidence — verify via `python -m pytest tests/`.

## Review Dimensions

Primary focus areas for code review:
- `error_paths` — parser failures, unsupported formats, missing files, invalid profiles must surface clear diagnostics. Silent skip on malformed input is a blocking finding.
- `edge_cases` — empty documents, binary files misidentified as text, Unicode handling in CUI banners, nested O-SMEAC detection in non-order documents, docx without text content.
- `readability_to_a_stranger` — lint messages must be actionable by a new user who knows the domain (military admin) but not the tool internals. Finding messages cite the specific rule and authority.
- `naming` — rule IDs must be stable and hierarchical (`cui.invalid_banner`, `pii.ssn`, `osmeac.missing_paragraph`). Rule ID changes break SARIF consumers.

## Local Fail-Closed Rules

- `mildoc-lint lint` with `--fail-on error` must exit non-zero on ERROR or BLOCKER findings. A zero exit code with ERROR findings is a bug.
- Unsupported file formats produce ERROR findings, not silent skips.
- The `archivist` subcommand (`ingest`, `diff`, `lint --receipt`) must verify hash chains before accepting state mutations.
- Document content must never leave the process memory. No temp files with document content on disk.

## Test Convention

- Framework: `pytest` (configured in `pyproject.toml`, `testpaths = ["tests"]`, `pythonpath = ["src"]`).
- Canonical command: `python -m pytest tests/ -q` (run from the repository root).
- Test documents live in `tests/data/` or `examples/`. Never use live user documents in tests.
- Regression test required for any fixed false-positive or false-negative in a lint rule.

## FAIL-CLOSED Markers

- FAIL-CLOSED: Any change to `PROFILE_ALIASES` in `engine.py` requires full rule-module test re-run.
- FAIL-CLOSED: Adding a new lint rule requires (1) public authority citation in `references.py` or explicit "in-house heuristic" label, (2) test coverage with positive and negative cases, (3) SARIF output validation.
- FAIL-CLOSED: `--fail-on` exit-code logic must be verified on every change to `reporters.py` or `cli.py`. A zero exit with ERROR findings is a shipped bug.
- FAIL-CLOSED: Network calls introduced into the codebase are a hard architectural violation. The tool is local-first by invariant.
