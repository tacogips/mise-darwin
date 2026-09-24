"""Uninstall Homebrew formulae and casks that this repository does not declare."""

from __future__ import annotations

import os
import platform
import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from . import REPO_ROOT
from .command import CommandError, command_exists, run

_BREWFILE_ENTRY = re.compile(
    r'^(tap|brew|cask)\s+"((?:\\.|[^"\\])*)"(?:\s*,\s*"((?:\\.|[^"\\])*)")?'
)
_OFFICIAL_TAPS = frozenset({"homebrew/bundle", "homebrew/cask", "homebrew/core"})
_MISE_TOML_FILES = ("mise.macos-arm64.toml",)
_BREWFILES = ("Brewfile.common",)


@dataclass(frozen=True)
class KeepSet:
    """Declared Homebrew taps, formulae, and casks that must not be removed."""

    taps: tuple[tuple[str, str | None], ...] = ()
    formulae: tuple[str, ...] = ()
    casks: tuple[str, ...] = ()


@dataclass(frozen=True)
class Inventory:
    """Currently installed Homebrew packages and retained dependencies."""

    formulae: tuple[str, ...] = ()
    casks: tuple[str, ...] = ()
    taps: tuple[str, ...] = ()
    formula_dependencies: tuple[str, ...] = ()
    cask_formula_dependencies: tuple[str, ...] = ()


@dataclass(frozen=True)
class Removals:
    """Packages and taps that are installed but not in the declared keep-set."""

    formulae: tuple[str, ...] = ()
    casks: tuple[str, ...] = ()
    taps: tuple[str, ...] = ()

    def empty(self) -> bool:
        return not (self.formulae or self.casks or self.taps)


def _unescape(value: str) -> str:
    return bytes(value, "utf-8").decode("unicode_escape")


def _ruby_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _needs_item_trust(name: str) -> bool:
    return "/" in name


def _needs_tap_trust(name: str) -> bool:
    return name not in _OFFICIAL_TAPS


def name_keys(name: str) -> frozenset[str]:
    """Return comparable names for a formula, cask, or tap."""
    return frozenset({name, name.rsplit("/", 1)[-1]})


def expand_names(names: tuple[str, ...]) -> frozenset[str]:
    keys: set[str] = set()
    for name in names:
        keys.update(name_keys(name))
    return frozenset(keys)


def undeclared(installed: tuple[str, ...], kept: frozenset[str]) -> tuple[str, ...]:
    """Return installed names that do not match the keep-set."""
    return tuple(sorted(name for name in installed if not (name_keys(name) & kept)))


def tap_name(package: str) -> str | None:
    """Return `user/repo` for a fully qualified formula or cask name."""
    parts = package.split("/")
    if len(parts) >= 3:
        return f"{parts[0]}/{parts[1]}"
    return None


def brew_packages_from_toml(text: str) -> tuple[str, ...]:
    """Return `brew:` package names from a mise TOML document."""
    data = tomllib.loads(text)
    packages = data.get("bootstrap", {}).get("packages", {})
    names = [
        key.removeprefix("brew:")
        for key in packages
        if isinstance(key, str) and key.startswith("brew:")
    ]
    return tuple(sorted(names))


def taps_from_toml(text: str) -> tuple[tuple[str, str | None], ...]:
    """Return declared Homebrew taps and optional clone URLs."""
    taps = tomllib.loads(text).get("bootstrap", {}).get("brew", {}).get("taps", {})
    if not isinstance(taps, dict):
        return ()
    typed_taps = cast(dict[object, object], taps)
    parsed: list[tuple[str, str | None]] = []
    for raw_name, url in typed_taps.items():
        if not isinstance(raw_name, str):
            continue
        clone: str | None = None
        if isinstance(url, str) and url:
            clone = url
        parsed.append((raw_name, clone))
    return tuple(sorted(parsed))


def parse_brewfile(text: str) -> KeepSet:
    """Parse tap, brew, and cask entries from a Brewfile. Ignore other types."""
    taps: dict[str, str | None] = {}
    formulae: set[str] = set()
    casks: set[str] = set()
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        matched = _BREWFILE_ENTRY.match(line)
        if matched is None:
            continue
        kind, name, clone_target = matched.groups()
        parsed_name = _unescape(name)
        parsed_clone = _unescape(clone_target) if clone_target else None
        if kind == "tap":
            taps[parsed_name] = parsed_clone or taps.get(parsed_name)
        elif kind == "brew":
            formulae.add(parsed_name)
        else:
            casks.add(parsed_name)
    return KeepSet(
        taps=tuple(sorted(taps.items())),
        formulae=tuple(sorted(formulae)),
        casks=tuple(sorted(casks)),
    )


def merge_keep_sets(*sets: KeepSet) -> KeepSet:
    """Combine keep-sets, preferring a tap clone URL when one is present."""
    taps: dict[str, str | None] = {}
    formulae: set[str] = set()
    casks: set[str] = set()
    for keep in sets:
        for name, url in keep.taps:
            current = taps.get(name)
            taps[name] = current or url
        formulae.update(keep.formulae)
        casks.update(keep.casks)
    return KeepSet(
        taps=tuple(sorted(taps.items())),
        formulae=tuple(sorted(formulae)),
        casks=tuple(sorted(casks)),
    )


def keep_set_from_toml(text: str) -> KeepSet:
    return KeepSet(taps=taps_from_toml(text), formulae=brew_packages_from_toml(text))


def load_declared_keep_set(root: Path, profile: str) -> KeepSet:
    """Build the keep-set from this repository's mise files and Brewfiles."""
    keep = KeepSet()
    for relative in (*_MISE_TOML_FILES, f"mise.{profile}.toml"):
        path = root / relative
        if path.is_file():
            keep = merge_keep_sets(keep, keep_set_from_toml(path.read_text(encoding="utf-8")))
    for relative in (*_BREWFILES, f"Brewfile.{profile}"):
        path = root / relative
        if path.is_file():
            keep = merge_keep_sets(keep, parse_brewfile(path.read_text(encoding="utf-8")))
    return keep


def render_brewfile(keep: KeepSet) -> str:
    """Render a Brewfile that names declared packages and their tap trust."""
    lines = [
        "# Generated keep-set for brew cleanup.",
        "# Do not install from this file; it exists only to name retained packages.",
    ]
    for name, url in keep.taps:
        entry = f"tap {_ruby_string(name)}"
        if url:
            entry += f", {_ruby_string(url)}"
        if _needs_tap_trust(name):
            entry += ", trusted: true"
        lines.append(entry)
    for name in keep.formulae:
        entry = f"brew {_ruby_string(name)}"
        if _needs_item_trust(name):
            entry += ", trusted: true"
        lines.append(entry)
    for name in keep.casks:
        entry = f"cask {_ruby_string(name)}"
        if _needs_item_trust(name):
            entry += ", trusted: true"
        lines.append(entry)
    return "\n".join(lines) + "\n"


def removals_from_inventory(keep: KeepSet, inventory: Inventory) -> Removals:
    """Compute undeclared formulae, casks, and taps, retaining Homebrew dependencies."""
    kept_formulae = expand_names(
        keep.formulae + inventory.formula_dependencies + inventory.cask_formula_dependencies
    )
    extra_formulae = undeclared(inventory.formulae, kept_formulae)
    extra_casks = undeclared(inventory.casks, expand_names(keep.casks))
    remaining_packages = tuple(
        name
        for name in (*inventory.formulae, *inventory.casks)
        if name not in extra_formulae and name not in extra_casks
    )
    kept_taps = {name for name, _ in keep.taps} | set(_OFFICIAL_TAPS)
    for package in remaining_packages:
        derived = tap_name(package)
        if derived:
            kept_taps.add(derived)
    return Removals(
        formulae=extra_formulae,
        casks=extra_casks,
        taps=tuple(sorted(name for name in inventory.taps if name not in kept_taps)),
    )


def _brew_env() -> dict[str, str]:
    env = os.environ.copy()
    env["HOMEBREW_NO_AUTO_UPDATE"] = "1"
    return env


def _output_names(output: str) -> tuple[str, ...]:
    return tuple(line.strip() for line in output.splitlines() if line.strip())


def _matching_installed(declared: tuple[str, ...], installed: tuple[str, ...]) -> tuple[str, ...]:
    kept = expand_names(declared)
    return tuple(name for name in installed if name_keys(name) & kept)


def read_inventory(keep: KeepSet) -> Inventory:
    env = _brew_env()
    formulae = _output_names(
        run(["brew", "list", "--formula", "--full-name"], capture=True, env=env).stdout
    )
    casks = _output_names(
        run(["brew", "list", "--cask", "--full-name"], capture=True, env=env).stdout
    )
    taps = _output_names(run(["brew", "tap"], capture=True, env=env).stdout)
    kept_formulae = _matching_installed(keep.formulae, formulae)
    formula_dependencies: tuple[str, ...] = ()
    if kept_formulae:
        formula_dependencies = _output_names(
            run(
                ["brew", "deps", "--union", "--full-name", "--installed", *kept_formulae],
                capture=True,
                env=env,
            ).stdout
        )
    cask_formula_dependencies: list[str] = []
    for cask in _matching_installed(keep.casks, casks):
        result = run(
            ["brew", "deps", "--cask", "--full-name", cask],
            capture=True,
            check=False,
            env=env,
        )
        if result.returncode == 0:
            cask_formula_dependencies.extend(_output_names(result.stdout))
    return Inventory(
        formulae=formulae,
        casks=casks,
        taps=taps,
        formula_dependencies=formula_dependencies,
        cask_formula_dependencies=tuple(cask_formula_dependencies),
    )


def _print_removals(removals: Removals, *, dry_run: bool) -> None:
    prefix = "Would uninstall" if dry_run else "Uninstalling"
    if removals.casks:
        print(f"{prefix} casks:")
        for name in removals.casks:
            print(f"  {name}")
    if removals.formulae:
        print(f"{prefix} formulae:")
        for name in removals.formulae:
            print(f"  {name}")
    if removals.taps:
        print("Would untap:" if dry_run else "Untapping:")
        for name in removals.taps:
            print(f"  {name}")


def _uninstall(removals: Removals) -> int:
    env = _brew_env()
    failures: list[str] = []
    if removals.casks:
        try:
            run(["brew", "uninstall", "--cask", *removals.casks], env=env)
        except CommandError as error:
            failures.append(str(error))
    if removals.formulae:
        try:
            run(["brew", "uninstall", "--formula", *removals.formulae], env=env)
        except CommandError as error:
            failures.append(str(error))
    if removals.taps:
        try:
            run(["brew", "untap", *removals.taps], env=env)
        except CommandError as error:
            failures.append(str(error))
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    return 0


def cleanup(*, profile: str, confirmed: bool, dry_run: bool, root: Path = REPO_ROOT) -> int:
    if not confirmed and not dry_run:
        print("error: --dry-run or --confirm is required", file=sys.stderr)
        return 64
    if platform.system() != "Darwin":
        print("This task only supports macOS.", file=sys.stderr)
        return 1
    if not command_exists("brew"):
        print("error: Homebrew is required to clean undeclared packages", file=sys.stderr)
        return 1

    keep = load_declared_keep_set(root, profile)
    if not keep.formulae and not keep.casks:
        print("error: declared Homebrew keep-set is empty", file=sys.stderr)
        return 2

    print(
        "keep-set: "
        f"{len(keep.formulae)} formula(e), {len(keep.casks)} cask(s), "
        f"{len(keep.taps)} tap(s)"
    )
    try:
        inventory = read_inventory(keep)
        removals = removals_from_inventory(keep, inventory)
    except CommandError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    if removals.empty():
        print("no undeclared Homebrew formulae, casks, or taps")
        return 0
    _print_removals(removals, dry_run=dry_run or not confirmed)
    if dry_run:
        return 0
    return _uninstall(removals)
