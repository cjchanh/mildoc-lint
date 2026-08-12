#!/usr/bin/env python3
"""Build a native PyInstaller artifact for the current platform."""
from __future__ import annotations

import argparse
import importlib.util
import platform
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = REPO_ROOT / "packaging" / "pyinstaller" / "mildoc-lint.spec"


def _platform_tag() -> str:
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    if system == "windows":
        return "windows"
    if system == "linux":
        return "linux"
    return system.replace(" ", "-")


def _arch_tag() -> str:
    machine = platform.machine().lower()
    if machine in {"x86_64", "amd64"}:
        return "x64"
    if machine in {"arm64", "aarch64"}:
        return "arm64"
    return machine.replace(" ", "-")


def _readme_text(platform_tag: str, arch_tag: str) -> str:
    executable = ".\\mildoc-lint.exe" if platform_tag == "windows" else "./mildoc-lint"
    sample_path = r"C:\path\to\docs" if platform_tag == "windows" else "/path/to/docs"
    return (
        "mildoc-lint standalone artifact\n"
        f"Platform: {platform_tag}-{arch_tag}\n\n"
        "Run:\n"
        f"  {executable} --version\n"
        f"  {executable} lint {sample_path} --profile all\n\n"
        "Boundary:\n"
        "- local execution\n"
        "- no telemetry\n"
        "- no model calls\n"
        "- no runtime network dependency\n"
        "- synthetic public examples only\n"
    )


def _remove_path(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    elif path.exists() or path.is_symlink():
        path.unlink()


def _copy_pyinstaller_output(source: Path, destination: Path) -> None:
    _remove_path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)

    if source.is_dir():
        shutil.copytree(source, destination)
        return

    if source.is_file():
        destination.mkdir(parents=True)
        shutil.copy2(source, destination / source.name)
        return

    raise FileNotFoundError(f"PyInstaller output not found: {source}")


def _module_is_missing(module: str) -> bool:
    try:
        return importlib.util.find_spec(module) is None
    except ModuleNotFoundError:
        return True


def _require_build_dependencies():
    missing = [
        name
        for name, module in (
            ("PyInstaller", "PyInstaller"),
            ("pypdf", "pypdf"),
        )
        if _module_is_missing(module)
    ]
    if missing:
        joined = ", ".join(missing)
        raise SystemExit(
            f"Build dependencies are missing ({joined}). Run: python -m pip install -e '.[build]'"
        )
    try:
        import PyInstaller.__main__ as pyinstaller
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "PyInstaller is not installed. Run: python -m pip install -e '.[build]'"
        ) from exc
    return pyinstaller


def _prepare_build_root() -> Path:
    if not SPEC_PATH.exists():
        raise FileNotFoundError(f"missing PyInstaller spec: {SPEC_PATH}")

    build_root = REPO_ROOT / "build" / "pyinstaller"
    raw_dist = build_root / "dist"
    work_path = build_root / "work"
    if build_root.exists():
        shutil.rmtree(build_root)
    raw_dist.mkdir(parents=True, exist_ok=True)
    work_path.mkdir(parents=True, exist_ok=True)
    return raw_dist


def _run_pyinstaller(pyinstaller, raw_dist: Path) -> None:
    work_path = raw_dist.parent / "work"
    pyinstaller.run(
        [
            "--clean",
            "--noconfirm",
            "--distpath",
            str(raw_dist),
            "--workpath",
            str(work_path),
            str(SPEC_PATH),
        ]
    )


def _stage_artifact(
    dist_dir: Path,
    pyinstaller_output: Path,
    platform_tag: str,
    arch_tag: str,
) -> Path:
    artifact_name = f"mildoc-lint-{platform_tag}-{arch_tag}"
    artifact_dir = dist_dir / artifact_name
    staging_dir = dist_dir / f".{artifact_name}.tmp"
    backup_dir = dist_dir / f".{artifact_name}.bak"
    _copy_pyinstaller_output(pyinstaller_output, staging_dir)

    shutil.copy2(REPO_ROOT / "LICENSE", staging_dir / "LICENSE")
    (staging_dir / "README.txt").write_text(
        _readme_text(platform_tag, arch_tag),
        encoding="utf-8",
    )
    if backup_dir.exists():
        _remove_path(backup_dir)
    if artifact_dir.exists():
        artifact_dir.replace(backup_dir)
    try:
        staging_dir.replace(artifact_dir)
    except Exception:
        if backup_dir.exists() and not artifact_dir.exists():
            backup_dir.replace(artifact_dir)
        raise
    if backup_dir.exists():
        _remove_path(backup_dir)
    return artifact_dir


def build(dist_dir: Path, platform_tag: str, arch_tag: str) -> Path:
    pyinstaller = _require_build_dependencies()
    raw_dist = _prepare_build_root()
    _run_pyinstaller(pyinstaller, raw_dist)
    return _stage_artifact(
        dist_dir=dist_dir,
        pyinstaller_output=raw_dist / "mildoc-lint",
        platform_tag=platform_tag,
        arch_tag=arch_tag,
    )


def _validate_native_tags(platform_tag: str, arch_tag: str) -> None:
    detected_platform = _platform_tag()
    detected_arch = _arch_tag()
    if platform_tag == detected_platform and arch_tag == detected_arch:
        return

    raise SystemExit(
        f"tag mismatch: current runner is {detected_platform}-{detected_arch}, "
        f"got {platform_tag}-{arch_tag}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a mildoc-lint standalone binary.")
    parser.add_argument("--dist-dir", default="dist", help="output directory")
    parser.add_argument("--platform-tag", default=_platform_tag())
    parser.add_argument("--arch-tag", default=_arch_tag())
    parser.add_argument(
        "--validate-native-tags",
        action="store_true",
        help="validate platform and architecture tags without building",
    )
    args = parser.parse_args()

    _validate_native_tags(args.platform_tag, args.arch_tag)
    if args.validate_native_tags:
        return 0

    artifact = build(
        dist_dir=(REPO_ROOT / args.dist_dir).resolve(),
        platform_tag=args.platform_tag,
        arch_tag=args.arch_tag,
    )
    try:
        display_path = artifact.relative_to(REPO_ROOT)
    except ValueError:
        display_path = artifact
    print(f"built artifact: {display_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
