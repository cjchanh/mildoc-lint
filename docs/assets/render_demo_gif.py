#!/usr/bin/env python3
"""Render an animated GIF of a mildoc-lint run for social posts.

Deterministic and headless: builds an asciicast (typed command + the real
linter output, at a fixed terminal size so nothing scrolls) and renders it to
docs/assets/demo.gif via `agg`. The README uses the static demo.png; this GIF
is for fast-scroll feeds (Hacker News / Reddit / X) where motion helps.

Regenerate (from the repo root, with mildoc-lint and agg on PATH):

    python3 docs/assets/render_demo_gif.py

agg: https://github.com/asciinema/agg  (`brew install agg`).
The severity labels are tinted at render time for scannability; the linter
itself emits plain text.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEMO_DOC = "demo-order.md"
COMMENT = "# a draft CUI order - check it locally, before it leaves your laptop"
CMD = f"mildoc-lint lint {DEMO_DOC} --profile mildoc"
COLS, ROWS = 100, 46

TINT = {"[ERROR]": "\033[31m", "[WARN]": "\033[33m", "[INFO]": "\033[36m"}


def lint_output() -> list[str]:
    proc = subprocess.run(
        ["mildoc-lint", "lint", DEMO_DOC, "--profile", "mildoc"],
        cwd=HERE,
        capture_output=True,
        text=True,
        check=False,
    )
    return (proc.stdout or proc.stderr).rstrip("\n").split("\n")


def tint(line: str) -> str:
    stripped = line.lstrip()
    for label, code in TINT.items():
        if stripped.startswith(label):
            return line.replace(label, f"{code}{label}\033[0m", 1)
    if line.startswith("mildoc-lint:"):
        return f"\033[1m{line}\033[0m"
    return line


def build_cast(path: Path) -> None:
    events: list[list[object]] = []
    t = 0.3
    events.append([round(t, 3), "o", f"\033[90m{COMMENT}\033[0m\r\n"])
    t = 1.0
    events.append([round(t, 3), "o", "\033[32m$ \033[0m"])
    for ch in CMD:
        t += 0.045
        events.append([round(t, 3), "o", ch])
    t += 0.35
    events.append([round(t, 3), "o", "\r\n"])
    t += 0.45
    body = "\r\n".join(tint(ln) for ln in lint_output()) + "\r\n"
    events.append([round(t, 3), "o", body])

    with path.open("w", encoding="utf-8") as f:
        f.write(json.dumps({"version": 2, "width": COLS, "height": ROWS}) + "\n")
        for ev in events:
            f.write(json.dumps(ev) + "\n")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        cast = Path(tmp) / "demo.cast"
        build_cast(cast)
        out = HERE / "demo.gif"
        subprocess.run(
            [
                "agg",
                "--font-size",
                "14",
                "--theme",
                "dracula",
                "--last-frame-duration",
                "4",
                str(cast),
                str(out),
            ],
            check=True,
        )
        print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
