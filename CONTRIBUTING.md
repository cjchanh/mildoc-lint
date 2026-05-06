# Contributing to mildoc-lint

Thanks for your interest. This repo is the public, open-source, deterministic core. The rules are simple. They keep it safe to publish and safe to depend on.

## What does NOT belong in this repo

Do not submit pull requests that contain or rely on any of the following:

- Real unit documents (orders, OPORDs, WARNORDs, FRAGORDs, PMCS records, maintenance records, training records, T&R artifacts).
- CUI of any category.
- PII of any kind: names, EDIPIs, SSNs, DODIDs, phone numbers, email addresses, dates of birth, passport numbers, financial accounts.
- Export-controlled technical data (ITAR, EAR, CTI).
- Customer documents, customer rule packs, customer SOPs.
- Non-public DoD checklists, including any CSEC/NAMP checklist content.
- Anything that would constitute a compliance certification claim.

## What DOES belong in this repo

- New deterministic rules backed by **public** DoD, USMC, Navy, or NIST references.
- Tests for every new rule (≥ 6 tests per rule, including ≥ 3 negative cases).
- Synthetic example fixtures.
- Documentation that matches the implemented behavior.

## How to add a rule

1. Open an issue describing the rule, the public source, and the rule's boundary (what it does NOT decide).
2. Add the rule to `src/cds_mildoc/rules/<profile>.py`.
3. Add the source authority to `src/cds_mildoc/references.py` with a public URL.
4. Add tests to `tests/test_linter.py` or a new test file.
5. Update `docs/<profile>-Compliance-Guide.md` with a per-rule entry.
6. Run `pytest`, `ruff check .`, and the smoke test. All must pass.
7. Open a pull request. The CI gate enforces the public-boundary rules in `tests/test_no_overclaim.py` and `tests/test_public_boundary.py`.

## Banned phrasing

The following phrases will fail the public-boundary test gate:

- "DoD approved"
- "DoD certified"
- "CMMC compliant" / "CMMC certified"
- "RMF ready" / "RMF certified"
- "NIST 800-171 certified"
- "certifies"
- "certified compliance"
- "official DoD" / "official Navy" / "official USMC"
- "full 30-item" / "CY26Q2 checklist"
- "classification review assistant"
- "AI writes orders"

If your contribution requires any of those framings, it does not belong in the open-source core.

## Examples

All committed examples must be obviously synthetic. Use placeholders like:

- `Synthetic Work Center`
- `synthetic@example.mil`
- `2026-05-15`
- `SYN-001`
- generic operational verbs and structures

Never copy from a real document.

## License

By contributing, you agree your contribution is licensed under Apache-2.0 (see `LICENSE`).
