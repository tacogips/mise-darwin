"""Human-readable host verification with structured checks."""

from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from . import REPO_ROOT, agents, wallpaper
from .command import manifest_lines, run


@dataclass(frozen=True)
class CheckResult:
    ok: bool
    detail: str = ""


Check = Callable[[], CheckResult]


def command_check(*arguments: str) -> Check:
    def check() -> CheckResult:
        result = run(arguments, capture=True, check=False)
        detail = (result.stderr or result.stdout).strip().splitlines()
        return CheckResult(result.returncode == 0, detail[-1] if detail else "")

    return check


def executable_check(name: str) -> Check:
    return lambda: CheckResult(shutil.which(name) is not None, f"{name} not found on PATH")


def path_check(path: Path, *, kind: str = "exists") -> Check:
    predicates = {
        "exists": path.exists,
        "file": path.is_file,
        "symlink": path.is_symlink,
    }

    def check() -> CheckResult:
        ok = predicates[kind]()
        return CheckResult(ok, f"missing {kind}: {path}")

    return check


def value_check(actual: Callable[[], str], expected: str) -> Check:
    def check() -> CheckResult:
        value = actual()
        return CheckResult(value == expected, f"expected {expected!r}, got {value!r}")

    return check


def not_nix_symlink(path: Path) -> Check:
    def check() -> CheckResult:
        if not path.is_symlink():
            return CheckResult(True)
        target = os.readlink(path)
        return CheckResult(not target.startswith("/nix/store/"), f"still points to {target}")

    return check


def herdr_integration(target: str) -> Check:
    def check() -> CheckResult:
        result = run(["herdr", "integration", "status"], capture=True, check=False)
        current = any(
            line.startswith(f"{target}: current ") for line in result.stdout.splitlines()
        )
        return CheckResult(current, f"{target} integration is not current")

    return check


def wallpaper_check() -> CheckResult:
    target = wallpaper.WALLPAPER.resolve(strict=True)
    current = wallpaper.desktop_pictures()
    ok = bool(current) and all(path.resolve(strict=False) == target for path in current)
    return CheckResult(ok, "managed wallpaper is not set on every desktop")


def _checks(profile: str, home: Path) -> list[tuple[str, Check]]:
    agent_paths = agents.AgentPaths(home)
    checks: list[tuple[str, Check]] = [
        ("mise config", command_check("mise", "config", "ls")),
        ("mise doctor", command_check("mise", "doctor")),
        ("fish", executable_check("fish")),
        ("neovim", executable_check("nvim")),
        ("git", executable_check("git")),
        ("ripgrep", executable_check("rg")),
        ("jq", executable_check("jq")),
        ("Herdr Claude integration", herdr_integration("claude")),
        ("Herdr Codex integration", herdr_integration("codex")),
        ("dotfile: nvim", path_check(home / ".config/nvim/init.lua")),
        ("dotfile: fish", path_check(home / ".config/fish/config.fish")),
        ("dotfile: git", path_check(home / ".gitconfig")),
        ("dotfile: lazydocker", path_check(home / ".config/lazydocker/config.yml")),
        ("dotfile: jj", path_check(home / ".config/jj/config.toml")),
        (
            "fish: GitHub token helper",
            path_check(home / ".config/fish/functions/gh-token-save-shared.fish", kind="file"),
        ),
        (
            "agent skill: secure GitHub Actions",
            path_check(
                agent_paths.shared_skills / "secure-github-action/SKILL.md", kind="file"
            ),
        ),
        (
            "agent skill: diagram design",
            path_check(
                agent_paths.shared_skills / "diagram-design/SKILL.md", kind="file"
            ),
        ),
        (
            "agent skill: Wrike Gateway",
            path_check(
                agent_paths.shared_skills / "wrike-via-gateway/SKILL.md", kind="file"
            ),
        ),
        (
            "agent skill: user skill router",
            path_check(
                agent_paths.shared_skills / "user-skill-router/SKILL.md", kind="file"
            ),
        ),
        (
            "Claude user command",
            path_check(
                agent_paths.claude_commands / "user-git-create-pr.md", kind="file"
            ),
        ),
        (
            "Claude Wrike Gateway skill",
            path_check(
                agent_paths.claude_skills / "wrike-via-gateway/SKILL.md", kind="file"
            ),
        ),
        ("Cursor CLI config", path_check(agent_paths.cursor_config, kind="file")),
        ("Cursor config ownership", not_nix_symlink(agent_paths.cursor_config)),
    ]

    if profile == "desktop":
        checks.extend(
            [
                ("desktop wallpaper", wallpaper_check),
                ("riela", executable_check("riela")),
                (
                    "Riela Codex user skill",
                    path_check(
                        agent_paths.codex_skills / "fable-and-improve-codex/SKILL.md",
                        kind="file",
                    ),
                ),
                (
                    "Riela Claude user skill",
                    path_check(
                        agent_paths.claude_skills / "fable-and-improve-codex/SKILL.md",
                        kind="file",
                    ),
                ),
                (
                    "Cursor Peekaboo skill",
                    path_check(
                        agent_paths.cursor_skills / "peekaboo/SKILL.md", kind="file"
                    ),
                ),
                (
                    "AeroSpace display synchronizer",
                    path_check(home / ".local/bin/aerospace-display-sync", kind="file"),
                ),
                (
                    "AeroSpace display LaunchAgent",
                    path_check(
                        home
                        / "Library/LaunchAgents/com.taco.aerospace-display-sync.plist",
                        kind="file",
                    ),
                ),
            ]
        )
        manifest = REPO_ROOT / "agent-user-scope/riela-packages.txt"
        for package_id in manifest_lines(manifest):
            checks.append(
                (
                    f"Riela package: {package_id}",
                    path_check(home / ".riela/packages" / package_id / "riela-package.json", kind="file"),
                )
            )

    developer_dir = Path("/Applications/Xcode.app/Contents/Developer")
    if developer_dir.is_dir():
        checks.extend(
            [
                (
                    "Xcode selection",
                    value_check(
                        lambda: run(["xcode-select", "-p"], capture=True).stdout.strip(),
                        str(developer_dir),
                    ),
                ),
                ("Swift", command_check("xcrun", "--find", "swift")),
                ("sourcekit-lsp", command_check("xcrun", "--find", "sourcekit-lsp")),
            ]
        )

    if profile == "home-server":
        checks.extend(
            [
                (
                    "home-server config",
                    path_check(Path("/etc/darwin-mac-home-server/compose.yaml"), kind="file"),
                ),
                (
                    "home-server workspace",
                    path_check(home / "home-server/compose.yaml", kind="symlink"),
                ),
            ]
        )
    return checks


def verify(profile: str, *, home: Path | None = None) -> bool:
    failures = 0
    for label, check in _checks(profile, home or Path.home()):
        try:
            result = check()
        except Exception as error:  # Keep all checks visible in one run.
            result = CheckResult(False, str(error))
        if result.ok:
            print(f"ok  {label}")
        else:
            suffix = f" ({result.detail})" if result.detail else ""
            print(f"ERR {label}{suffix}", file=sys.stderr)
            failures += 1

    if failures:
        print(f"{failures} verification check(s) failed", file=sys.stderr)
        return False
    print(f"mise-darwin verification passed for profile: {profile}")
    return True
