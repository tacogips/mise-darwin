from __future__ import annotations

import subprocess
import unittest
from unittest.mock import Mock, call, patch

from scripts.mise_darwin.upgrade_taco import tap_packages, upgrade


class UpgradeTacoTests(unittest.TestCase):
    def test_tap_packages_filters_and_sorts_unique_names(self) -> None:
        output = "\n".join(
            [
                "homebrew/core/jq",
                "tacogips/tap/kinko",
                "tacogips/tap/ign",
                "tacogips/tap/kinko",
            ]
        )

        self.assertEqual(
            tap_packages(output),
            ("tacogips/tap/ign", "tacogips/tap/kinko"),
        )

    @patch("scripts.mise_darwin.upgrade_taco.command_exists", return_value=True)
    @patch("scripts.mise_darwin.upgrade_taco.run")
    def test_upgrade_updates_formulae_and_casks_without_confirmation(
        self, run: Mock, _command_exists: Mock
    ) -> None:
        run.side_effect = [
            subprocess.CompletedProcess([], 0, "tacogips/tap/ign\n", ""),
            subprocess.CompletedProcess([], 0, "tacogips/tap/riela\n", ""),
            subprocess.CompletedProcess([], 0, "", ""),
            subprocess.CompletedProcess([], 0, "", ""),
        ]

        upgrade()

        self.assertEqual(
            run.call_args_list,
            [
                call(["brew", "list", "--formula", "--full-name"], capture=True),
                call(["brew", "list", "--cask", "--full-name"], capture=True),
                call(
                    [
                        "brew",
                        "upgrade",
                        "--formula",
                        "--no-ask",
                        "tacogips/tap/ign",
                    ]
                ),
                call(
                    [
                        "brew",
                        "upgrade",
                        "--cask",
                        "--greedy",
                        "--no-ask",
                        "tacogips/tap/riela",
                    ]
                ),
            ],
        )


if __name__ == "__main__":
    unittest.main()
