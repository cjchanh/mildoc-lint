from __future__ import annotations

import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from .models import Document

SUPPORTED_SUFFIXES = {".txt", ".md", ".markdown", ".rst", ".docx", ".pdf"}
TEXT_SUFFIXES = {".txt", ".md", ".markdown", ".rst", ".csv", ".json", ".yaml", ".yml"}


class ParserError(RuntimeError):
    pass


def iter_paths(path: str | Path, recursive: bool = True) -> list[Path]:
    root = Path(path)
    if root.is_file():
        return [root]
    if not root.exists():
        raise ParserError(f"path does not exist: {root}")
    pattern = "**/*" if recursive else "*"
    paths = [p for p in root.glob(pattern) if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES | TEXT_SUFFIXES]
    return sorted(paths)


def load_document(path: str | Path) -> Document:
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix in TEXT_SUFFIXES or suffix == "":
        return Document(text=_read_text(p), path=str(p), kind=suffix.lstrip(".") or "text")
    if suffix == ".docx":
        return Document(text=_read_docx(p), path=str(p), kind="docx")
    if suffix == ".pdf":
        return Document(text=_read_pdf(p), path=str(p), kind="pdf")
    raise ParserError(f"unsupported file type: {p.suffix}")


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def _read_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dependency branch
        raise ParserError(
            'PDF parsing requires optional dependency: install with `pipx install "mildoc-lint[pdf]"`, '
            '`pip install "mildoc-lint[pdf]"`, or, from a checkout, `pip install -e ".[pdf]"`'
        ) from exc

    try:
        reader = PdfReader(str(path))
        pages: list[str] = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
        return "\f".join(pages)
    except Exception as exc:  # pragma: no cover - depends on PDF internals
        raise ParserError(f"failed to parse PDF {path}: {exc}") from exc


def _read_docx(path: Path) -> str:
    """Extract readable text from a DOCX without non-stdlib dependencies.

    The extractor includes headers and footers because CUI markings often live there.
    It is not a layout engine and does not reproduce Word pagination.
    """
    try:
        with zipfile.ZipFile(path) as zf:
            names = zf.namelist()
            parts: list[tuple[str, str]] = []
            for name in names:
                if name == "word/document.xml":
                    parts.append(("DOCUMENT", zf.read(name).decode("utf-8", errors="replace")))
            for name in names:
                if re.match(r"word/header\d*\.xml$", name):
                    parts.append((f"HEADER {Path(name).name}", zf.read(name).decode("utf-8", errors="replace")))
            for name in names:
                if re.match(r"word/footer\d*\.xml$", name):
                    parts.append((f"FOOTER {Path(name).name}", zf.read(name).decode("utf-8", errors="replace")))
    except zipfile.BadZipFile as exc:
        raise ParserError(f"not a valid DOCX: {path}") from exc

    rendered: list[str] = []
    for label, xml in parts:
        text = _xml_to_lines(xml)
        if text:
            rendered.append(f"[{label}]")
            rendered.extend(text)
    return "\n".join(rendered).strip() + "\n"


def _xml_to_lines(xml: str) -> list[str]:
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return []

    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    lines: list[str] = []

    for para in root.findall(".//w:p", ns):
        chunks: list[str] = []
        for node in para.iter():
            tag = node.tag.rsplit("}", 1)[-1]
            if tag == "t" and node.text:
                chunks.append(node.text)
            elif tag == "tab":
                chunks.append("\t")
            elif tag in {"br", "cr"}:
                chunks.append("\n")
        line = "".join(chunks).replace("\xa0", " ").strip()
        if line:
            lines.extend(part.rstrip() for part in line.splitlines())
    return lines
