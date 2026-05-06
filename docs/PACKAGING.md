# Packaging

`mildoc-lint v0.2.1` adds packaging infrastructure only. It does not add a GUI,
desktop shell, maintainer assistant, manual ingestion, RAG, or v0.3 rule-pack
metadata.

## PyPI And pipx Path

The package is configured in `pyproject.toml`:

- project name: `mildoc-lint`
- console script: `mildoc-lint`
- compatibility alias: `cds-mildoc`
- license: Apache-2.0

Recommended install command after publication:

```bash
pipx install mildoc-lint
```

This repo does not publish to PyPI automatically.

## Standalone Binary Path

Standalone binaries are built with PyInstaller through:

```bash
python scripts/build_binary.py
```

Expected local output:

```text
dist/
  mildoc-lint-<platform>-<arch>/
    mildoc-lint
    README.txt
    LICENSE
```

On Windows, the executable is `mildoc-lint.exe`.

After the archive-packaging step has created `release/`, generate checksums for
those bundles with:

```bash
python scripts/checksum_artifacts.py release
```

## GitHub Actions Matrix

`.github/workflows/build-artifacts.yml` builds release artifacts on:

- `ubuntu-latest`
- `windows-latest`
- `macos-13`
- `macos-14`

The workflow runs tests, ruff, CLI smoke checks, PyInstaller build, built-binary
smoke checks, packaging, checksum generation, and artifact upload. It does not
publish to PyPI and does not create a GitHub Release.

## Signing Roadmap

Signing is deliberately out of scope for `v0.2.1`.

- macOS: Developer ID signing and notarization later
- Windows: signing later
- Linux: AppImage later

## Desktop Boundary

No GUI ships in `v0.2.1`. A future desktop wrapper should remain separate from
the CLI/library release surface until CLI adoption justifies the larger
installer and security surface.
