# Archivist receipts

The Archivist is `mildoc-lint`'s local receipt and provenance ledger. Every lint run can produce a deterministic, content-addressed receipt that records what was checked, against what rule pack, by what tool version, with what sources, and what the decision was.

This is **not** a compliance certification. It is a local document-assurance ledger.

## What a receipt is

A receipt is a JSON manifest with the schema `mildoc.receipt.v1`:

```json
{
  "schema": "mildoc.receipt.v1",
  "tool": "mildoc-lint",
  "version": "0.2.0",
  "profile": "osmeac",
  "document_sha256": "ab9dff855d69de210620ff…",
  "rule_pack_sha256": "f557527e18580b9a7d2467…",
  "source_set_sha256": "08c1f3e2…",
  "findings_sha256": "9d3c0f1e…",
  "decision": "PASS",
  "parent_receipt_sha256": null,
  "created_at_utc": "2026-05-06T00:39:29Z",
  "receipt_sha256": "a02f8f8d11eab03cf27bed03…"
}
```

The `receipt_sha256` is computed over a canonical JSON serialization (sorted keys, no whitespace) of every field above. Identical inputs always produce identical receipts.

## What gets hashed

| Object | Hash |
|---|---|
| Document | `document_hash(text, path)` — normalized text + canonical JSON of the path |
| Section | `section_hash(heading, body)` |
| Claim | `claim_hash(text, location)` |
| Finding | `finding_hash(rule_id, message, evidence)` |
| Rule pack | `rule_pack_hash(rules, sources)` — joint hash of rule definitions and source authorities |
| Receipt | `receipt_hash(manifest)` — canonical JSON over every other field |

All hashing uses SHA-256, hex-encoded.

## Decisions

A receipt's `decision` is computed from findings and gate flags:

- `PASS` — no `error` or `blocker` findings, no fail-closed conditions hit.
- `WARN` — only `warn` or `info` findings.
- `FAIL` — at least one `error` finding, no `--require-pass`.
- `BLOCKED` — fail-closed condition hit (see below).

## Fail-closed conditions

The Archivist BLOCKS in these cases:

1. **Document changed since last PASS** — content-addressed integrity. If the document hash differs from the last passing receipt's, the new run starts BLOCKED.
2. **Rule pack changed since last PASS** — same idea, but for the rule definitions and authorities.
3. **`--require-pass` with `error` findings** — caller demands a clean lint.
4. **`--require-sources` with unsourced findings** — caller demands every finding cite a public authority.
5. **`--require-no-pii` with any `pii.*` finding** — caller demands the document be PII-clean.
6. **Missing CUI designation indicator block** on a CUI-context document.
7. **FRAGORD without base order reference**.
8. **NAMP record with `evidence:` reference but no actual evidence field**.

## Workflow

Initialize the local ledger (one-time per repo):

```bash
mildoc-lint archivist init
```

Lint a document and write a receipt:

```bash
mildoc-lint archivist lint docs/order.md --profile osmeac --write-receipt
```

Check the last receipt:

```bash
mildoc-lint archivist status docs/order.md
```

Gate a document for release (exit 1 on BLOCKED):

```bash
mildoc-lint archivist gate docs/order.md --require-pass --require-sources --require-no-pii
echo "exit code: $?"
```

Compare two documents' receipts:

```bash
mildoc-lint archivist diff docs/order-v1.md docs/order-v2.md
```

Override the database location:

```bash
mildoc-lint archivist init --db-path /path/to/custom.sqlite3
mildoc-lint archivist lint docs/order.md --profile mildoc --db-path /path/to/custom.sqlite3
```

## Storage layout

By default, the Archivist writes to `<cwd>/.mildoc/`:

```
.mildoc/
  archivist.sqlite3      # primary ledger
  receipts.ndjson        # append-only receipt log (one JSON object per line)
```

`.mildoc/` is in `.gitignore`. Receipts are local-only artifacts; do not commit them.

## What this is NOT

- ❌ Compliance certification of any kind. Not CMMC. Not RMF. Not NIST 800-171.
- ❌ Classification review. The receipt records the lint, not whether content is actually CUI.
- ❌ Replacement for QA, CSEC, official maintenance review, or command approval.
- ❌ Network-aware. No telemetry. No cloud calls. No model calls.
- ❌ A signed attestation. Receipts are local-trust only at v0.2. Signing is a future phase.

## Architectural inspiration (not conformance)

The receipt model borrows from:

- **W3C PROV-DM** — entities/activities/agents triple. Documents/sections/claims are entities, lint runs are activities, rule packs/tool versions are agents.
- **SLSA / in-toto attestations** — the "verify the chain, don't trust the producer" pattern.

`mildoc-lint` does not claim PROV or SLSA conformance. These are listed as design inspiration only.
