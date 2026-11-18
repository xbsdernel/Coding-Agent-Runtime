"""CLI entry point for the Coding-Agent Runtime."""

from __future__ import annotations

import subprocess
import sys

import click

from codeagent import __version__


def _git_describe() -> str:
    """Return `git describe --always --dirty` or 'unknown'."""
    try:
        result = subprocess.run(
            ["git", "describe", "--always", "--dirty", "--tags"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def _is_dirty() -> bool:
    """Return True if the git working tree has uncommitted changes."""
    try:
        result = subprocess.run(
            ["git", "diff", "--quiet"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode != 0
    except Exception:
        return False


@click.group()
@click.version_option(version=__version__, prog_name="codeagent")
def main() -> None:
    """Coding-Agent Runtime — autonomous code-repair agent framework."""


@main.command()
def info() -> None:
    """Print runtime version and git state."""
    desc = _git_describe()
    click.echo(f"codeagent {__version__} (git: {desc})")


@main.command()
def run() -> None:
    """Execute an agent episode (placeholder)."""
    if _is_dirty():
        click.secho("ERROR: Refusing to run on a dirty working tree.", fg="red", err=True)
        click.echo("Commit or stash your changes first.", err=True)
        sys.exit(1)
    click.echo("Agent run — not yet implemented.")


if __name__ == "__main__":
    main()
