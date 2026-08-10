from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.mise_darwin.command import atomic_write, manifest_lines, sync_directory


class CommandTests(unittest.TestCase):
    def test_sync_directory_mirrors_managed_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            target = root / "target"
            (source / "nested").mkdir(parents=True)
            (source / "nested/current.txt").write_text("current", encoding="utf-8")
            (target / "nested").mkdir(parents=True)
            (target / "nested/stale.txt").write_text("stale", encoding="utf-8")

            sync_directory(source, target)

            self.assertEqual((target / "nested/current.txt").read_text(), "current")
            self.assertFalse((target / "nested/stale.txt").exists())

    def test_atomic_write_replaces_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "config.json"
            atomic_write(path, "first\n")
            atomic_write(path, "second\n", mode=0o600)
            self.assertEqual(path.read_text(), "second\n")
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_manifest_lines_ignores_comments_and_empty_lines(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "manifest.txt"
            path.write_text("# comment\n\nfirst\n second \n", encoding="utf-8")
            self.assertEqual(list(manifest_lines(path)), ["first", "second"])


if __name__ == "__main__":
    unittest.main()
