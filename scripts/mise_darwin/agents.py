"""Synchronize explicitly managed agent assets without deleting user content."""

from __future__ import annotations

import os
from pathlib import Path

from . import REPO_ROOT
from .command import sync_directory, sync_file

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


def install(*, profile: str, home: Path | None = None) -> None:
    home = home or Path.home()
    source_root = REPO_ROOT / "agent-user-scope"

    for source in sorted((source_root / "agents/skills").iterdir()):
        if source.is_dir():
            sync_directory(source, home / ".agents/skills" / source.name)

    sync_directory(
        source_root / "agents/skills/wrike-via-gateway",
        home / ".claude/skills/wrike-via-gateway",
    )

    for source in sorted((source_root / "claude/commands").glob("*.md")):
        sync_file(source, home / ".claude/commands" / source.name)

    for name in LEGACY_CLAUDE_COMMANDS:
        path = home / ".claude/commands" / name
        if path.is_symlink() and os.readlink(path).startswith("/nix/store/"):
            path.unlink()

    for source in sorted((source_root / "claude/skills").iterdir()):
        if source.is_dir():
            sync_directory(source, home / ".claude/skills" / source.name)

    sync_file(source_root / "cursor/cli-config.json", home / ".cursor/cli-config.json")
    if profile == "desktop":
        sync_file(source_root / "cursor/mcp.json", home / ".cursor/mcp.json")
        sync_directory(
            source_root / "cursor/skills/peekaboo",
            home / ".cursor/skills/peekaboo",
        )
