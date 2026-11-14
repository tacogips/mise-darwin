from __future__ import annotations

import unittest
from io import StringIO
from unittest.mock import patch

from scripts.mise_darwin import REPO_ROOT
from scripts.mise_darwin.brew_cleanup import (
    Inventory,
    KeepSet,
    brew_packages_from_toml,
    cleanup,
    load_declared_keep_set,
    merge_keep_sets,
    parse_brewfile,
    removals_from_inventory,
    render_brewfile,
    taps_from_toml,
    undeclared,
)


class TomlKeepSetTests(unittest.TestCase):
    def test_brew_packages_from_toml_skip_mas_entries(self) -> None:
        text = """
[bootstrap.packages]
"brew:fish" = "latest"
"brew:file-formula" = "latest"
"mas:497799835" = "latest"
"""
        self.assertEqual(brew_packages_from_toml(text), ("file-formula", "fish"))

    def test_taps_from_toml_keeps_clone_urls(self) -> None:
        text = """
[bootstrap.brew.taps]
"tacogips/tap" = "https://github.com/tacogips/homebrew-tap.git"
"nikitabobko/tap" = "https://github.com/nikitabobko/homebrew-tap.git"
"""
        taps = taps_from_toml(text)
        self.assertEqual(
            taps,
            (
                ("nikitabobko/tap", "https://github.com/nikitabobko/homebrew-tap.git"),
                ("tacogips/tap", "https://github.com/tacogips/homebrew-tap.git"),
            ),
        )


class BrewfileParserTests(unittest.TestCase):
    def test_parse_brewfile_reads_taps_formulae_and_casks(self) -> None:
        text = """
# comment
tap "tacogips/tap"
tap "slp/krunkit", "https://example.invalid/krunkit.git"
brew "tacogips/tap/ign"
cask "ghostty"
cask "font-jetbrains-mono"
mas "Xcode", id: 497799835
vscode "unused"
"""
        keep = parse_brewfile(text)
        self.assertEqual(
            keep.taps,
            (
                ("slp/krunkit", "https://example.invalid/krunkit.git"),
                ("tacogips/tap", None),
            ),
        )
        self.assertEqual(keep.formulae, ("tacogips/tap/ign",))
        self.assertEqual(keep.casks, ("font-jetbrains-mono", "ghostty"))


class MergeAndRenderTests(unittest.TestCase):
    def test_merge_keep_sets_prefers_tap_url(self) -> None:
        first = KeepSet(taps=(("tacogips/tap", None),), formulae=("fish",))
        second = KeepSet(
            taps=(("tacogips/tap", "https://github.com/tacogips/homebrew-tap.git"),),
            casks=("ghostty",),
        )
        merged = merge_keep_sets(first, second)
        self.assertEqual(
            merged.taps,
            (("tacogips/tap", "https://github.com/tacogips/homebrew-tap.git"),),
        )
        self.assertEqual(merged.formulae, ("fish",))
        self.assertEqual(merged.casks, ("ghostty",))

    def test_render_brewfile_marks_third_party_entries_trusted(self) -> None:
        keep = KeepSet(
            taps=(
                ("homebrew/core", None),
                ("tacogips/tap", "https://github.com/tacogips/homebrew-tap.git"),
            ),
            formulae=("fish", "tacogips/tap/ign"),
            casks=("ghostty", "nikitabobko/tap/aerospace"),
        )
        rendered = render_brewfile(keep)
        self.assertIn('tap "homebrew/core"\n', rendered)
        self.assertIn(
            'tap "tacogips/tap", "https://github.com/tacogips/homebrew-tap.git", trusted: true\n',
            rendered,
        )
        self.assertIn('brew "fish"\n', rendered)
        self.assertIn('brew "tacogips/tap/ign", trusted: true\n', rendered)
        self.assertIn('cask "ghostty"\n', rendered)
        self.assertIn('cask "nikitabobko/tap/aerospace", trusted: true\n', rendered)


class RepositoryKeepSetTests(unittest.TestCase):
    def test_desktop_keep_set_includes_mise_formulae_and_brewfile_casks(self) -> None:
        keep = load_declared_keep_set(REPO_ROOT, "desktop")
        self.assertIn("fish", keep.formulae)
        self.assertIn("file-formula", keep.formulae)
        self.assertIn("tacogips/tap/ign", keep.formulae)
        self.assertIn("ghostty", keep.casks)
        self.assertIn("font-jetbrains-mono", keep.casks)
        tap_names = {name for name, _ in keep.taps}
        self.assertIn("tacogips/tap", tap_names)
        self.assertNotIn("go", keep.formulae)


class RemovalTests(unittest.TestCase):
    def test_undeclared_matches_bare_and_fully_qualified_names(self) -> None:
        extras = undeclared(
            ("homebrew/core/wget", "jq", "extra"),
            frozenset({"wget", "jq"}),
        )
        self.assertEqual(extras, ("extra",))

    def test_removals_keep_declared_packages_and_dependencies(self) -> None:
        keep = KeepSet(
            taps=(("tacogips/tap", None),),
            formulae=("fish",),
            casks=("ghostty",),
        )
        inventory = Inventory(
            formulae=("fish", "pcre2", "wget", "tacogips/tap/mail-gateway-draft"),
            casks=("ghostty", "extra-cask"),
            taps=("tacogips/tap", "homebrew/core", "unused/tap"),
            formula_dependencies=("pcre2",),
        )
        removals = removals_from_inventory(keep, inventory)
        self.assertEqual(removals.formulae, ("tacogips/tap/mail-gateway-draft", "wget"))
        self.assertEqual(removals.casks, ("extra-cask",))
        self.assertEqual(removals.taps, ("unused/tap",))


class CleanupCommandTests(unittest.TestCase):
    def test_cleanup_requires_dry_run_or_confirm(self) -> None:
        with patch("scripts.mise_darwin.brew_cleanup.platform.system", return_value="Darwin"):
            status = cleanup(profile="desktop", confirmed=False, dry_run=False)
        self.assertEqual(status, 64)

    def test_cleanup_dry_run_lists_extras_without_uninstalling(self) -> None:
        inventory = Inventory(
            formulae=("zzz-extra-formula",),
            casks=("zzz-extra-cask",),
            taps=("unused/tap",),
        )
        buffer = StringIO()
        with (
            patch("scripts.mise_darwin.brew_cleanup.platform.system", return_value="Darwin"),
            patch("scripts.mise_darwin.brew_cleanup.command_exists", return_value=True),
            patch("scripts.mise_darwin.brew_cleanup.read_inventory", return_value=inventory),
            patch("scripts.mise_darwin.brew_cleanup._uninstall") as uninstall,
            patch("sys.stdout", buffer),
        ):
            status = cleanup(profile="desktop", confirmed=False, dry_run=True)
        self.assertEqual(status, 0)
        uninstall.assert_not_called()
        output = buffer.getvalue()
        self.assertIn("Would uninstall casks:", output)
        self.assertIn("zzz-extra-cask", output)
        self.assertIn("zzz-extra-formula", output)
        self.assertIn("unused/tap", output)

    def test_cleanup_confirm_uninstalls_extras(self) -> None:
        inventory = Inventory(formulae=("zzz-extra-formula",))
        with (
            patch("scripts.mise_darwin.brew_cleanup.platform.system", return_value="Darwin"),
            patch("scripts.mise_darwin.brew_cleanup.command_exists", return_value=True),
            patch("scripts.mise_darwin.brew_cleanup.read_inventory", return_value=inventory),
            patch("scripts.mise_darwin.brew_cleanup._uninstall", return_value=0) as uninstall,
        ):
            status = cleanup(profile="desktop", confirmed=True, dry_run=False)
        self.assertEqual(status, 0)
        removals = uninstall.call_args.args[0]
        self.assertEqual(removals.formulae, ("zzz-extra-formula",))


if __name__ == "__main__":
    unittest.main()
