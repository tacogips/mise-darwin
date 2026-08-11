from __future__ import annotations

import json
import plistlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from scripts.mise_darwin.bootstrap import (
    AEROSPACE_AGENT_LABEL,
    BAT_THEME,
    DOCKER_PLUGIN_DIRS,
    converge_bat_theme_cache,
    converge_aerospace_sync,
    converge_docker_config,
)


class BootstrapTests(unittest.TestCase):
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
