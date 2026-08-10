from __future__ import annotations

import unittest

from scripts.mise_darwin.nix_uninstall import filter_nix_mount, strip_nix_shell_block


class NixUninstallTests(unittest.TestCase):
    def test_filters_only_nix_fstab_entries(self) -> None:
        content = (
            "LABEL=Nix\\040Store /nix apfs rw 0 0\n"
            "/dev/disk3s1 /Volumes/Data apfs rw 0 0\n"
        )
        self.assertEqual(
            filter_nix_mount(content, synthetic=False),
            "/dev/disk3s1 /Volumes/Data apfs rw 0 0\n",
        )

    def test_filters_only_nix_synthetic_entry(self) -> None:
        self.assertEqual(
            filter_nix_mount("nix\nData\t/Volumes/Data\n", synthetic=True),
            "Data\t/Volumes/Data\n",
        )

    def test_strips_nix_shell_block(self) -> None:
        content = "before\n# Nix\nsource /nix/profile\n# End Nix\nafter\n"
        self.assertEqual(strip_nix_shell_block(content), "before\nafter\n")


if __name__ == "__main__":
    unittest.main()
