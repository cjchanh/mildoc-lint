# Rule Packs

`mildoc-lint` keeps built-in rule metadata in declarative YAML files under
`src/cds_mildoc/rule_packs/`. The Python rule modules still own detection
logic. Rule packs own the auditable metadata attached to findings.

The built-in packs are:

- `cui.yaml`
- `pii.yaml`
- `osmeac.yaml`
- `naval.yaml`
- `namp.yaml`

## Record Schema

Each record has exactly these fields:

```yaml
- rule_id: pii.ssn
  severity: error
  profile: pii
  source:
    title: "NIST SP 800-171 Rev. 3"
    url: "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-171r3.pdf"
    retrieved_at_utc: "2026-06-20T00:00:00Z"
  testimony: "One-line authority statement for this check."
  fail_closed: true
```

- `rule_id` is stable and hierarchical.
- `severity` is one of `info`, `warn`, `error`, or `blocker`.
- `profile` names the rule family that enables the record.
- `source` names the public authority used by the built-in rule.
- `testimony` is a one-line statement explaining the source relationship.
- `fail_closed` must be `true`; malformed packs are rejected.

The loader intentionally supports a small YAML subset: list items, mappings,
quoted strings, plain strings, and booleans. This keeps the runtime dependency
surface unchanged.

## Hash Contract

`src/cds_mildoc/packs.py` loads the built-in packs and computes:

- `rule_pack_hash`: SHA-256 over canonical sorted rule records.
- `source_set_hash`: SHA-256 over canonical unique source records.

The same pack content produces the same hashes. Reordering records does not
change the hash. Changing severity, source, testimony, or `fail_closed` does.

Archivist receipts use the same pack-backed hash path, so a receipt can show
which rule metadata set was active for a lint run.

## Overlays

Overlays are additional YAML files supplied at runtime:

```bash
mildoc-lint lint docs/example.md --profile pii --rule-pack unit-overlay.yaml
```

An overlay can override metadata for an existing `rule_id`, including severity,
or add metadata for a future/private rule. The open-core linter only fires rules
implemented in Python; a metadata-only overlay record does not create detection
logic by itself.

Malformed overlays fail closed. Missing required fields, duplicate `rule_id`s,
invalid severities, non-UTC retrieval timestamps, or `fail_closed: false` all
stop loading.

## Public/Private Boundary

Built-in packs in this repository must cite public authorities already listed
in `src/cds_mildoc/references.py`.

Customer, unit-specific, or non-public overlay content must stay outside this
repository. This repo ships the overlay mechanism, not private overlay content.

Rule packs do not change these product boundaries:

- The tool does not determine classification.
- The tool does not generate tactical plans.
- The tool does not replace human review.
- The tool does not copy, transmit, or persist document content beyond the lint
  run.
