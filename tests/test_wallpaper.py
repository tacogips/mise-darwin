from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from scripts.mise_darwin import wallpaper


def result(stdout: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess([], 0, stdout, "")


class WallpaperTests(unittest.TestCase):
    @patch("scripts.mise_darwin.wallpaper.run")
    def test_apply_skips_matching_desktops(self, run: Mock) -> None:
        run.return_value = result(f"{wallpaper.WALLPAPER.resolve()}\n")

        wallpaper.apply()

        run.assert_called_once()

    @patch("scripts.mise_darwin.wallpaper.run")
    def test_apply_updates_drifted_desktops(self, run: Mock) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            previous = Path(temporary) / "previous.jpg"
            run.side_effect = [
                result(f"{previous}\n"),
                result(),
                result(f"{wallpaper.WALLPAPER.resolve()}\n"),
            ]

            wallpaper.apply()

            self.assertEqual(run.call_count, 3)
            setter = run.call_args_list[1].args[0]
            self.assertEqual(setter[-1], wallpaper.WALLPAPER.resolve())


if __name__ == "__main__":
    unittest.main()
