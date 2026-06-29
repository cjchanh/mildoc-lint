#!/usr/bin/env bash
#
# mildoc-lint -- one-command demo
#
# Runs the deterministic linter over a SYNTHETIC draft operations order and shows
# three findings, each cited to a public authority:
#   1. invalid CUI banner          -> DoD CUI Markings Training Aid, 2024
#   2. missing Command and Signal  -> USMC FGHT 1004 (O-SMEAC / operations order)
#   3. exposed SSN (redacted)      -> NIST SP 800-171 Rev. 3
#
# Fail-closed: the linter exits non-zero because ERROR-severity findings exist
# (cite-or-refuse). Zero network, zero telemetry. The SSN is the placeholder
# 123-45-6789 and is redacted in all tool output -- no real CUI or PII anywhere.
#
# Usage:  bash demo/run_demo.sh        (from anywhere in a mildoc-lint checkout)
#
set -uo pipefail

DEMO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$DEMO_DIR/.." && pwd)"
cd "$REPO_ROOT"                       # run from repo root so paths print relative
SAMPLE="demo/sample_draft_opord.md"

if [ ! -f "$SAMPLE" ]; then
  echo "demo: sample not found at $REPO_ROOT/$SAMPLE" >&2
  exit 3
fi

# ----- locate the linter ------------------------------------------------------
# Prefer THIS repository's source so the demo testifies to the working tree, not
# a possibly-stale installed copy. Fall back to the installed console script.
MILDOC_SRC=""
if PYTHONPATH="$REPO_ROOT/src" python3 -c "import cds_mildoc" >/dev/null 2>&1; then
  MILDOC_SRC="$REPO_ROOT/src"
  MODE="repo source ($MILDOC_SRC)"
elif command -v mildoc-lint >/dev/null 2>&1; then
  MODE="installed console script ($(command -v mildoc-lint))"
else
  echo "demo: could not find cds_mildoc on PYTHONPATH or 'mildoc-lint' on PATH." >&2
  echo "      run from a mildoc-lint checkout, or: pipx install mildoc-lint" >&2
  exit 3
fi

run_mildoc() {
  if [ -n "$MILDOC_SRC" ]; then
    PYTHONPATH="$MILDOC_SRC" python3 -m cds_mildoc "$@"
  else
    mildoc-lint "$@"
  fi
}

hr() { printf '%s\n' "----------------------------------------------------------------------"; }

echo "mildoc-lint demo"
echo "linter:  $MODE"
echo "version: $(run_mildoc --version 2>/dev/null || echo unknown)"
echo "sample:  $SAMPLE  (synthetic -- training data only)"
hr

# ----- 1. the lint run (human-readable, every finding cited) ------------------
printf '%s\n\n' '$ mildoc-lint lint demo/sample_draft_opord.md --profile mildoc'
LINT_OUT="$(run_mildoc lint "$SAMPLE" --profile mildoc 2>&1)"; LINT_RC=$?
printf '%s\n\n' "$LINT_OUT"
echo "(exit code: $LINT_RC -- non-zero is fail-closed: ERROR findings present)"
hr

# ----- 2. cited authority per finding (machine-readable) ----------------------
echo "Cited authority per finding (parsed from --format json):"
echo
run_mildoc lint "$SAMPLE" --profile mildoc --format json 2>/dev/null \
  | python3 "$DEMO_DIR/show_citations.py"
hr

# ----- 3. fail-closed gate (cite-or-refuse, explicit BLOCKED decision) --------
# 'archivist gate --require-no-pii' returns a BLOCKED decision and a non-zero
# exit because the document carries PII. This is the boundary a CI step hits.
# A throwaway DB path keeps the repo working tree clean.
TMP_DB="$(mktemp -t mildoc_demo_db.XXXXXX)"; rm -f "$TMP_DB"
printf '%s\n\n' '$ mildoc-lint archivist gate demo/sample_draft_opord.md --require-no-pii'
GATE_OUT="$(run_mildoc archivist gate "$SAMPLE" --require-no-pii --db-path "$TMP_DB" 2>&1)"; GATE_RC=$?
printf '%s\n\n' "$GATE_OUT"
echo "(exit code: $GATE_RC -- non-zero is the refusal)"
rm -f "$TMP_DB" "$TMP_DB"-* 2>/dev/null
hr

# ----- 4. self-check: the demo testifies to its own correctness ---------------
fail=0
need() { # need <label> <rc-of-condition>
  if [ "$2" -eq 0 ]; then echo "  PASS  $1"; else echo "  FAIL  $1"; fail=1; fi
}

echo "Self-check (the demo verifies its own output):"
[ "$LINT_RC" -eq 1 ];                                               need "lint exits non-zero on ERROR findings (fail-closed)" $?
printf '%s' "$LINT_OUT" | grep -qF "cui.invalid_banner";            need "flags invalid CUI banner (cui.invalid_banner)" $?
printf '%s' "$LINT_OUT" | grep -qF "osmeac.missing_command_signal"; need "flags missing O-SMEAC Command and Signal" $?
printf '%s' "$LINT_OUT" | grep -qF "pii.ssn";                       need "flags exposed SSN (pii.ssn)" $?
printf '%s' "$LINT_OUT" | grep -qF "DoD CUI Markings Training Aid"; need "CUI finding cites DoD CUI Markings Training Aid, 2024" $?
printf '%s' "$LINT_OUT" | grep -qF "USMC FGHT 1004";                need "Command-and-Signal finding cites USMC FGHT 1004" $?
printf '%s' "$LINT_OUT" | grep -qF "NIST SP 800-171";               need "SSN finding cites NIST SP 800-171 Rev. 3" $?
printf '%s' "$LINT_OUT" | grep -qF -- "***-**-****";                need "SSN is REDACTED in output (***-**-****)" $?
printf '%s' "$LINT_OUT" | grep -qF "123-45-6789"; [ "$?" -ne 0 ];   need "raw SSN never appears in output (zero PII leak)" $?
[ "$GATE_RC" -eq 1 ];                                               need "archivist gate refuses (BLOCKED, non-zero) on PII" $?
hr

if [ "$fail" -eq 0 ]; then
  echo "DEMO PASS -- three cited findings present, SSN redacted, fail-closed exit verified."
  exit 0
else
  echo "DEMO FAIL -- see FAIL lines above."
  exit 4
fi
