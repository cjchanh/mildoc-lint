# Roadmap

## Phase 0: Open-core credibility

Deliver a boring, local, deterministic linter that is useful without a model.

- CUI marking checks
- PII indicators
- O-SMEAC structure checks
- naval correspondence surface checks
- NAMP/CSEC record-shape checks
- text/JSON/SARIF reports
- synthetic fixtures only

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
