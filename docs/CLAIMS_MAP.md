# Claims map

Every public claim in `mildoc-lint`'s README and docs maps to a verifiable artifact in this repo. If a claim does not have an evidence path here, it does not belong in our docs.

| Claim | Evidence |
|---|---|
| Local-first; no network calls | No `requests` / `httpx` / `urllib` import in any module under `src/cds_mildoc/`. Verify: `grep -RnE "^(from\|import) (requests\|httpx\|urllib\|aiohttp)" src/` returns nothing. Design note: [`THREAT_MODEL.md`](../THREAT_MODEL.md). |
| Synthetic examples only | [`examples/`](../examples/) contains only `bad_cui_order.md`, `good_training_opord.md`, `namp_discrepancy.md`, `naval_letter_bad.md`, plus generated SARIF. All fixtures use synthetic placeholders (`Synthetic Work Center`, `synthetic@example.invalid`, `SYN-001`). [`CONTRIBUTING.md`](../CONTRIBUTING.md) bans real data. |
| CLI entrypoint `mildoc-lint` | [`pyproject.toml`](../pyproject.toml) `[project.scripts]` declares `mildoc-lint = "cds_mildoc.cli:main"`. Smoke test: `tests/test_cli_entrypoints.py::test_parser_prog_name_is_mildoc_lint`. |
| `--version` reports `mildoc-lint 0.2.1` | [`src/cds_mildoc/cli.py`](../src/cds_mildoc/cli.py) `--version` action. Test: `tests/test_cli_entrypoints.py::test_version_string_reports_mildoc_lint`. |
| CUI checks | [`src/cds_mildoc/rules/cui.py`](../src/cds_mildoc/rules/cui.py) (~240 LOC). Doc: [`docs/CUI-Compliance-Guide.md`](CUI-Compliance-Guide.md). Test: `tests/test_linter.py::test_cui_invalid_banner_and_missing_di_line`. |
| PII checks | [`src/cds_mildoc/rules/pii.py`](../src/cds_mildoc/rules/pii.py). Test: `tests/test_linter.py::test_pii_redacts_ssn`. |
| O-SMEAC checks | [`src/cds_mildoc/rules/osmeac.py`](../src/cds_mildoc/rules/osmeac.py) (~232 LOC). Doc: [`docs/OSMEAC-Compliance-Guide.md`](OSMEAC-Compliance-Guide.md). Test: `tests/test_linter.py::test_osmeac_missing_sections`. |
| Naval correspondence checks | [`src/cds_mildoc/rules/naval.py`](../src/cds_mildoc/rules/naval.py). Test: `tests/test_linter.py::test_naval_subject_and_order`. |
| NAMP record-shape checks | [`src/cds_mildoc/rules/namp.py`](../src/cds_mildoc/rules/namp.py). Doc: [`docs/NAMP-CSEC-Notes.md`](NAMP-CSEC-Notes.md). Test: `tests/test_linter.py::test_namp_good_record_shape_info_only`. |
| SARIF output | [`src/cds_mildoc/reporters.py`](../src/cds_mildoc/reporters.py) `render_sarif`. Example: [`examples/mildoc-example.sarif`](../examples/mildoc-example.sarif). Schema-pinned to SARIF 2.1.0. |
| JSON output | `src/cds_mildoc/reporters.py` `render_json`. CLI `--format json`. |
| Public-source rule authorities | [`src/cds_mildoc/references.py`](../src/cds_mildoc/references.py) (10 entries). Doc: [`docs/SOURCES.md`](SOURCES.md). CLI: `mildoc-lint rules`. |
| Archivist receipts (deterministic, content-addressed) | [`src/cds_mildoc/archivist/`](../src/cds_mildoc/archivist/). Doc: [`docs/Archivist-Receipts.md`](Archivist-Receipts.md). Determinism test: `tests/test_archivist.py::test_receipt_hash_is_deterministic` and `::test_archivist_lint_is_deterministic`. |
| No compliance certification | README "What it is not" section. INTENT.md. Test: `tests/test_no_overclaim.py::test_no_banned_phrases_in_repo_markdown` blocks unsupported approval, compliance, readiness, and certification claim patterns. |
| No tactical-plan generation | README states "It does **not** generate tactical plans." Doc: [`docs/OSMEAC-Compliance-Guide.md`](OSMEAC-Compliance-Guide.md) "What it does not cover" section. Test: `tests/test_public_boundary.py::test_readme_contains_required_disclaimers`. |
| No classification review | README and [`docs/CUI-Compliance-Guide.md`](CUI-Compliance-Guide.md) explicitly state the linter does not decide whether content is actually CUI. |
| Open-core boundary | [`docs/PUBLIC_BOUNDARY.md`](PUBLIC_BOUNDARY.md). [`docs/OPEN_CORE.md`](OPEN_CORE.md). |
| Ten-rule public boundary tests | [`tests/test_no_overclaim.py`](../tests/test_no_overclaim.py) and [`tests/test_public_boundary.py`](../tests/test_public_boundary.py) enforce banned phrases and required disclaimers. |
| Apache-2.0 | [`LICENSE`](../LICENSE) and `pyproject.toml` `license = { text = "Apache-2.0" }`. |
