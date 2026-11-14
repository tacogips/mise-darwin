from __future__ import annotations

import unittest

from scripts.mise_darwin.aerospace_sync import (
    Monitor,
    fallback_workspace,
    parse_monitors,
    workspace_targets,
)


class AeroSpaceSyncTests(unittest.TestCase):
    def test_two_displays_use_one_digit_external_and_builtin_workspaces(self) -> None:
        monitors = parse_monitors("1|Built-in Retina Display\n2|Studio Display\n")

        self.assertEqual(workspace_targets(monitors), {"9": "1", "1": "2", "2": "2"})

    def test_three_displays_assign_each_external_a_one_digit_workspace(self) -> None:
        monitors = [
            Monitor("1", "Built-in Retina Display"),
            Monitor("2", "Left Display"),
            Monitor("3", "Right Display"),
        ]

        targets = workspace_targets(monitors)

        self.assertEqual(targets, {"9": "1", "1": "2", "2": "3"})
        self.assertEqual(fallback_workspace("2", targets), "1")
        self.assertEqual(fallback_workspace("3", targets), "2")

    def test_external_only_display_still_gets_workspaces_one_and_two(self) -> None:
        self.assertEqual(
            workspace_targets([Monitor("4", "Studio Display")]),
            {"1": "4", "2": "4"},
        )


if __name__ == "__main__":
    unittest.main()
