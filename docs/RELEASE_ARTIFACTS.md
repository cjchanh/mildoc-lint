# Release Artifacts

`mildoc-lint` release artifacts are a convenience path for users who do not want
to install Python before running the CLI.

## Artifact Matrix

| Platform | Artifact | Contents |
|---|---|---|
| macOS arm64 | `mildoc-lint-macos-arm64.tar.gz` | `mildoc-lint`, `README.txt`, `LICENSE` |
| macOS x64 | `mildoc-lint-macos-x64.tar.gz` | `mildoc-lint`, `README.txt`, `LICENSE` |
| Windows x64 | `mildoc-lint-windows-x64.zip` | `mildoc-lint.exe`, `README.txt`, `LICENSE` |
| Linux x64 | `mildoc-lint-linux-x64.tar.gz` | `mildoc-lint`, `README.txt`, `LICENSE` |

Linux arm64 is not part of the first artifact matrix.

## Checksum Verification

Every artifact bundle should be accompanied by `SHA256SUMS`.

```bash
sha256sum -c SHA256SUMS
```

On macOS:

```bash
shasum -a 256 -c SHA256SUMS
```

On Windows PowerShell, compare the listed checksum with:

```powershell
Get-FileHash .\mildoc-lint-windows-x64.zip -Algorithm SHA256
```

## Unsigned Binary Warning

The first standalone artifacts are unsigned. They are intended as open-source
convenience artifacts, not enterprise-signed installers.

Signing roadmap:

- macOS Developer ID signing and notarization later
- Windows signing later
- Linux AppImage later

## Runtime Boundary

Standalone artifacts keep the same product boundary as the Python package:

- local execution
- no telemetry
- no model calls
- no runtime network dependency
- no compliance certification
- no classification review
- synthetic public examples only
