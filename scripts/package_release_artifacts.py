#!/usr/bin/env python3
"""Package standalone binary artifacts for release upload."""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def _remove_path(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    elif path.exists() or path.is_symlink():
        path.unlink()


def _archive_settings(artifact_name: str) -> tuple[str, str]:
    if "-windows-" in artifact_name:
        return "zip", ".zip"
    if "-linux-" in artifact_name or "-macos-" in artifact_name:
        return "gztar", ".tar.gz"
    raise ValueError(f"unsupported artifact name: {artifact_name}")


def package_release_artifact(
    dist_dir: Path,
    release_dir: Path,
) -> Path:
    if not dist_dir.exists() or not dist_dir.is_dir():
        raise FileNotFoundError(f"dist directory does not exist: {dist_dir}")

    release_dir.mkdir(exist_ok=True)
    folders = sorted(
        p for p in dist_dir.iterdir() if p.is_dir() and p.name.startswith("mildoc-lint-")
    )
    if len(folders) != 1:
        raise ValueError(f"expected one artifact folder, found {folders}")

    archive_format, archive_suffix = _archive_settings(folders[0].name)
    archive_path = release_dir / f"{folders[0].name}{archive_suffix}"
    _remove_path(archive_path)
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
