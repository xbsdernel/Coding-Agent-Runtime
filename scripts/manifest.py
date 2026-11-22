"""Manifest generator and verifier for frozen milestones.

Enforces cryptographic verifiability of frozen codebase milestones
(e.g., schemas-v1, v0-scaffold).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

DEFAULT_FROZEN_FILES = [
    "pyproject.toml",
    "src/codeagent/__init__.py",
    "src/codeagent/schemas.py",
    "src/codeagent/cli.py",
]


def sha256_file(filepath: Path) -> str:
    """Compute the SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def get_git_commit() -> str:
    """Return HEAD commit hash."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception:
        return "unknown"


def get_git_tag() -> str:
    """Return latest git tag or description."""
    try:
        res = subprocess.run(
            ["git", "describe", "--tags", "--always"],
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception:
        return "unknown"


def generate_manifest(
    milestone: str,
    output_path: Path,
    files: list[str] | None = None,
    root_dir: Path | None = None,
) -> dict:
    """Generate a cryptographic manifest of frozen files."""
    root = root_dir or Path.cwd()
    file_list = files or DEFAULT_FROZEN_FILES
    entries: dict[str, str] = {}

    for rel_path in sorted(file_list):
        p = root / rel_path
        if not p.exists():
            raise FileNotFoundError(f"Cannot freeze non-existent file: {p}")
        entries[rel_path] = sha256_file(p)

    manifest_data = {
        "milestone": milestone,
        "git_commit": get_git_commit(),
        "git_tag": get_git_tag(),
        "created_at": datetime.now(UTC).isoformat(),
        "files": entries,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2, sort_keys=True)
        f.write("\n")

    return manifest_data


def verify_manifest(manifest_path: Path, root_dir: Path | None = None) -> bool:
    """Verify disk files against recorded manifest hashes."""
    root = root_dir or Path.cwd()
    if not manifest_path.exists():
        print(f"ERROR: Manifest file not found: {manifest_path}", file=sys.stderr)
        return False

    with open(manifest_path, encoding="utf-8") as f:
        data = json.load(f)

    files = data.get("files", {})
    all_ok = True

    print(f"Verifying milestone: {data.get('milestone')} (tag: {data.get('git_tag')})")
    for rel_path, expected_hash in files.items():
        p = root / rel_path
        if not p.exists():
            print(f"  [MISSING] {rel_path}", file=sys.stderr)
            all_ok = False
            continue
        actual_hash = sha256_file(p)
        if actual_hash == expected_hash:
            print(f"  [OK]      {rel_path}")
        else:
            msg = (
                f"  [MUTATED] {rel_path} "
                f"(expected {expected_hash[:8]}..., got {actual_hash[:8]}...)"
            )
            print(msg, file=sys.stderr)
            all_ok = False

    return all_ok


def main() -> None:
    parser = argparse.ArgumentParser(description="Milestone manifest generator & verifier")
    subparsers = parser.add_subparsers(dest="command", required=True)

    gen_p = subparsers.add_parser("generate", help="Generate manifest file")
    gen_p.add_argument("--milestone", required=True, help="Milestone label (e.g. schemas-v1)")
    gen_p.add_argument(
        "--output", default="manifest.json", help="Output path (default: manifest.json)"
    )

    ver_p = subparsers.add_parser("verify", help="Verify files against manifest")
    ver_p.add_argument(
        "--manifest", default="manifest.json", help="Manifest path (default: manifest.json)"
    )

    args = parser.parse_args()

    if args.command == "generate":
        out = Path(args.output)
        manifest = generate_manifest(args.milestone, out)
        count = len(manifest["files"])
        print(f"Generated manifest for {args.milestone} at {out} with {count} files.")
    elif args.command == "verify":
        ok = verify_manifest(Path(args.manifest))
        if not ok:
            sys.exit(1)
        print("All frozen files verified successfully.")


if __name__ == "__main__":
    main()
