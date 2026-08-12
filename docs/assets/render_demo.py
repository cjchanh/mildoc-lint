#!/usr/bin/env python3
"""Render a styled terminal-window PNG of a mildoc-lint run for the README.

Deterministic and reproducible: runs the linter on the synthetic demo-order.md
and draws the real output. Regenerate with:

    python3 docs/assets/render_demo.py

Requires Pillow (`pip install pillow`) and a monospace TTF (macOS Menlo by
default; override with MILDOC_DEMO_FONT). No network, no recording.
"""
from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
DEMO_DOC = "demo-order.md"
WRAP_COLS = 92
SCALE = 2  # retina

# Dracula-ish palette.
BG = (40, 42, 54)
WIN = (33, 34, 44)
FG = (228, 228, 234)
DIM = (140, 144, 160)
SEV = {"[ERROR]": (255, 85, 85), "[WARN]": (241, 250, 140), "[INFO]": (139, 233, 253)}
PROMPT = (80, 250, 123)
DOTS = [(255, 95, 86), (255, 189, 46), (39, 201, 63)]


def load_font(size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        os.environ.get("MILDOC_DEMO_FONT"),
        "/System/Library/Fonts/Menlo.ttc",
        "/System/Library/Fonts/SFNSMono.ttf",
        "/Library/Fonts/Menlo.ttc",
    ]
    for path in candidates:
        if path and Path(path).exists():
            return ImageFont.truetype(path, size)
    raise SystemExit("no monospace TTF found; set MILDOC_DEMO_FONT to one")


def run_lint() -> list[str]:
    proc = subprocess.run(
        ["mildoc-lint", "lint", DEMO_DOC, "--profile", "mildoc"],
        cwd=HERE,
        capture_output=True,
        text=True,
        check=False,
    )
    return (proc.stdout or proc.stderr).rstrip("\n").splitlines()


def wrap(lines: list[str]) -> list[str]:
    out: list[str] = []
    for line in lines:
        if len(line) <= WRAP_COLS:
            out.append(line)
            continue
        indent = " " * (len(line) - len(line.lstrip()) + 2)
        out.extend(textwrap.wrap(line, WRAP_COLS, subsequent_indent=indent) or [""])
    return out


def color_for(line: str) -> tuple[int, int, int]:
    stripped = line.lstrip()
    for label, rgb in SEV.items():
        if stripped.startswith(label):
            return rgb
    if line.startswith("mildoc-lint:"):
        return FG
    if stripped.startswith(("source:", "fix:", "snippet:")):
        return DIM
    return FG


def main() -> int:
    header = "$ mildoc-lint lint demo-order.md --profile mildoc"
    body = wrap(run_lint())
    lines = [header, ""] + body

    fs = 13 * SCALE
    font = load_font(fs)
    bold = load_font(fs)
    pad = 18 * SCALE
    title_h = 22 * SCALE
    asc, desc = font.getmetrics()
    lh = asc + desc + 3 * SCALE

    tmp = Image.new("RGB", (10, 10))
    measure = ImageDraw.Draw(tmp)
    text_w = max(int(measure.textlength(ln, font=font)) for ln in lines)
    width = text_w + pad * 2
    height = title_h + pad + lh * len(lines) + pad

    img = Image.new("RGB", (width, height), BG)
    d = ImageDraw.Draw(img)
    radius = 10 * SCALE
    d.rounded_rectangle([0, 0, width - 1, height - 1], radius=radius, fill=WIN)
    for i, dot in enumerate(DOTS):
        cx = pad + i * 16 * SCALE
        cy = title_h // 2 + 2 * SCALE
        r = 5 * SCALE
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=dot)
    d.text((width // 2, title_h // 2), "mildoc-lint", font=font, fill=DIM, anchor="mm")

    y = title_h + pad
    for ln in lines:
        if ln == header:
            d.text((pad, y), "$ ", font=bold, fill=PROMPT)
            off = int(d.textlength("$ ", font=bold))
            d.text((pad + off, y), ln[2:], font=bold, fill=FG)
        else:
            d.text((pad, y), ln, font=font, fill=color_for(ln))
        y += lh

    out = HERE / "demo.png"
    img.save(out)
    print(f"wrote {out} ({width}x{height})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
