"""PyInstaller console entrypoint for mildoc-lint."""
from __future__ import annotations

from cds_mildoc.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
