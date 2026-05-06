# Security

## Data boundary

This tool is designed to run locally. The open-core implementation makes no network calls, emits no telemetry, and does not call external AI APIs.

Do not test with real operational records unless the host, account, storage location, and repository controls are authorized for that data.

## Sensitive-data policy

Do not submit or commit:

- CUI
- classified information
- ITAR/EAR technical data
- real orders
- unit movement details
- rosters
- SSNs, EDIPI, DOB, medical, personnel, or financial data
- OOMA/NALCOMIS/DECKPLATE exports
- CSEC data not cleared for redistribution

Use synthetic fixtures only.

## Threat model summary

Primary risks:

- accidental ingestion of sensitive operational documents
- false confidence in a linter result
- prompt-injection risk if a future model layer is attached
- parser exploitation from malformed DOCX/PDF
- leakage through CI logs or SARIF uploads

Built-in mitigations:

- local-only execution
- no network features
- redaction of obvious sensitive snippets
- optional PDF parser isolated behind extra dependency
- SARIF/JSON output for auditable CI gates

Future enterprise mitigations:

- signed rule packs
- deterministic builds and SBOM
- explicit no-cloud deployment mode
- allowlist-based file selection
- content hashing without storing raw text
- model sandbox if generation is added
