#!/usr/bin/env python3
"""Package standalone binary artifacts for release upload."""
from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path


_ARTIFACT_NAME_RE = re.compile(
    r"^mildoc-lint-(?P<platform>linux|macos|windows)-(?P<arch>x64|arm64)$"
)


def _platform_tag_from_artifact_name(artifact_name: str) -> str:
    match = _ARTIFACT_NAME_RE.fullmatch(artifact_name)
    if match is None:
        raise ValueError(f"unsupported artifact name: {artifact_name}")
    return match.group("platform")


def _archive_settings(platform_tag: str) -> tuple[str, str]:
    formats = {
        "windows": ("zip", ".zip"),
        "linux": ("gztar", ".tar.gz"),
        "macos": ("gztar", ".tar.gz"),
    }
    try:
        return formats[platform_tag]
    except KeyError as exc:
        raise ValueError(f"unsupported platform tag: {platform_tag}") from exc


def package_release_artifact(
    dist_dir: Path,
    release_dir: Path,
) -> Path:
    if not dist_dir.exists() or not dist_dir.is_dir():
        raise FileNotFoundError(f"dist directory does not exist: {dist_dir}")

    release_dir.mkdir(parents=True, exist_ok=True)
    staged = sorted(p for p in release_dir.iterdir() if not p.name.startswith("."))
    if staged:
        raise ValueError(f"release directory must be empty before staging: {staged}")

    folders = sorted(
        p for p in dist_dir.iterdir() if p.is_dir() and p.name.startswith("mildoc-lint-")
    )
    if len(folders) != 1:
        raise ValueError(f"expected one artifact folder, found {folders}")

    platform_tag = _platform_tag_from_artifact_name(folders[0].name)
    archive_format, archive_suffix = _archive_settings(platform_tag)
    return Path(
        shutil.make_archive(
            str(release_dir / folders[0].name),
            archive_format,
            root_dir=dist_dir,
            base_dir=folders[0].name,
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Package a mildoc-lint release artifact.")
    parser.add_argument("dist_dir", help="directory containing one mildoc-lint artifact folder")
    parser.add_argument("release_dir", help="directory that receives the release archive")
    args = parser.parse_args()

    archive = package_release_artifact(Path(args.dist_dir).resolve(), Path(args.release_dir).resolve())
    print(archive)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
