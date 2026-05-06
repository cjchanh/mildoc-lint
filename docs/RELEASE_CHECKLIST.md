# Release Checklist

Run before any tag, release, or public-push action. Fail-closed: if any item fails, do not release.

## Code gates

- [ ] `pytest` passes
- [ ] `ruff check .` passes (or pre-existing style is reported separately)
- [ ] `mildoc-lint --version` returns `mildoc-lint 0.1.0`
- [ ] `mildoc-lint lint examples --profile all` runs and reports findings
- [ ] `mildoc-lint lint examples --profile all --format sarif --out /tmp/check.sarif` writes a valid SARIF 2.1.0 file
- [ ] `mildoc-lint rules` lists every authority key

## Repo hygiene

- [ ] No `.DS_Store`, `__MACOSX/`, `*.egg-info/`, `dist/`, or `build/` tracked
- [ ] No real names, real units, real EDIPIs, real SSNs, real OPORDs, or real maintenance records anywhere in fixtures or docs
- [ ] No fake `.mil` contact information that could be mistaken for real
- [ ] No `Cargo.lock` / `target/` (this is a Python repo)

## Claim hygiene

The README and docs must NOT contain any of the following unsupported claims:

- "DoD approved"
- "DoD certified"
- "CMMC compliant"
- "RMF ready"
- "RMF certified"
- "NIST 800-171 certified"
- "certifies"
- "official"
- "full 30-item checklist"
- "CY26Q2 checklist"
- "WASM browser version" (until implemented)
- "local LLM drafting" (until implemented)

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
