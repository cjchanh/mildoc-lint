# Integrations

Drop-in ways to run `mildoc-lint` in other projects. Everything here is local-first — no network calls, no telemetry, no cloud.

## GitHub Actions

Lint your documents on every push / pull request and (optionally) upload results to GitHub code scanning. Copy into `.github/workflows/mildoc-lint.yml`:

```yaml
name: mildoc-lint
on: [pull_request, push]
permissions:
  contents: read
  security-events: write   # only needed for the optional SARIF upload step
jobs:
  mildoc-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pipx install mildoc-lint      # or: pip install mildoc-lint
      - run: mildoc-lint lint ./docs --profile mildoc --format sarif --out mildoc.sarif --fail-on error
      - if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: mildoc.sarif
```

Drop the last step if you only want a pass/fail gate without code-scanning upload.

## pre-commit

Catch issues before they are committed. Add to your repository's `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/cjchanh/mildoc-lint
    rev: v0.2.1
    hooks:
      - id: mildoc-lint
```

Then:

```bash
pip install pre-commit
pre-commit install
```

The hook lints changed `.md`, `.markdown`, `.rst`, and `.txt` files with the `mildoc` profile and fails on `error`. Override per repository:

```yaml
      - id: mildoc-lint
        args: ["--profile", "cui", "--fail-on", "warn"]
        files: '\.(md|rst)$'
```

## Docker

```bash
docker build -t mildoc-lint .
docker run --rm -v "$PWD:/work:ro" mildoc-lint lint /work/docs --profile mildoc
```

The container makes no network calls. Mount your documents read-only (`:ro`).

## Exit codes

`--fail-on <severity>` makes `mildoc-lint` exit non-zero at or above that severity (`info`, `warn`, `error`, `blocker`). Use it to gate CI and pre-commit. The default is `error`.
