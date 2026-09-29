from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.mise_darwin.agents import (
    AgentPaths,
    converge_codex_skill_visibility,
    refresh_skills,
)


class AgentPathsTests(unittest.TestCase):
    def test_roots_are_derived_from_home(self) -> None:
        home = Path("/example/home")
        paths = AgentPaths(home)

        self.assertEqual(paths.legacy_shared_skills, home / ".agents/skills")
        self.assertEqual(paths.skills("claude"), home / ".claude/skills")
        self.assertEqual(paths.skills("codex"), home / ".codex/skills")
        self.assertEqual(paths.codex_skills, home / ".codex/skills")
        self.assertEqual(paths.claude_skills, home / ".claude/skills")
        self.assertEqual(paths.cursor_skills, home / ".cursor/skills")


class CodexSkillVisibilityTests(unittest.TestCase):
    def _write_skill(self, root: Path, name: str, metadata: str = "") -> Path:
        skill = root / name
        (skill / "agents").mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: Test skill.\n---\n",
            encoding="utf-8",
        )
        if metadata:
            (skill / "agents/openai.yaml").write_text(metadata, encoding="utf-8")
        return skill

    def test_only_router_remains_implicitly_invocable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            codex = home / ".codex/skills"
            router = self._write_skill(
                codex,
                "user-skill-router",
                'interface:\n  display_name: "Router"\n',
            )
            apple = self._write_skill(
                codex,
                "apple-calendar",
                'interface:\n  display_name: "Calendar"\n',
            )
            riela = self._write_skill(
                codex,
                "riela-workflow",
                "policy:\n  allow_implicit_invocation: true\n",
            )
            unconfigured = self._write_skill(codex, "unconfigured-skill")

            converge_codex_skill_visibility(home)
            converge_codex_skill_visibility(home)

            self.assertIn(
                "allow_implicit_invocation: true",
                (router / "agents/openai.yaml").read_text(encoding="utf-8"),
            )
            apple_metadata = (apple / "agents/openai.yaml").read_text(encoding="utf-8")
            self.assertIn('display_name: "Calendar"', apple_metadata)
            self.assertEqual(apple_metadata.count("allow_implicit_invocation"), 1)
            self.assertIn("allow_implicit_invocation: false", apple_metadata)
            self.assertEqual(
                (riela / "agents/openai.yaml")
                .read_text(encoding="utf-8")
                .count("allow_implicit_invocation"),
                1,
            )
            self.assertIn(
                "allow_implicit_invocation: false",
                (riela / "agents/openai.yaml").read_text(encoding="utf-8"),
            )
            self.assertEqual(
                (unconfigured / "agents/openai.yaml").read_text(encoding="utf-8"),
                "policy:\n  allow_implicit_invocation: false\n",
            )


if __name__ == "__main__":
    unittest.main()


class RefreshSkillsTests(unittest.TestCase):
    def _skill(self, root: Path, name: str, body: str = "managed") -> Path:
        skill = root / name
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(f"---\nname: {name}\n---\n{body}\n", encoding="utf-8")
        return skill

    def _package(self, home: Path, package_id: str, skills: dict[str, list[str]]) -> None:
        installed = home / ".riela/packages" / package_id
        installed.mkdir(parents=True)
        (installed / "riela-package.json").write_text("{}\n", encoding="utf-8")
        for agent, names in skills.items():
            for name in names:
                self._skill(installed / "skills" / agent, name, body=package_id)

    def _repo(self, root: Path, claude_packages: str, codex_packages: str) -> None:
        for agent, packages in (("claude", claude_packages), ("codex", codex_packages)):
            base = root / "agent-user-scope" / agent
            base.mkdir(parents=True)
            (base / "riela-packages.txt").write_text(packages, encoding="utf-8")
        self._skill(root / "agent-user-scope/claude/skills", "claude-only")
        self._skill(root / "agent-user-scope/codex/skills", "codex-only")

    def test_refresh_clears_roots_and_recreates_agent_specific_skills(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            home = Path(temporary) / "home"
            self._repo(root, "both\nclaude-pkg\n", "both\n")
            self._package(home, "both", {"claude": ["shared-name"], "codex": ["shared-name"]})
            self._package(home, "claude-pkg", {"claude": ["claude-workflow"], "codex": ["leaked"]})
            self._skill(home / ".claude/skills", "stale-claude")
            self._skill(home / ".codex/skills", "stale-codex")
            system = self._skill(home / ".codex/skills/.system", "builtin")
            synced = self._skill(home / ".claude/skills/synced", "account-skill")
            self._skill(home / ".agents/skills", "legacy-shared")

            with patch("scripts.mise_darwin.agents.REPO_ROOT", root):
                refresh_skills(home)

            self.assertEqual(
                sorted(path.name for path in (home / ".claude/skills").iterdir()),
                ["claude-only", "claude-workflow", "shared-name", "synced"],
            )
            self.assertEqual(
                sorted(path.name for path in (home / ".codex/skills").iterdir()),
                [".system", "codex-only", "shared-name"],
            )
            self.assertTrue((system / "SKILL.md").is_file())
            self.assertTrue((synced / "SKILL.md").is_file())
            self.assertFalse((home / ".agents/skills").exists())

    def test_later_package_overrides_earlier_package_skill(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            home = Path(temporary) / "home"
            self._repo(root, "first\nsecond\n", "")
            self._package(home, "first", {"claude": ["riela-workflow"]})
            self._package(home, "second", {"claude": ["riela-workflow"]})

            with patch("scripts.mise_darwin.agents.REPO_ROOT", root):
                refresh_skills(home)

            self.assertIn(
                "second",
                (home / ".claude/skills/riela-workflow/SKILL.md").read_text(encoding="utf-8"),
            )

    def test_package_cannot_shadow_repository_skill(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            home = Path(temporary) / "home"
            self._repo(root, "", "pkg\n")
            self._package(home, "pkg", {"codex": ["codex-only"]})
            stale = self._skill(home / ".codex/skills", "stale-codex")

            with patch("scripts.mise_darwin.agents.REPO_ROOT", root):
                with self.assertRaisesRegex(RuntimeError, "already defines"):
                    refresh_skills(home)

            self.assertTrue(stale.is_dir())
