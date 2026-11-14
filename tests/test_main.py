from __future__ import annotations

import unittest

from scripts.mise_darwin.__main__ import command_arguments, shell_arguments


class MainTests(unittest.TestCase):
    def test_command_arguments_removes_separator(self) -> None:
        self.assertEqual(command_arguments(["--", "--help"]), ["--help"])

    def test_command_arguments_preserves_regular_arguments(self) -> None:
        self.assertEqual(command_arguments(["--verbose"]), ["--verbose"])

    def test_shell_arguments_accepts_controls_after_package(self) -> None:
        self.assertEqual(
            shell_arguments(
                ["--dry-run", "--install-only"],
                dry_run=False,
                install_only=False,
            ),
            ([], True, True),
        )

    def test_shell_arguments_separator_preserves_command_flags(self) -> None:
        self.assertEqual(
            shell_arguments(
                ["--", "--dry-run"], dry_run=False, install_only=False
            ),
            (["--dry-run"], False, False),
        )

    def test_shell_arguments_removes_separator_after_controls(self) -> None:
        self.assertEqual(
            shell_arguments(
                ["--dry-run", "--", "rg", "--version"],
                dry_run=False,
                install_only=False,
            ),
            (["rg", "--version"], True, False),
        )


if __name__ == "__main__":
    unittest.main()
