from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from scripts.mise_darwin import temporary_tool
from scripts.mise_darwin.temporary_tool import HttpTool, install


class TemporaryToolTests(unittest.TestCase):
    def tool(self) -> HttpTool:
        return HttpTool(
            name="example",
            version="1.2.3",
            url="https://example.com/example-1.2.3.tar.gz",
            sha256="a" * 64,
            executable="bin/example",
            bin_path="bin",
        )

    def test_validation_rejects_path_traversal(self) -> None:
        tool = self.tool()
        invalid = HttpTool(**{**tool.__dict__, "executable": "../example"})

        with self.assertRaisesRegex(ValueError, "safe relative path"):
            invalid.validated()

    def test_mise_spec_contains_pinned_url_checksum_and_bin_path(self) -> None:
        self.assertEqual(
            self.tool().mise_spec,
            "http:example["
            "url=https://example.com/example-1.2.3.tar.gz,"
            f"checksum=sha256:{'a' * 64},bin_path=bin]@1.2.3",
        )

    def test_dmg_url_selects_dmg_extraction(self) -> None:
        tool = HttpTool(
            **{
                **self.tool().__dict__,
                "url": "https://example.com/example.dmg",
            }
        )

        self.assertEqual(tool.validated().resolved_format, "dmg")

    def test_dmg_install_rejects_non_macos_host(self) -> None:
        tool = HttpTool(
            **{
                **self.tool().__dict__,
                "url": "https://example.com/example.dmg",
            }
        )

        with patch("scripts.mise_darwin.temporary_tool.sys.platform", "linux"):
            with self.assertRaisesRegex(RuntimeError, "only on macOS"):
                install(tool, dry_run=True)

    def test_install_reuses_matching_managed_destination(self) -> None:
        tool = self.tool().validated()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            destination = root / f"example-{tool.cache_key}"
            executable = destination / tool.executable
            executable.parent.mkdir(parents=True)
            destination.chmod(0o700)
            executable.write_text("#!/bin/sh\n", encoding="utf-8")
            executable.chmod(0o755)
            (destination / temporary_tool.MARKER_NAME).write_text(
                tool.marker_content, encoding="utf-8"
            )

            with (
                patch.object(temporary_tool, "TEMPORARY_TOOL_ROOT", root),
                patch("scripts.mise_darwin.temporary_tool.run") as run,
            ):
                self.assertEqual(install(tool), executable)

            run.assert_not_called()

    def test_install_refuses_unmanaged_destination(self) -> None:
        tool = self.tool().validated()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            destination = root / f"example-{tool.cache_key}"
            destination.mkdir()

            with patch.object(temporary_tool, "TEMPORARY_TOOL_ROOT", root):
                with self.assertRaisesRegex(RuntimeError, "unmanaged temporary path"):
                    install(tool)

    def test_install_uses_mise_install_into_and_marks_destination(self) -> None:
        tool = self.tool().validated()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)

            def fake_run(
                arguments: list[str | os.PathLike[str]], **_kwargs: object
            ) -> Mock:
                staging = Path(arguments[-1])
                executable = staging / tool.executable
                executable.parent.mkdir(parents=True)
                executable.write_text("#!/bin/sh\n", encoding="utf-8")
                executable.chmod(0o755)
                return Mock(returncode=0)

            with (
                patch.object(temporary_tool, "TEMPORARY_TOOL_ROOT", root),
                patch(
                    "scripts.mise_darwin.temporary_tool.run", side_effect=fake_run
                ) as run,
            ):
                executable = install(tool)

            destination = root / f"example-{tool.cache_key}"
            self.assertEqual(executable, destination / tool.executable)
            self.assertEqual(
                json.loads((destination / temporary_tool.MARKER_NAME).read_text()),
                json.loads(tool.marker_content),
            )
            arguments = run.call_args.args[0]
            self.assertEqual(arguments[:3], ["mise", "install-into", "--yes"])
            self.assertEqual(arguments[3], tool.mise_spec)


if __name__ == "__main__":
    unittest.main()
