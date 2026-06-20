"""Packaging helper regression tests."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from scripts import build_binary
from scripts.build_binary import _readme_text
from scripts.checksum_artifacts import write_checksums
from scripts.package_release_artifacts import package_release_artifact

REPO_ROOT = Path(__file__).resolve().parents[1]


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


def test_checksum_artifacts_rejects_nested_payload_without_recursive(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact"
    nested = artifact / "_internal"
    nested.mkdir(parents=True)
    (nested / "payload.dylib").write_bytes(b"payload")

    with pytest.raises(ValueError, match="nested directories: _internal"):
        write_checksums(artifact)


def test_checksum_artifacts_can_include_nested_payload_recursively(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact"
    nested = artifact / "_internal"
    nested.mkdir(parents=True)
    (nested / "payload.dylib").write_bytes(b"payload")

    text = write_checksums(artifact, recursive=True).read_text(encoding="utf-8")

    assert "_internal/payload.dylib" in text


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


def test_copy_pyinstaller_output_replaces_stale_destination_file(tmp_path: Path) -> None:
    source = tmp_path / "raw" / "mildoc-lint"
    destination = tmp_path / "dist" / "mildoc-lint-macos-arm64"
    source.mkdir(parents=True)
    destination.parent.mkdir(parents=True)
    (source / "mildoc-lint").write_text("new\n", encoding="utf-8")
    destination.write_text("interrupted build marker\n", encoding="utf-8")

    build_binary._copy_pyinstaller_output(source, destination)

    assert destination.is_dir()
    assert (destination / "mildoc-lint").read_text(encoding="utf-8") == "new\n"


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


def test_stage_artifact_recovers_from_stale_backup_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw_output = tmp_path / "raw" / "mildoc-lint"
    artifact_dir = tmp_path / "dist" / "mildoc-lint-linux-x64"
    backup_path = tmp_path / "dist" / ".mildoc-lint-linux-x64.bak"
    raw_output.mkdir(parents=True)
    artifact_dir.mkdir(parents=True)
    (tmp_path / "LICENSE").write_text("license\n", encoding="utf-8")
    (raw_output / "mildoc-lint").write_text("new\n", encoding="utf-8")
    (artifact_dir / "mildoc-lint").write_text("old\n", encoding="utf-8")
    backup_path.write_text("stale\n", encoding="utf-8")
    monkeypatch.setattr(build_binary, "REPO_ROOT", tmp_path)

    out = build_binary._stage_artifact(tmp_path / "dist", raw_output, "linux", "x64")

    assert out == artifact_dir
    assert (artifact_dir / "mildoc-lint").read_text(encoding="utf-8") == "new\n"
    assert not backup_path.exists()


def test_package_release_artifact_archives_single_platform_folder(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    release = tmp_path / "release"
    artifact = dist / "mildoc-lint-linux-x64"
    artifact.mkdir(parents=True)
    (artifact / "mildoc-lint").write_text("binary\n", encoding="utf-8")

    archive = package_release_artifact(dist, release)

    assert archive == release / "mildoc-lint-linux-x64.tar.gz"
    assert archive.is_file()
    assert sorted(p.name for p in release.iterdir()) == ["mildoc-lint-linux-x64.tar.gz"]


def test_package_release_artifact_uses_zip_for_windows(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    release = tmp_path / "release"
    artifact = dist / "mildoc-lint-windows-x64"
    artifact.mkdir(parents=True)
    (artifact / "mildoc-lint.exe").write_text("binary\n", encoding="utf-8")

    archive = package_release_artifact(dist, release)

    assert archive == release / "mildoc-lint-windows-x64.zip"
    assert archive.is_file()


def test_package_release_artifact_rejects_non_empty_release_dir(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    release = tmp_path / "release"
    artifact = dist / "mildoc-lint-linux-x64"
    artifact.mkdir(parents=True)
    release.mkdir()
    (release / "stale.tar.gz").write_text("stale\n", encoding="utf-8")

    with pytest.raises(ValueError, match="release directory must be empty"):
        package_release_artifact(dist, release)


def test_package_release_artifact_rejects_unknown_artifact_name(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    release = tmp_path / "release"
    artifact = dist / "mildoc-lint-plan9-x64"
    artifact.mkdir(parents=True)

    with pytest.raises(ValueError, match="unsupported artifact name"):
        package_release_artifact(dist, release)


def test_build_binary_requires_pdf_build_dependency(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_module_is_missing(module: str) -> bool:
        return module == "pypdf"

    monkeypatch.setattr(build_binary, "_module_is_missing", fake_module_is_missing)

    with pytest.raises(SystemExit, match=r"Build dependencies are missing \(pypdf\)"):
        build_binary._require_build_dependencies()


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


def test_release_constraints_pin_public_build_toolchain() -> None:
    constraints = REPO_ROOT / "constraints" / "release.txt"
    lines = [
        line.strip()
        for line in constraints.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    required = {
        "build",
        "pyinstaller",
        "pypdf",
        "pytest",
        "ruff",
        "setuptools",
        "wheel",
    }

    assert required <= {line.split("==", maxsplit=1)[0] for line in lines}
    assert all("==" in line and ">=" not in line for line in lines)


def test_release_workflow_pins_publication_actions_and_toolchain() -> None:
    workflow = (REPO_ROOT / ".github" / "workflows" / "build-artifacts.yml").read_text(
        encoding="utf-8"
    )

    assert not re.search(r"actions/[a-z-]+@v\d+", workflow)
    assert len(re.findall(r"actions/[a-z-]+@[0-9a-f]{40}", workflow)) == 7
    # the release-publish action (softprops/action-gh-release) must also be SHA-pinned
    assert not re.search(r"softprops/[a-z-]+@v\d+", workflow)
    assert len(re.findall(r"softprops/[a-z-]+@[0-9a-f]{40}", workflow)) == 1
    assert "python -m pip install -r constraints/release.txt" in workflow
    assert "python -m pip install --no-deps -e ." in workflow
    assert "python -m build --no-isolation" in workflow
    assert 'smoke_env["PIP_BUILD_CONSTRAINT"] = str(constraints)' in workflow
    assert 'smoke_env["PIP_CONSTRAINT"] = str(constraints)' in workflow
    assert "macos-15-intel" in workflow
    assert "macos-13" not in workflow
