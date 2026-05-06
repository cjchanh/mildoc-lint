# AGENTS.md - mildoc-lint

## Project Identity

`mildoc-lint` is a local-first Python CLI for deterministic document-shape linting over synthetic defense-adjacent examples.

Current status: alpha public-release candidate at version 0.2.0.

## Build And Verification

Use the repository virtual environment when present.

```bash
./.venv/bin/python -m pip install -e '.[dev]'
./.venv/bin/python -m pytest -v
./.venv/bin/ruff check .
./.venv/bin/mildoc-lint --version
./.venv/bin/cds-mildoc --version
./.venv/bin/mildoc-lint lint examples --profile all
./.venv/bin/mildoc-lint lint examples --profile all --format json --out /tmp/mildoc-example.json
./.venv/bin/mildoc-lint lint examples --profile all --format sarif --out examples/mildoc-example.sarif
```

Expected lint smoke behavior: the example corpus intentionally emits findings and may exit nonzero unless the caller gates only on blocker severity.

## Public Release Constraints

- No network calls, telemetry, cloud APIs, or model calls in `src/cds_mildoc/`.
- No real CUI, PII, unit documents, maintenance records, customer data, controlled technical data, or operational details in fixtures, tests, docs, or examples.
- Built-in rules must remain deterministic and public-source backed.
- CUI rules check marking shape only; they do not determine whether information is actually CUI.
- NAMP/CSEC rules check record shape only; they do not encode non-public checklist content or certify readiness/compliance.
- O-SMEAC rules check structure only; they do not generate tactical plans or validate tactical soundness.
- SARIF and JSON output must not point at fake remotes or public URLs that do not exist.
- `cds-mildoc` may remain as a compatibility CLI alias, but public docs should prefer `mildoc-lint`.

## Public Private Boundary

Public repo scope:

- deterministic rule engine
- local CLI
- text, JSON, and SARIF output
- Archivist receipt schema and local ledger
- synthetic examples
- public-source references

Out of public repo scope:

- actual manual/NAMP corpus ingestion
- customer documents or unit packs
- procedure graphs and troubleshooting flows
- LLM/RAG assistants
- adapters for official systems of record
- RMF/CMMC packages
- signed/offline enterprise builds

## Completion Gate

A release-hardening change is not complete until tests, ruff, CLI smoke tests, SARIF validation, pollution checks, and git status review have all completed with no unresolved blocker.
