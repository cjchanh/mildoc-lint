# Open-core split

`mildoc-lint` is the open-core wedge of a larger document-assurance stack. This document spells out what is open, what is intentionally not, and where the boundary sits.

## Open-core (this repo, Apache-2.0)

- Deterministic rule engine
- Local CLI (`mildoc-lint`)
- CUI marking and PII shape checks
- O-SMEAC training-grade structure checks
- Naval correspondence surface checks
- NAMP/CSEC record-shape checks
- JSON, text, and SARIF 2.1.0 output
- Synthetic example fixtures
- Public-source authority references
- CI workflow and SARIF GitHub Code Scanning integration

The open-core surface stays useful without any model, network call, or proprietary import.

## Closed / future enterprise

These are kept out of the open-core repo deliberately. They are the layer that produces revenue and the layer that touches non-public material.

- **Unit-specific rule packs** — wing/squadron/component-level rule packs that encode local conventions.
- **Local LLM drafting adapter** — a deterministic, offline drafting layer over local models (MoLA, MLX, Ollama) that helps populate skeletons without network calls. Behind a human approval gate.
- **NAMP/CSEC importers** — ingestion adapters for actual checklist data. Will only be authored if/when a real public-source checklist is available; until then no checklist content appears anywhere.
- **OOMA / NALCOMIS / DECKPLATE adapters** — read-only export bridges for records originating in official maintenance systems.
- **SharePoint / NMCI packaging** — installer/distribution for restricted networks.
- **Signed enterprise builds** — reproducible, signed, SBOM'd builds for offline enterprise environments.
- **RMF / CMMC deployment package** — deployment artifacts and documentation for assessing a rules-engine deployment under RMF or CMMC. The linter itself is not a CMMC or RMF certification.

## What stays out of both

These are not products. They are off-limits.

- Real CUI material in fixtures, examples, or tests.
- Real unit rosters, real maintenance records, real names.
- Operational details of any active mission.
- Classified information of any kind.

## Boundary signals

If a future contribution would require shipping any of the following inside this repo, route it to the closed enterprise layer instead:

- non-public DoD checklist content
- a customer's local rule pack
- a real document with real names or real markings (use synthetic fixtures)
- a model adapter that calls a network model
- compliance-certification language

The open-core repo stays boring, deterministic, and Tuesday-stable.
