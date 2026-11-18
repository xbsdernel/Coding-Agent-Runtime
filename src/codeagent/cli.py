"""CLI entry point for the Coding-Agent Runtime."""

from __future__ import annotations

import subprocess
import sys

import click

from codeagent import __version__


def _git_describe() -> str:
    """Return `git describe --tags --always --dirty` or 'unknown'."""
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--always", "--dirty", "--long"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        result = subprocess.run(
            ["git", "describe", "--tags", "--always", "--dirty"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def _is_dirty() -> bool:
    """Return True if the git working tree has uncommitted or untracked changes."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return False
        return bool(result.stdout.strip())
    except Exception:
        return False


def _version_callback(ctx: click.Context, param: click.Parameter, value: bool) -> None:
    """Print version with full git describe stamping and exit."""
    if not value or ctx.resilient_parsing:
        return
    desc = _git_describe()
    click.echo(f"codeagent {__version__} ({desc})")
    ctx.exit()


@click.group()
@click.option(
    "--version",
    is_flag=True,
    callback=_version_callback,
    expose_value=False,
    is_eager=True,
    help="Show the version and exit.",
)
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
