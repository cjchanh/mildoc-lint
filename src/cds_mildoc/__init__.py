"""CDS MilDoc Linter."""

from .models import Document, Finding, Severity
from .engine import lint_document, lint_path

__all__ = ["Document", "Finding", "Severity", "lint_document", "lint_path"]
__version__ = "0.1.0"
