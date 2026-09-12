from __future__ import annotations

import json
import os
import plistlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, call, patch

from scripts.mise_darwin.bootstrap import (
    AEROSPACE_AGENT_LABEL,
    BAT_THEME,
    DOCKER_PLUGIN_DIRS,
    converge_riela_packages,
    converge_riela_cli_quarantine,
    converge_bat_theme_cache,
    converge_aerospace_sync,
    converge_docker_config,
    retire_legacy_codex_riela_skill,
)


class BootstrapTests(unittest.TestCase):
    def _riela_fixture(self, root: Path, home: Path, checkout: Path) -> None:
        manifest = root / "agent-user-scope/riela-packages.txt"
        manifest.parent.mkdir(parents=True)
        manifest.write_text("first\nsecond\n", encoding="utf-8")
        for package_id in ("first", "second"):
            (checkout / "packages" / package_id).mkdir(parents=True)
        for path in (
            home / ".codex/skills/codex-design-and-implement-review-loop/SKILL.md",
            home / ".claude/skills/fable-and-improve-codex/SKILL.md",
            home / ".claude/skills/fable-and-improve-opus/SKILL.md",
        ):
            path.parent.mkdir(parents=True)
            path.write_text("test\n", encoding="utf-8")

    @patch("scripts.mise_darwin.bootstrap.converge_riela_cli_quarantine")
    @patch("scripts.mise_darwin.bootstrap.command_exists", return_value=True)
    @patch("scripts.mise_darwin.bootstrap.run")
    def test_riela_packages_use_update_for_installed_and_install_for_missing(
        self, run: Mock, _command_exists: Mock, _quarantine: Mock
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            home = root / "home"
            checkout = home / "gits/tacogips/riela-packages"
            self._riela_fixture(root, home, checkout)
            (checkout / ".git").mkdir()
            installed_manifest = home / ".riela/packages/first/riela-package.json"
            installed_manifest.parent.mkdir(parents=True)
            installed_manifest.write_text("{}\n", encoding="utf-8")
            with (
                patch("scripts.mise_darwin.bootstrap.REPO_ROOT", root),
                patch.dict(os.environ, {"RIELA_GIT_EXECUTABLE": "/custom/git"}, clear=True),
            ):
                converge_riela_packages(home)

            self.assertEqual(
                run.call_args_list,
                [
                    call(["/custom/git", "-C", checkout, "pull", "--ff-only"]),
                    call(
                        [
                            "riela", "package", "update", "first", "--source",
                            checkout / "packages/first", "--scope", "user", "--output", "json",
                        ],
                        quiet=True,
                    ),
                    call(
                        [
                            "riela", "package", "install", "second", "--source",
                            checkout / "packages/second", "--scope", "user", "--output", "json",
                        ],
                        quiet=True,
                    ),
                ],
            )

    @patch("scripts.mise_darwin.bootstrap.converge_riela_cli_quarantine")
    @patch("scripts.mise_darwin.bootstrap.command_exists", return_value=True)
    @patch("scripts.mise_darwin.bootstrap.run")
    def test_custom_riela_checkout_is_not_pulled(
        self, run: Mock, _command_exists: Mock, _quarantine: Mock
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            home = root / "home"
            checkout = root / "custom-packages"
            self._riela_fixture(root, home, checkout)
            (checkout / ".git").mkdir()
            with (
                patch("scripts.mise_darwin.bootstrap.REPO_ROOT", root),
                patch.dict(os.environ, {"RIELA_PACKAGES_CHECKOUT": str(checkout)}, clear=True),
            ):
                converge_riela_packages(home)

            self.assertEqual(len(run.call_args_list), 2)
            self.assertTrue(all(args.args[0][:3] == ["riela", "package", "install"] for args in run.call_args_list))

    @patch("scripts.mise_darwin.bootstrap.converge_riela_cli_quarantine")
    @patch("scripts.mise_darwin.bootstrap.command_exists", return_value=True)
    @patch("scripts.mise_darwin.bootstrap.run")
    def test_default_riela_checkout_accepts_git_worktree_marker(
        self, run: Mock, _command_exists: Mock, _quarantine: Mock
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            home = root / "home"
            checkout = home / "gits/tacogips/riela-packages"
            self._riela_fixture(root, home, checkout)
            (checkout / ".git").write_text("gitdir: /test/repository/worktrees/packages\n", encoding="utf-8")
            with (
                patch("scripts.mise_darwin.bootstrap.REPO_ROOT", root),
                patch.dict(os.environ, {}, clear=True),
            ):
                converge_riela_packages(home)

            self.assertEqual(run.call_args_list[0], call(["git", "-C", checkout, "pull", "--ff-only"]))
            self.assertEqual(len(run.call_args_list), 3)

    @patch("scripts.mise_darwin.bootstrap.converge_riela_cli_quarantine")
    @patch("scripts.mise_darwin.bootstrap.command_exists", return_value=True)
    @patch("scripts.mise_darwin.bootstrap.run")
    def test_default_riela_checkout_without_git_fails_before_package_changes(
        self, run: Mock, _command_exists: Mock, _quarantine: Mock
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            home = root / "home"
            checkout = home / "gits/tacogips/riela-packages"
            self._riela_fixture(root, home, checkout)
            with (
                patch("scripts.mise_darwin.bootstrap.REPO_ROOT", root),
                patch.dict(os.environ, {}, clear=True),
            ):
                with self.assertRaisesRegex(RuntimeError, "not a Git repository"):
                    converge_riela_packages(home)

            run.assert_not_called()

    @patch("scripts.mise_darwin.bootstrap.run")
    def test_riela_cli_quarantine_is_removed_only_when_present(self, run: Mock) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            cli = Path(temporary) / "riela"
            cli.touch()
            run.return_value = Mock(returncode=0)

            converge_riela_cli_quarantine(cli)

            self.assertEqual(
                run.call_args_list,
                [
                    call(
                        ["xattr", "-p", "com.apple.quarantine", cli],
                        quiet=True,
                        check=False,
                    ),
                    call(
                        ["xattr", "-d", "com.apple.quarantine", cli]
                    ),
                ],
            )

    def test_retire_legacy_codex_riela_skill_preserves_unrelated_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            codex_skills = Path(temporary)
            skill = codex_skills / "fable-and-improve-codex"
            metadata = skill / "agents"
            metadata.mkdir(parents=True)
            (skill / "SKILL.md").write_text("managed\n", encoding="utf-8")
            (metadata / "openai.yaml").write_text("managed\n", encoding="utf-8")
            user_file = skill / "notes.md"
            user_file.write_text("preserve\n", encoding="utf-8")

            retire_legacy_codex_riela_skill(codex_skills)

            self.assertFalse((skill / "SKILL.md").exists())
            self.assertFalse((metadata / "openai.yaml").exists())
            self.assertEqual(user_file.read_text(encoding="utf-8"), "preserve\n")

    @patch("scripts.mise_darwin.bootstrap.run")
    @patch("scripts.mise_darwin.bootstrap.command_exists", return_value=True)
    def test_bat_theme_cache_rebuilds_only_for_changed_theme(
        self, _command_exists: Mock, run: Mock
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)

            converge_bat_theme_cache(home)
            converge_bat_theme_cache(home)

            run.assert_called_once_with(["bat", "cache", "--build"])
            stamp = home / ".cache/mise-darwin/bat-sora.sha256"
            self.assertEqual(len(stamp.read_text(encoding="utf-8").strip()), 64)
            self.assertTrue(BAT_THEME.is_file())

    def test_aerospace_sync_installs_launcher_and_launch_agent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)

            converge_aerospace_sync(home, load_agent=False)

            launcher = home / ".local/bin/aerospace-display-sync"
            agent = home / "Library/LaunchAgents" / f"{AEROSPACE_AGENT_LABEL}.plist"
            self.assertTrue(launcher.stat().st_mode & 0o100)
            payload = plistlib.loads(agent.read_bytes())
            self.assertEqual(payload["ProgramArguments"], [str(launcher)])
            self.assertEqual(payload["StartInterval"], 5)

    def test_docker_config_preserves_other_settings(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            config_path = home / ".docker/config.json"
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                json.dumps({"credsStore": "desktop", "cliPluginsExtraDirs": ["/custom"]}),
                encoding="utf-8",
            )

            converge_docker_config(home)

            config = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual(config["credsStore"], "desktop")
            self.assertEqual(
                config["cliPluginsExtraDirs"],
                sorted(["/custom", *DOCKER_PLUGIN_DIRS]),
            )

    def test_invalid_docker_config_is_replaced(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            config_path = home / ".docker/config.json"
            config_path.parent.mkdir(parents=True)
            config_path.write_text("not json", encoding="utf-8")

            converge_docker_config(home)

            config = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual(config["cliPluginsExtraDirs"], sorted(DOCKER_PLUGIN_DIRS))


if __name__ == "__main__":
    unittest.main()
