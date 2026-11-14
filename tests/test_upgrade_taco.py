from __future__ import annotations

import json
import subprocess
import unittest
from unittest.mock import Mock, call, patch

from scripts.mise_darwin.command import CommandError
from scripts.mise_darwin.upgrade_taco import (
    catalog_names,
    orphan_report,
    partition,
    tap_packages,
    upgrade,
)


def _catalog(formulae: list[str], casks: list[str]) -> str:
    return json.dumps([{"formula_names": formulae, "cask_tokens": casks}])


def _completed(stdout: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess([], 0, stdout, "")


class TapPackagesTests(unittest.TestCase):
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


class CatalogTests(unittest.TestCase):
    def test_catalog_names_splits_formulae_and_casks(self) -> None:
        output = _catalog(["tacogips/tap/ign"], ["tacogips/tap/riela"])

        self.assertEqual(
            catalog_names(output),
            (frozenset({"tacogips/tap/ign"}), frozenset({"tacogips/tap/riela"})),
        )

    def test_catalog_names_tolerates_missing_keys(self) -> None:
        self.assertEqual(
            catalog_names(json.dumps([{}])),
            (frozenset(), frozenset()),
        )


class PartitionTests(unittest.TestCase):
    def test_partition_separates_retired_packages(self) -> None:
        installed = ("tacogips/tap/x-gateway-read", "tacogips/tap/x-gateway-reader")

        known, orphaned = partition(
            installed, frozenset({"tacogips/tap/x-gateway-reader"})
        )

        self.assertEqual(known, ("tacogips/tap/x-gateway-reader",))
        self.assertEqual(orphaned, ("tacogips/tap/x-gateway-read",))

    def test_partition_keeps_everything_when_catalog_is_unavailable(self) -> None:
        installed = ("tacogips/tap/ign", "tacogips/tap/kinko")

        self.assertEqual(partition(installed, frozenset()), (installed, ()))


class OrphanReportTests(unittest.TestCase):
    def test_orphan_report_uses_bare_names_in_the_remedy(self) -> None:
        report = orphan_report(("tacogips/tap/x-gateway-read",), "formula")

        self.assertIn("tacogips/tap/x-gateway-read", report)
        self.assertIn("brew uninstall --formula x-gateway-read", report)


class UpgradeTests(unittest.TestCase):
    @patch("scripts.mise_darwin.upgrade_taco.command_exists", return_value=True)
    @patch("scripts.mise_darwin.upgrade_taco.run")
    def test_upgrade_updates_formulae_and_casks_without_confirmation(
        self, run: Mock, _command_exists: Mock
    ) -> None:
        run.side_effect = [
            _completed(_catalog(["tacogips/tap/ign"], ["tacogips/tap/riela"])),
            _completed("tacogips/tap/ign\n"),
            _completed(),
            _completed("tacogips/tap/riela\n"),
            _completed(),
        ]

        upgrade()

        self.assertEqual(
            run.call_args_list,
            [
                call(["brew", "tap-info", "--json", "tacogips/tap"], capture=True),
                call(["brew", "list", "--formula", "--full-name"], capture=True),
                call(
                    [
                        "brew",
                        "upgrade",
                        "--formula",
                        "--no-ask",
                        "tacogips/tap/ign",
                    ]
                ),
                call(["brew", "list", "--cask", "--full-name"], capture=True),
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

    @patch("scripts.mise_darwin.upgrade_taco.command_exists", return_value=True)
    @patch("scripts.mise_darwin.upgrade_taco.run")
    def test_upgrade_skips_orphans_and_reports_them(
        self, run: Mock, _command_exists: Mock
    ) -> None:
        run.side_effect = [
            _completed(_catalog(["tacogips/tap/x-gateway-reader"], [])),
            _completed("tacogips/tap/x-gateway-read\ntacogips/tap/x-gateway-reader\n"),
            _completed(),
            _completed(""),
        ]

        with patch("builtins.print") as printed:
            upgrade()

        self.assertEqual(
            run.call_args_list[2],
            call(
                [
                    "brew",
                    "upgrade",
                    "--formula",
                    "--no-ask",
                    "tacogips/tap/x-gateway-reader",
                ]
            ),
        )
        report = "\n".join(str(entry.args[0]) for entry in printed.call_args_list)
        self.assertIn("tacogips/tap/x-gateway-read", report)
        self.assertIn("brew uninstall --formula x-gateway-read", report)

    @patch("scripts.mise_darwin.upgrade_taco.command_exists", return_value=True)
    @patch("scripts.mise_darwin.upgrade_taco.run")
    def test_upgrade_runs_casks_even_when_formulae_fail(
        self, run: Mock, _command_exists: Mock
    ) -> None:
        run.side_effect = [
            _completed(_catalog(["tacogips/tap/ign"], ["tacogips/tap/riela"])),
            _completed("tacogips/tap/ign\n"),
            CommandError("command failed (1): brew upgrade --formula"),
            _completed("tacogips/tap/riela\n"),
            _completed(),
        ]

        with self.assertRaises(CommandError):
            upgrade()

        self.assertEqual(
            run.call_args_list[4],
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
        )

    @patch("scripts.mise_darwin.upgrade_taco.command_exists", return_value=True)
    @patch("scripts.mise_darwin.upgrade_taco.run")
    def test_upgrade_falls_back_to_every_package_when_catalog_fails(
        self, run: Mock, _command_exists: Mock
    ) -> None:
        run.side_effect = [
            CommandError("command failed (1): brew tap-info"),
            _completed("tacogips/tap/ign\n"),
            _completed(),
            _completed(""),
        ]

        with patch("builtins.print"):
            upgrade()

        self.assertEqual(
            run.call_args_list[2],
            call(["brew", "upgrade", "--formula", "--no-ask", "tacogips/tap/ign"]),
        )


if __name__ == "__main__":
    unittest.main()
