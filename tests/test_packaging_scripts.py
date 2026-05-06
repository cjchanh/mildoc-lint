"""Packaging helper regression tests."""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts import build_binary
from scripts.build_binary import _readme_text
from scripts.checksum_artifacts import write_checksums


def test_checksum_artifacts_is_deterministic(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact"
    artifact.mkdir()
    (artifact / "b.txt").write_text("bravo\n", encoding="utf-8")
    (artifact / "a.txt").write_text("alpha\n", encoding="utf-8")

    first = write_checksums(artifact).read_text(encoding="utf-8")
    second = write_checksums(artifact).read_text(encoding="utf-8")

    assert first == second
    assert first.splitlines()[0].endswith("  a.txt")
    assert first.splitlines()[1].endswith("  b.txt")


def test_checksum_artifacts_excludes_generated_cache_and_existing_checksum(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact"
    cache = artifact / "__pycache__"
    artifact.mkdir()
    cache.mkdir()
    (artifact / "payload.txt").write_text("payload\n", encoding="utf-8")
    (artifact / "SHA256SUMS").write_text("old\n", encoding="utf-8")
    (cache / "payload.pyc").write_bytes(b"cache")

    text = write_checksums(artifact).read_text(encoding="utf-8")

    assert "payload.txt" in text
    assert "SHA256SUMS" not in text
    assert "__pycache__" not in text


def test_checksum_artifacts_rejects_empty_artifact_dir(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="artifact directory is empty"):
        write_checksums(tmp_path)


def test_copy_pyinstaller_output_only_replaces_destination(tmp_path: Path) -> None:
    source = tmp_path / "raw" / "mildoc-lint"
    destination = tmp_path / "dist" / "mildoc-lint-macos-arm64"
    sibling = tmp_path / "dist" / "mildoc-lint-linux-x64"
    source.mkdir(parents=True)
    destination.mkdir(parents=True)
    sibling.mkdir(parents=True)
    (source / "mildoc-lint").write_text("new\n", encoding="utf-8")
    (destination / "mildoc-lint").write_text("old\n", encoding="utf-8")
    (sibling / "mildoc-lint").write_text("existing\n", encoding="utf-8")

    build_binary._copy_pyinstaller_output(source, destination)

    assert (destination / "mildoc-lint").read_text(encoding="utf-8") == "new\n"
    assert (sibling / "mildoc-lint").read_text(encoding="utf-8") == "existing\n"


def test_build_binary_replaces_artifact_without_leaving_backup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw_dist = tmp_path / "build" / "pyinstaller" / "dist" / "mildoc-lint"
    (tmp_path / "LICENSE").write_text("license\n", encoding="utf-8")
    artifact_dir = tmp_path / "dist" / "mildoc-lint-linux-x64"
    artifact_dir.mkdir(parents=True)
    (artifact_dir / "mildoc-lint").write_text("old\n", encoding="utf-8")

    monkeypatch.setattr(build_binary, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(build_binary, "SPEC_PATH", tmp_path / "mildoc-lint.spec")
    build_binary.SPEC_PATH.write_text("# spec\n", encoding="utf-8")

    class FakePyInstaller:
        @staticmethod
        def run(_args: list[str]) -> None:
            raw_dist.mkdir(parents=True)
            (raw_dist / "mildoc-lint").write_text("new\n", encoding="utf-8")
            return None

    monkeypatch.setitem(__import__("sys").modules, "PyInstaller.__main__", FakePyInstaller)

    out = build_binary.build(tmp_path / "dist", "linux", "x64")

    assert out == artifact_dir
    assert (artifact_dir / "mildoc-lint").read_text(encoding="utf-8") == "new\n"
    assert not (tmp_path / "dist" / ".mildoc-lint-linux-x64.bak").exists()


def test_binary_readme_names_windows_executable() -> None:
    text = _readme_text("windows", "x64")

    assert r".\mildoc-lint.exe --version" in text
    assert r".\mildoc-lint.exe lint C:\path\to\docs --profile all" in text
    assert "no telemetry" in text


def test_build_binary_rejects_tag_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(build_binary, "_platform_tag", lambda: "linux")
    monkeypatch.setattr(build_binary, "_arch_tag", lambda: "x64")

    with pytest.raises(SystemExit, match="tag mismatch"):
        build_binary._validate_native_tags("windows", "x64")
