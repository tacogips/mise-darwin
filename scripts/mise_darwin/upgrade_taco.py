"""Upgrade installed Homebrew packages from the tacogips tap."""

from __future__ import annotations

from .command import command_exists, run

TAP_PREFIX = "tacogips/tap/"


def tap_packages(output: str) -> tuple[str, ...]:
    """Return unique, fully qualified tacogips tap packages."""
    return tuple(
        sorted(
            {
                line.strip()
                for line in output.splitlines()
                if line.strip().startswith(TAP_PREFIX)
            }
        )
    )


def _installed(package_type: str) -> tuple[str, ...]:
    result = run(
        ["brew", "list", f"--{package_type}", "--full-name"],
        capture=True,
    )
    return tap_packages(result.stdout)


def upgrade() -> None:
    if not command_exists("brew"):
        raise RuntimeError("Homebrew is required to upgrade tacogips packages")

    formulae = _installed("formula")
    casks = _installed("cask")

    if formulae:
        run(["brew", "upgrade", "--formula", "--no-ask", *formulae])
    else:
        print("no installed tacogips formulae")

    if casks:
        run(["brew", "upgrade", "--cask", "--greedy", "--no-ask", *casks])
    else:
        print("no installed tacogips casks")
