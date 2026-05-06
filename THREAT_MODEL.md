# Threat Model

## System purpose

CDS MilDoc Linter performs static analysis over local document files and emits findings. It does not classify, approve, transmit, submit, or store official records.

## Assets

- local documents being scanned
- findings that may contain snippets from scanned documents
- rule packs
- CI artifacts such as SARIF/JSON
- future enterprise adapters

## Trust boundaries

1. User-controlled document input.
2. Local parser and rule engine.
3. Output files and CI logs.
4. Optional future closed-source adapters.

## Adversary goals

- cause sensitive text to be emitted into logs
- exploit parser behavior with malformed documents
- bypass lint findings through malformed labels or Unicode confusables
- poison rule packs
- induce future AI layer to call unauthorized tools

## Current controls

- no network access in core logic
- no external model calls
- no telemetry
- stdlib DOCX text extraction
- parser errors become findings, not silent passes
- obvious PII snippets are redacted
- rule authorities are embedded as public URLs

## Known limits

- DOCX pagination cannot be faithfully reproduced without a layout engine.
- PDF text extraction requires optional dependency and cannot guarantee layout correctness.
- CUI determination is authority-dependent; this tool only detects marking and content indicators.
- O-SMEAC checks are structural heuristics, not tactical adequacy checks.
- NAMP/CSEC checks validate record shape, not official system-of-record state.

## Closed-core controls before enterprise use

- signed and versioned rule packs
- update provenance
- SBOM and reproducible builds
- file allowlists and maximum file-size gates
- structured audit logs with content minimization
- offline package mirrors
- fuzzing for DOCX/PDF parsers
