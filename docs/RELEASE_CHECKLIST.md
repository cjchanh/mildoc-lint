# Release Checklist

Run before any tag, release, or public-push action. Fail-closed: if any item fails, do not release.

## Code gates

- [ ] `pytest` passes
- [ ] `ruff check .` passes
- [ ] If `ruff` reports a pre-existing style issue that is intentional, document it separately in this checklist before release
- [ ] `mildoc-lint --version` returns `mildoc-lint 0.2.1`
- [ ] README commands are smoke-tested (run each shell snippet in the README's Run section)
- [ ] `mildoc-lint lint examples --profile all` runs and reports findings
- [ ] Example SARIF is generated: `mildoc-lint lint examples --profile all --format sarif --out examples/mildoc-example.sarif` writes a valid SARIF 2.1.0 file
- [ ] `mildoc-lint rules` lists every authority key
- [ ] No unsupported compliance claims in any tracked Markdown (enforced by `tests/test_no_overclaim.py` and `tests/test_public_boundary.py`)
- [ ] No real CUI, PII, unit documents, maintenance records, or controlled technical data in any tracked file

## Repo hygiene

- [ ] No `.DS_Store`, `__MACOSX/`, `*.egg-info/`, `dist/`, or `build/` tracked
- [ ] No real names, real units, real EDIPIs, real SSNs, real OPORDs, or real maintenance records anywhere in fixtures or docs
- [ ] No invented `.mil` contact information that could be mistaken for real
- [ ] No `Cargo.lock` / `target/` (this is a Python repo)

## Claim hygiene

The README and docs must not contain unsupported approval, compliance,
readiness, authority, completeness, or roadmap assertions. The exact denylist is
held in the public-boundary tests so release docs do not repeat claim text.

The static check `tests/test_no_overclaim.py` enforces this. Run `pytest tests/test_no_overclaim.py` to verify.

## Sign-off

- [ ] `git status` clean
- [ ] Local commit created with descriptive message
- [ ] No public push without explicit `OPERATOR COMMIT:` from the operator
- [ ] No GitHub remote created without explicit `OPERATOR COMMIT:` from the operator

## Post-release

- [ ] Tag commit
- [ ] SBOM generated (future, Phase 1)
- [ ] Release notes drafted from commit log
