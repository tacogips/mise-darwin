from __future__ import annotations

import subprocess
import unittest
from unittest.mock import Mock, patch

from scripts.mise_darwin.temporary_packages import (
    JsonValue,
    MiseTool,
    cask_tool,
    resolve,
    resolve_mise,
    run_package,
)
from scripts.mise_darwin.temporary_tool import HttpTool


class TemporaryPackagesTests(unittest.TestCase):
    def test_cask_tool_extracts_app_metadata(self) -> None:
        payload: dict[str, JsonValue] = {
            "token": "qflipper",
            "version": "1.3.3",
            "url": "https://example.com/qFlipper.dmg",
            "sha256": "a" * 64,
            "artifacts": [{"app": ["qFlipper.app"]}],
        }

        tool = cask_tool(payload)

        self.assertEqual(tool.name, "qflipper")
        self.assertEqual(tool.executable, "qFlipper.app")
        self.assertEqual(tool.launch_kind, "app")
        self.assertEqual(tool.artifact_format, "dmg")

    @patch("scripts.mise_darwin.temporary_packages.run")
    def test_resolve_mise_uses_first_registry_backend_and_latest_version(
        self, run: Mock
    ) -> None:
        run.side_effect = [
            subprocess.CompletedProcess([], 0, "aqua:owner/tool cargo:tool\n", ""),
            subprocess.CompletedProcess([], 0, "1.2.3\n", ""),
        ]

        tool = resolve_mise("tool")

        self.assertEqual(tool, MiseTool("tool", "1.2.3", "aqua:owner/tool"))

    @patch("scripts.mise_darwin.temporary_packages.resolve_cask")
    @patch("scripts.mise_darwin.temporary_packages.resolve_mise", return_value=None)
    def test_unprefixed_package_falls_back_to_cask(
        self, _resolve_mise: Mock, resolve_cask: Mock
    ) -> None:
        expected = HttpTool(
            name="example",
            version="1.0.0",
            url="https://example.com/example.dmg",
            sha256="a" * 64,
            executable="Example.app",
            artifact_format="dmg",
            launch_kind="app",
        )
        resolve_cask.return_value = expected

        self.assertEqual(resolve("example"), expected)
        resolve_cask.assert_called_once_with("example")

    @patch("scripts.mise_darwin.temporary_packages.run_mise_tool", return_value=7)
    @patch("scripts.mise_darwin.temporary_packages.resolve")
    def test_run_package_dispatches_mise_tool(
        self, resolve: Mock, run_mise_tool: Mock
    ) -> None:
        tool = MiseTool("example", "1.0.0", "aqua:owner/example")
        resolve.return_value = tool

        result = run_package("mise:example", ["example", "--version"])

        self.assertEqual(result, 7)
        run_mise_tool.assert_called_once_with(
            tool,
            ["example", "--version"],
            dry_run=False,
            install_only=False,
        )


if __name__ == "__main__":
    unittest.main()
