# Quickstart — no coding required

`mildoc-lint` runs entirely on your own computer. It never sends your files anywhere — no network, no telemetry, no cloud.

This guide is for people who do not normally use a terminal. If you are comfortable with `pip`, use the [README](../README.md) instead.

## 1. Download

Go to the **[Releases page](https://github.com/cjchanh/mildoc-lint/releases/latest)** and download the file for your computer:

| Your computer | Download |
|---|---|
| Windows | `mildoc-lint-windows-x64.zip` |
| Mac (Apple Silicon — M1/M2/M3/M4) | `mildoc-lint-macos-arm64.tar.gz` |
| Linux | `mildoc-lint-linux-x64.tar.gz` |

> Intel Macs do not yet have a prebuilt download. Install from source instead — see the [README](../README.md).

Optionally also download `SHA256SUMS` to verify the download (recommended in cleared environments — see the last section).

## 2. Unpack

- **Windows:** right-click the `.zip` and choose *Extract All*.
- **Mac / Linux:** double-click the `.tar.gz`, or run `tar -xzf mildoc-lint-*.tar.gz`.

You now have a **folder** that contains the `mildoc-lint` program.

## 3. Open a terminal in that folder

- **Windows:** open the extracted folder, click the address bar, type `cmd`, and press Enter.
- **Mac:** right-click the folder and choose *New Terminal at Folder*.
- **Linux:** right-click inside the folder and choose *Open Terminal*.

## 4. Check one document

```
mildoc-lint lint "path/to/your/document.md"
```

Replace the path with your file. Supported formats: `.txt`, `.md`, `.rst`, `.docx`.
(On Mac/Linux you may need to type `./mildoc-lint` instead of `mildoc-lint`.)

You will see a list of findings — what looks off and how to fix it. Nothing is uploaded, and nothing in your file is changed.

## 5. Check a whole folder

```
mildoc-lint lint "path/to/your/folder" --profile mildoc
```

## What the results mean

- **BLOCKER / ERROR** — a structural problem worth fixing before the document goes out.
- **WARN** — worth a look.
- **INFO** — a suggestion.

`mildoc-lint` checks **shape**, not content. It does not decide what is CUI, does not certify compliance, and does not replace official review, QA, CSEC, or command approval. See [`INTENT.md`](../INTENT.md).

## Verify your download (optional, recommended for cleared use)

From the folder that has both the download and `SHA256SUMS`:

```
shasum -a 256 -c SHA256SUMS      # Mac / Linux
```

If it prints `OK`, the file is intact and unmodified.
