# NAMP / CSEC Notes

## Current scope (v0.1)

`mildoc-lint`'s NAMP profile is a **record-shape linter** for NAMP/CSEC-style discrepancy and readiness records. It checks that records contain the canonical fields:

- `Reference:` — the NAMP, CSEC, or local checklist reference
- `Discrepancy:` — an objective description of the issue
- `Owner:` or `OPR:` — work center / shop / responsible party
- `Corrective Action:` — root cause and corrective action
- `Due Date:` — `YYYY-MM-DD`
- `Status:` — Open / In Progress / Closed / Verified
- `Evidence:` — attachment, log, photo, or record identifier

Generate a starter record with:

```bash
mildoc-lint new namp-discrepancy
```

## What this does NOT do

- It does **not** include a CSEC checklist. There is no "30-item CY26Q2" or any other quarter encoded in this repo.
- It does **not** import from OOMA, NALCOMIS, DECKPLATE, or any CSEC system.
- It does **not** measure squadron readiness, unit-level compliance, or program audit posture.
- It does **not** replace official QA, MMQA, or maintenance review.
- It does **not** make any compliance claim against COMNAVAIRFORINST 4790.2.

## Roadmap

A future release may ingest a public-source CSEC checklist into a YAML rule pack and produce a per-item compliance report. That work is gated on:

1. A real, public-source checklist artifact being available for ingestion.
2. A signed rule-pack format (Phase 1 in [`../ROADMAP.md`](../ROADMAP.md)).
3. Tests that verify ingestion against the public source.

Until those gates are met, no checklist-based compliance claim will appear in this repo or in `mildoc-lint`'s output.

## Source

NAVAIR Naval Aviation Maintenance Program — public CSEC pages and the public CSEC Help Guide. See [`SOURCES.md`](SOURCES.md).
