from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.mise_darwin.agents import AgentPaths, converge_codex_skill_visibility


class AgentPathsTests(unittest.TestCase):
    def test_roots_are_derived_from_home(self) -> None:
        home = Path("/example/home")
        paths = AgentPaths(home)

        self.assertEqual(paths.shared_skills, home / ".agents/skills")
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
            shared = home / ".agents/skills"
            codex = home / ".codex/skills"
            router = self._write_skill(
                shared,
                "user-skill-router",
                'interface:\n  display_name: "Router"\n',
            )
            apple = self._write_skill(
                shared,
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
