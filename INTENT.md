# INTENT

`mildoc-lint` is an Apache-2.0, open-source, local-first document-assurance linter for defense-adjacent administrative, CUI, O-SMEAC, naval correspondence, and NAMP/CSEC readiness records.

It exists to catch mechanical, structural failures in military-style documents before those documents leave the local machine.

## What this project is

- An open-source tool, licensed under Apache-2.0.
- Local-first: no telemetry, no network calls, no cloud APIs, no model calls.
- Synthetic examples only. The repo ships no real unit data, no real names, no real markings, no real PII, no CUI, and no operational details.
- Source-backed: every built-in rule cites a public DoD, USMC, Navy, or NIST reference. Citations are public references for deterministic rule logic, not a certification basis.

## What this project is not

- Not affiliated with the U.S. Department of Defense, the U.S. Navy, the U.S. Marine Corps, or any U.S. Government program office, and not endorsed by them.
- Not a compliance certification of any kind. Not CMMC. Not RMF. Not NIST 800-171.
- Not a classification review tool. The linter records marking shape; it does not decide whether content is actually CUI.
- Not a replacement for QA, CSEC, MMQA, official maintenance review, legal review, or command approval.
- Not a tactical-plan generator. It does not author orders.
- Not affiliated with NAVAIR, COMNAVAIRFORINST 4790.2, or any DoD program office.

## License

Apache-2.0. See [`LICENSE`](LICENSE).
