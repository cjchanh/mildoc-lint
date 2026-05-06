# Public boundary

The line between what is in this repo and what is not.

## In this repo (public, Apache-2.0)

- Deterministic rule engine
- Local CLI (`mildoc-lint`)
- CUI marking shape checks
- PII shape checks
- O-SMEAC training-grade structure checks
- Naval correspondence surface checks
- NAMP/CSEC record-shape checks
- JSON, text, and SARIF 2.1.0 output
- Synthetic example fixtures
- Public-source authority references
- Local Archivist receipt ledger (SQLite, deterministic content-addressed receipts)
- Release checklist
- Threat model
- CI workflow with SARIF GitHub Code Scanning integration

## NOT in this repo (private, CDS enterprise / future)

These are deliberately kept out of the open-source core. They are the layer that touches non-public material or that requires customer agreements.

- Actual NAMP / technical-manual corpus ingestion
- Unit SOP ingestion
- Customer documents of any kind
- Maintenance procedure graphs
- LLM / RAG-backed assistant
- Source-ranking / retrieval-quality logic
- Fault-isolation state machines
- Unit-specific rule packs
- OOMA / NALCOMIS / DECKPLATE adapters
- SharePoint / NMCI packaging
- Signed / offline / airgap-deploy builds
- RMF / CMMC deployment packages
- Governor Console
- Enterprise Archivist / evidence vault
- Customer-specific workflows

## Why split this way

The open-source core exists to be inspectable, reproducible, and trustworthy as a substrate. Anything that requires non-public source material, customer authorization, or revenue capture lives in the private layer and is not part of this repo.

## What stays out of both

- Real CUI material.
- Real PII.
- Real unit rosters or maintenance records.
- Operational details of any active mission.
- Classified information of any kind.
