"""Tests for the milestone manifest generator and verifier."""

from __future__ import annotations

# Add scripts directory to sys.path so manifest module can be imported
import sys
from pathlib import Path

scripts_dir = str(Path(__file__).resolve().parent.parent / "scripts")
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from manifest import generate_manifest, sha256_file, verify_manifest  # noqa: E402


def test_sha256_file(tmp_path: Path):
    sample = tmp_path / "sample.txt"
    sample.write_text("hello world\n", encoding="utf-8")
    digest = sha256_file(sample)
    assert len(digest) == 64
    assert isinstance(digest, str)


def test_generate_and_verify_manifest(tmp_path: Path):
    f1 = tmp_path / "a.py"
    f2 = tmp_path / "b.txt"
    f1.write_text("x = 1\n", encoding="utf-8")
    f2.write_text("content\n", encoding="utf-8")

    manifest_file = tmp_path / "manifest.json"
    manifest_data = generate_manifest(
        milestone="test-v1",
        output_path=manifest_file,
        files=["a.py", "b.txt"],
        root_dir=tmp_path,
    )

    assert manifest_data["milestone"] == "test-v1"
    assert "a.py" in manifest_data["files"]
    assert "b.txt" in manifest_data["files"]
    assert manifest_file.exists()

    # Verify passes when files are untouched
    assert verify_manifest(manifest_file, root_dir=tmp_path) is True

    # Mutate a file
    f1.write_text("x = 2\n", encoding="utf-8")
    assert verify_manifest(manifest_file, root_dir=tmp_path) is False

    # Delete a file
    f2.unlink()
    assert verify_manifest(manifest_file, root_dir=tmp_path) is False
