"""Upgrade installed Homebrew packages from the tacogips tap."""

from __future__ import annotations

import json

from .command import CommandError, command_exists, run

TAP = "tacogips/tap"
TAP_PREFIX = f"{TAP}/"

_PASSES = (
    ("formula", "formulae", ("--formula", "--no-ask")),
    ("cask", "casks", ("--cask", "--greedy", "--no-ask")),
)


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


def catalog_names(output: str) -> tuple[frozenset[str], frozenset[str]]:
    """Return (formulae, casks) currently published by the tap."""
    formulae: set[str] = set()
    casks: set[str] = set()
    for entry in json.loads(output):
        formulae.update(entry.get("formula_names", ()))
        casks.update(entry.get("cask_tokens", ()))
    return frozenset(formulae), frozenset(casks)


def partition(
    installed: tuple[str, ...], published: frozenset[str]
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Split installed packages into ones the tap still ships and orphans.

    An empty catalog means the tap could not be read, so nothing is treated as
    orphaned; upgrading everything is safer than skipping everything.
    """
    if not published:
        return installed, ()
    known = tuple(name for name in installed if name in published)
    orphaned = tuple(name for name in installed if name not in published)
    return known, orphaned


def orphan_report(orphaned: tuple[str, ...], package_type: str) -> str:
    """Describe orphaned kegs and the command that removes them."""
    bare = " ".join(name.rsplit("/", 1)[-1] for name in orphaned)
    return "\n".join(
        (
            f"warning: {len(orphaned)} installed {package_type}(s) are no longer"
            f" published by {TAP}: {', '.join(orphaned)}",
            f"  remove with: brew uninstall --{package_type} {bare}",
            f"  (retired packages cannot be addressed as {TAP_PREFIX}<name>;"
            " the bare names above are required)",
        )
    )


def _tap_catalog() -> tuple[frozenset[str], frozenset[str]]:
    try:
        result = run(["brew", "tap-info", "--json", TAP], capture=True)
        return catalog_names(result.stdout)
    except (CommandError, ValueError, TypeError, AttributeError) as error:
        print(f"warning: could not read the {TAP} catalog ({error})")
        print("  orphan detection is disabled for this run")
        return frozenset(), frozenset()


def _installed(package_type: str) -> tuple[str, ...]:
    result = run(
        ["brew", "list", f"--{package_type}", "--full-name"],
        capture=True,
    )
    return tap_packages(result.stdout)


def upgrade() -> None:
    if not command_exists("brew"):
        raise RuntimeError("Homebrew is required to upgrade tacogips packages")

    warnings: list[str] = []
    failures: list[str] = []

    for (package_type, plural, options), published in zip(_PASSES, _tap_catalog()):
        known, orphaned = partition(_installed(package_type), published)
        if orphaned:
            warnings.append(orphan_report(orphaned, package_type))
        if not known:
            print(f"no installed tacogips {plural}")
            continue
        # Each pass runs even when an earlier one fails; they are independent.
        try:
            run(["brew", "upgrade", *options, *known])
        except CommandError as error:
            failures.append(str(error))

    for warning in warnings:
        print(warning)

    if failures:
        raise CommandError("; ".join(failures))
