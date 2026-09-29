"""Synchronize explicitly managed agent assets.

User-scope skills are owned by this repository: every refresh clears the Claude
Code and Codex skill roots and recreates only the skills defined here plus the
agent-specific skills of the Riela packages listed per agent. Nothing is placed
in the former shared ``~/.agents/skills`` root.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from . import REPO_ROOT
from .command import atomic_write, manifest_lines, remove_path, sync_directory, sync_file

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
SKILL_AGENTS = ("claude", "codex")
# Entries each agent manages itself; a refresh never removes them. Dot-prefixed
# entries (such as Codex's bundled ``.system`` skills) are always kept too.
AGENT_OWNED_SKILL_ENTRIES = {
    "claude": frozenset({"synced"}),  # skills synced from the Claude account
    "codex": frozenset(),
}


@dataclass(frozen=True)
class AgentPaths:
    """Agent configuration roots derived from a single home directory."""

    home: Path

    @property
    def legacy_shared_skills(self) -> Path:
        """Former cross-agent skill root; refresh removes it."""
        return self.home / ".agents/skills"

    @property
    def riela_packages(self) -> Path:
        return self.home / ".riela/packages"

    def skills(self, agent: str) -> Path:
        return {"claude": self.claude_skills, "codex": self.codex_skills}[agent]

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

    root = AgentPaths(home or Path.home()).codex_skills
    if not root.is_dir():
        return
    for skill in sorted(root.iterdir()):
        if skill.name.startswith(".") or not (skill / "SKILL.md").is_file():
            continue
        _set_implicit_invocation(skill, allowed=skill.name == USER_SKILL_ROUTER)


def riela_package_manifest(agent: str) -> Path:
    return REPO_ROOT / "agent-user-scope" / agent / "riela-packages.txt"


def riela_package_ids() -> list[str]:
    """Every Riela package any agent needs, in first-listed order."""

    ids: list[str] = []
    for agent in SKILL_AGENTS:
        for package_id in manifest_lines(riela_package_manifest(agent)):
            if package_id not in ids:
                ids.append(package_id)
    return ids


def skill_sources(agent: str, paths: AgentPaths) -> dict[str, Path]:
    """Map skill name to source directory for one agent.

    Repository skills come first, then each listed Riela package's
    ``skills/<agent>`` directory in manifest order. A later package overrides an
    earlier package that ships the same skill name; a package may never shadow a
    skill defined in this repository.
    """

    sources: dict[str, Path] = {}
    managed = REPO_ROOT / "agent-user-scope" / agent / "skills"
    for source in sorted(managed.iterdir()) if managed.is_dir() else ():
        if (source / "SKILL.md").is_file():
            sources[source.name] = source
    repository_names = set(sources)
    for package_id in manifest_lines(riela_package_manifest(agent)):
        package_skills = paths.riela_packages / package_id / "skills" / agent
        if not (paths.riela_packages / package_id / "riela-package.json").is_file():
            print(f"warning: Riela package {package_id} is not installed; skipping its {agent} skills")
            continue
        for source in sorted(package_skills.iterdir()) if package_skills.is_dir() else ():
            if not (source / "SKILL.md").is_file():
                continue
            if source.name in repository_names or source.name in AGENT_OWNED_SKILL_ENTRIES[agent]:
                raise RuntimeError(
                    f"Riela package {package_id} ships {agent} skill {source.name}, "
                    "which agent-user-scope already defines"
                )
            sources[source.name] = source
    return sources


def refresh_skills(home: Path) -> None:
    """Clear the Claude Code and Codex skill roots, then recreate managed skills.

    Dot-prefixed entries such as Codex's bundled ``.system`` skills and Claude
    Code's account-synced ``synced`` store belong to the agent itself and are
    kept. The legacy shared ``~/.agents/skills`` root is
    removed entirely.
    """

    paths = AgentPaths(home)
    planned = {agent: skill_sources(agent, paths) for agent in SKILL_AGENTS}
    remove_path(paths.legacy_shared_skills)
    for agent in SKILL_AGENTS:
        root = paths.skills(agent)
        root.mkdir(parents=True, exist_ok=True)
        for existing in root.iterdir():
            if existing.name.startswith(".") or existing.name in AGENT_OWNED_SKILL_ENTRIES[agent]:
                continue
            remove_path(existing)
        for name, source in planned[agent].items():
            sync_directory(source, root / name)


def install(*, profile: str, home: Path | None = None) -> None:
    home = home or Path.home()
    paths = AgentPaths(home)
    source_root = REPO_ROOT / "agent-user-scope"

    refresh_skills(home)

    for source in sorted((source_root / "claude/commands").glob("*.md")):
        sync_file(source, paths.claude_commands / source.name)

    for name in LEGACY_CLAUDE_COMMANDS:
        path = paths.claude_commands / name
        if path.is_symlink() and os.readlink(path).startswith("/nix/store/"):
            path.unlink()

    sync_file(source_root / "cursor/cli-config.json", paths.cursor_config)
    if profile == "desktop":
        sync_file(source_root / "cursor/mcp.json", paths.cursor_mcp_config)
        sync_directory(
            source_root / "cursor/skills/peekaboo",
            paths.cursor_skills / "peekaboo",
        )
