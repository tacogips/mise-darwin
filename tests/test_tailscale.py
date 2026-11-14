from __future__ import annotations

import plistlib
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, call, patch

from scripts.mise_darwin import tailscale


def result(stdout: str = "", returncode: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess([], returncode, stdout, "")


class TailscaleTests(unittest.TestCase):
    @patch("scripts.mise_darwin.tailscale.run")
    def test_ownership_repair_rejects_unrelated_opt_or_linked_cellar(self, run: Mock) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cellar = root / "cellar"
            cellar.mkdir()
            opt = root / "opt"
            opt.symlink_to(root / "unrelated")
            with self.assertRaises(RuntimeError):
                tailscale.restore_formula_ownership(cellar=cellar, opt=opt)
            opt.unlink()
            opt.write_text("user data", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                tailscale.restore_formula_ownership(cellar=cellar, opt=opt)
            cellar.rmdir()
            cellar.symlink_to(root)
            with self.assertRaises(RuntimeError):
                tailscale.restore_formula_ownership(cellar=cellar, opt=opt)
            run.assert_not_called()

    def test_validate_daemon_rejects_customized_or_symlinked_targets(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "sh.brew.tailscale.plist"
            valid = {
                "Label": "sh.brew.tailscale",
                "ProgramArguments": ["/opt/homebrew/opt/tailscale/bin/tailscaled"],
            }
            path.write_bytes(plistlib.dumps(valid))
            tailscale.validate_daemon(path, "sh.brew.tailscale")
            for change in (
                {"Label": "unrelated"},
                {"ProgramArguments": ["/usr/local/bin/tailscaled"]},
                {"ProgramArguments": [*valid["ProgramArguments"], "--state=custom"]},
                {"Program": "/usr/local/bin/unrelated"},
            ):
                path.write_bytes(plistlib.dumps({**valid, **change}))
                with self.assertRaises(RuntimeError):
                    tailscale.validate_daemon(path, "sh.brew.tailscale")
            path.unlink()
            target = Path(temporary) / "target"
            target.write_bytes(plistlib.dumps(valid))
            path.symlink_to(target)
            with self.assertRaises(RuntimeError):
                tailscale.validate_daemon(path, "sh.brew.tailscale")

    @patch("scripts.mise_darwin.tailscale.run")
    def test_current_policies_are_not_written(self, run: Mock) -> None:
        run.side_effect = [result("1\n"), result("never\n")]
        tailscale.configure_policies(Path("/example"))
        self.assertTrue(all(item.args[0][1] == "read" for item in run.call_args_list))

    @patch("scripts.mise_darwin.tailscale.run")
    def test_only_drifted_policy_is_written_using_explicit_path(self, run: Mock) -> None:
        run.side_effect = [result("1\n"), result("always\n"), result()]
        tailscale.configure_policies(Path("/example"))
        run.assert_called_with([
            "defaults", "write", "/example/Library/Preferences/io.tailscale.ipn.macsys.plist",
            "AllowIncomingConnections", "-string", "never",
        ])

    @patch("scripts.mise_darwin.tailscale.run")
    def test_policy_dry_run_has_no_writes(self, run: Mock) -> None:
        run.return_value = result(returncode=1)
        tailscale.configure_policies(Path("/example"), dry_run=True)
        self.assertEqual(run.call_count, 2)
        self.assertTrue(all(item.args[0][1] == "read" for item in run.call_args_list))

    @patch("scripts.mise_darwin.tailscale.restore_formula_ownership")
    @patch("scripts.mise_darwin.tailscale.run")
    def test_user_daemon_is_backed_up_and_stopped_before_formula_removal(
        self, run: Mock, restore_ownership: Mock
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            path = home / "Library/LaunchAgents/homebrew.mxcl.tailscale.plist"
            path.parent.mkdir(parents=True)
            path.write_bytes(plistlib.dumps({
                "Label": "homebrew.mxcl.tailscale",
                "ProgramArguments": ["/opt/homebrew/opt/tailscale/bin/tailscaled"],
            }))
            run.return_value = result()
            tailscale.retire_daemons(home, system_directory=home / "system")
            commands = [item.args[0] for item in run.call_args_list]
            self.assertEqual(commands[0][:3], ["/bin/cp", "-p", str(path)])
            self.assertIn(".mise-darwin-backup-", commands[0][3])
            self.assertEqual(commands[2][0:2], ["launchctl", "bootout"])
            self.assertEqual(commands[3], ["/bin/rm", str(path)])
            self.assertEqual(commands[-1], ["brew", "uninstall", "--formula", "tailscale"])
            restore_ownership.assert_called_once_with(dry_run=False)

    @patch("scripts.mise_darwin.tailscale.run")
    def test_failed_service_stop_prevents_removal(self, run: Mock) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            path = home / "Library/LaunchAgents/homebrew.mxcl.tailscale.plist"
            path.parent.mkdir(parents=True)
            path.write_bytes(plistlib.dumps({
                "Label": "homebrew.mxcl.tailscale",
                "ProgramArguments": ["/opt/homebrew/opt/tailscale/bin/tailscaled"],
            }))
            run.side_effect = [result(), result(), RuntimeError("stop failed")]
            with self.assertRaises(RuntimeError):
                tailscale.retire_daemons(home, system_directory=home / "system")
            self.assertTrue(path.is_file())
            self.assertFalse(any(item.args[0][0] == "/bin/rm" for item in run.call_args_list))

    def test_cli_preserves_unmanaged_files_and_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            launcher = home / ".local/bin/tailscale"
            launcher.parent.mkdir(parents=True)
            launcher.write_text("unrelated user data", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                tailscale.install_cli(home)
            self.assertEqual(launcher.read_text(), "unrelated user data")
            launcher.unlink()
            launcher.symlink_to(home / "missing")
            with self.assertRaises(RuntimeError):
                tailscale.install_cli(home)

    def test_cli_installation_is_idempotent_and_dry_run_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            launcher = home / ".local/bin/tailscale"
            tailscale.install_cli(home, dry_run=True)
            self.assertFalse(launcher.exists())
            tailscale.install_cli(home)
            modified = launcher.stat().st_mtime_ns
            self.assertEqual(launcher.stat().st_mode & 0o777, 0o755)
            self.assertIn("TAILSCALE_BE_CLI='1'", launcher.read_text())
            tailscale.install_cli(home)
            self.assertEqual(launcher.stat().st_mtime_ns, modified)

    @patch("scripts.mise_darwin.tailscale.install_cli")
    @patch("scripts.mise_darwin.tailscale.prepare")
    @patch("scripts.mise_darwin.tailscale.APP")
    @patch("scripts.mise_darwin.tailscale.run")
    def test_installed_running_app_is_not_reinstalled_or_opened(
        self, run: Mock, app: Mock, prepare: Mock, install_cli: Mock
    ) -> None:
        app.is_dir.return_value = True
        run.return_value = result()
        tailscale.apply()
        prepare.assert_called_once()
        install_cli.assert_called_once()
        self.assertEqual(run.call_args_list[:2], [
            call(["brew", "list", "--cask", "tailscale-app"], quiet=True, check=False),
            call(["pgrep", "-x", "Tailscale"], quiet=True, check=False),
        ])
        self.assertEqual(run.call_args_list[2].args[0], [tailscale.APP_CLI, "syspolicy", "reload"])

    @patch("scripts.mise_darwin.tailscale.install_cli")
    @patch("scripts.mise_darwin.tailscale.prepare")
    @patch("scripts.mise_darwin.tailscale.run")
    def test_setup_dry_run_never_installs_or_opens(
        self, run: Mock, prepare: Mock, install_cli: Mock
    ) -> None:
        run.return_value = result(returncode=1)
        tailscale.apply(dry_run=True)
        self.assertEqual(run.call_count, 2)
        prepare.assert_called_once_with(Path.home(), dry_run=True)
        install_cli.assert_called_once_with(Path.home(), dry_run=True)


if __name__ == "__main__":
    unittest.main()
