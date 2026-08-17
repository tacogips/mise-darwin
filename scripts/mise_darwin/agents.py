"""Synchronize explicitly managed agent assets without deleting user content."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from . import REPO_ROOT
from .command import atomic_write, sync_directory, sync_file

LEGACY_CLAUDE_COMMANDS = (
    "add-local-command.md",
    "add-local-subagent.md",
    "cc.md",
    "commit-diff.md",
    "cont-handover.md",
    "eng.md",
    "handover.md",
    "output-design.md",
    "read-commit-logs.md",
    "reload.md",
    "show-github-url.md",
)

USER_SKILL_ROUTER = "user-skill-router"


@dataclass(frozen=True)
class AgentPaths:
    """Agent configuration roots derived from a single home directory."""

    home: Path

    @property
    def shared_skills(self) -> Path:
        return self.home / ".agents/skills"

    @property
    def codex_skills(self) -> Path:
        return self.home / ".codex/skills"

    @property
    def claude_commands(self) -> Path:
        return self.home / ".claude/commands"

    @property
    def claude_skills(self) -> Path:
        return self.home / ".claude/skills"

    @property
    def cursor_config(self) -> Path:
        return self.home / ".cursor/cli-config.json"

    @property
    def cursor_mcp_config(self) -> Path:
        return self.home / ".cursor/mcp.json"

    @property
    def cursor_skills(self) -> Path:
        return self.home / ".cursor/skills"


def _set_implicit_invocation(skill: Path, *, allowed: bool) -> None:
    metadata = skill / "agents/openai.yaml"
    try:
        content = metadata.read_text(encoding="utf-8")
    except FileNotFoundError:
        content = ""

    value = "true" if allowed else "false"
    key_pattern = re.compile(
        r"(?m)^([ \t]*allow_implicit_invocation:[ \t]*)(?:true|false)[ \t]*$"
    )
    if key_pattern.search(content):
        updated = key_pattern.sub(rf"\g<1>{value}", content, count=1)
    elif re.search(r"(?m)^policy:\s*$", content):
        updated = re.sub(
            r"(?m)^policy:\s*$",
            f"policy:\n  allow_implicit_invocation: {value}",
            content,
            count=1,
        )
    else:
        prefix = f"{content.rstrip()}\n\n" if content.strip() else ""
        updated = f"{prefix}policy:\n  allow_implicit_invocation: {value}\n"

    if updated != content:
        atomic_write(metadata, updated, mode=0o644)


def converge_codex_skill_visibility(home: Path | None = None) -> None:
    """Keep one user-skill router implicit and all detailed user skills explicit."""

    paths = AgentPaths(home or Path.home())
    for root in (paths.shared_skills, paths.codex_skills):
        if not root.is_dir():
            continue
        for skill in sorted(root.iterdir()):
            if not skill.is_dir() or not (skill / "SKILL.md").is_file():
                continue
            _set_implicit_invocation(skill, allowed=skill.name == USER_SKILL_ROUTER)


def install(*, profile: str, home: Path | None = None) -> None:
    home = home or Path.home()
    paths = AgentPaths(home)
    source_root = REPO_ROOT / "agent-user-scope"

    for source in sorted((source_root / "agents/skills").iterdir()):
        if source.is_dir():
            sync_directory(source, paths.shared_skills / source.name)

    sync_directory(
        source_root / "agents/skills/wrike-via-gateway",
        paths.claude_skills / "wrike-via-gateway",
    )

    for source in sorted((source_root / "claude/commands").glob("*.md")):
        sync_file(source, paths.claude_commands / source.name)

    for name in LEGACY_CLAUDE_COMMANDS:
        path = paths.claude_commands / name
        if path.is_symlink() and os.readlink(path).startswith("/nix/store/"):
            path.unlink()

    for source in sorted((source_root / "claude/skills").iterdir()):
        if source.is_dir():
            sync_directory(source, paths.claude_skills / source.name)

    sync_file(source_root / "cursor/cli-config.json", paths.cursor_config)
    if profile == "desktop":
        sync_file(source_root / "cursor/mcp.json", paths.cursor_mcp_config)
        sync_directory(
            source_root / "cursor/skills/peekaboo",
            paths.cursor_skills / "peekaboo",
        )
