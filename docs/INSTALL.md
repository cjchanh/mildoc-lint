# Install

`mildoc-lint` is a local-first CLI. It does not require a network call at
runtime, does not emit telemetry, and does not call model APIs.

## 1. Install With pipx

After PyPI publication, use `pipx` when you want an isolated command-line
install:

```bash
pipx install mildoc-lint
mildoc-lint --version
```

Run a scan against a local document or folder:

```bash
mildoc-lint lint /path/to/docs --profile all
```

PDF input requires the optional PDF extra:

```bash
pipx install "mildoc-lint[pdf]"
# or
pip install "mildoc-lint[pdf]"
```

When installed from a source checkout, the repo's `examples/` corpus can be used
as a synthetic smoke test and intentionally emits findings.

## 2. Install From Source

```bash
git clone https://github.com/cjchanh/mildoc-lint.git
cd mildoc-lint
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
mildoc-lint --version
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
mildoc-lint --version
```

## 3. Run Standalone Binary

Download the `build-artifacts` workflow artifact ZIP from GitHub Actions,
extract it, then unpack the enclosed platform archive:

```bash
unzip mildoc-lint-linux-x64.zip
tar -xzf mildoc-lint-linux-x64.tar.gz
cd mildoc-lint-linux-x64
./mildoc-lint --version
```

On macOS, use the matching `mildoc-lint-macos-arm64.tar.gz` or
`mildoc-lint-macos-x64.tar.gz` artifact.

On Windows, unzip the artifact, enter the unpacked directory, and run:

```powershell
cd .\mildoc-lint-windows-x64
.\mildoc-lint.exe --version
```

Standalone binaries are unsigned in the first release-artifact path. Verify the
download with `SHA256SUMS` before running it.

## 4. Verify Install

```bash
mildoc-lint --version
mildoc-lint lint /path/to/docs --profile all
mildoc-lint lint /path/to/docs --profile all --format sarif --out mildoc-example.sarif
```

For `pipx`, `pip`, and source installs, `cds-mildoc --version` is also available
as a compatibility alias. Standalone binary artifacts ship only `mildoc-lint`.
Public docs prefer `mildoc-lint`.

## 5. Uninstall

For a `pipx` install:

```bash
pipx uninstall mildoc-lint
```

For a source install, remove the virtual environment or uninstall from it:

```bash
pip uninstall mildoc-lint
```

For a standalone binary, delete the unpacked artifact directory.

## 6. Security Note

`mildoc-lint` runs locally. It has no telemetry, no runtime network dependency,
and no model calls. The public repo ships synthetic examples only. Do not scan
or submit real CUI, PII, customer documents, unit documents, controlled technical
data, or operational details unless your environment is authorized for that data.
