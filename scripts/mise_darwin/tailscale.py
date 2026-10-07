"""Converge the standalone desktop app without deleting tailnet credentials."""

from __future__ import annotations

import os
import plistlib
import sys
from datetime import datetime
from pathlib import Path

from .command import atomic_write, run

APP = Path("/Applications/Tailscale.app")
APP_CLI = APP / "Contents/MacOS/Tailscale"
CLI_MARKER = "# Managed by mise-darwin: Tailscale desktop CLI."
DAEMON_LABELS = ("sh.brew.tailscale", "homebrew.mxcl.tailscale")
POLICIES = (
    ("TailscaleStartOnLogin", "-bool", "true", "1"),
    ("AllowIncomingConnections", "-string", "never", "never"),
)


def validate_daemon(path: Path, label: str) -> None:
    """Only retire known Homebrew/mise definitions pointing at their formula."""
    if path.name != f"{label}.plist" or path.is_symlink() or not path.is_file():
        raise RuntimeError(f"refusing unexpected Tailscale service path: {path}")
    data = plistlib.loads(path.read_bytes())
    arguments = data.get("ProgramArguments")
    if (
        data.get("Label") != label
        or arguments != ["/opt/homebrew/opt/tailscale/bin/tailscaled"]
        or data.get("Program") not in (None, "/opt/homebrew/opt/tailscale/bin/tailscaled")
    ):
        raise RuntimeError(f"refusing customized Tailscale service: {path}")


def _execute(arguments: list[str], *, dry_run: bool) -> None:
    if dry_run:
        print(f"would run: {arguments!r}")
    else:
        run(arguments)


def restore_formula_ownership(
    *,
    dry_run: bool = False,
    cellar: Path = Path("/opt/homebrew/Cellar/tailscale"),
    opt: Path = Path("/opt/homebrew/opt/tailscale"),
) -> None:
    """Undo sudo service-start ownership changes only inside the known formula."""
    if not cellar.is_dir() or cellar.is_symlink():
        raise RuntimeError(f"refusing unexpected formula directory: {cellar}")
    paths = [cellar, *cellar.rglob("*")]
    if opt.exists() or opt.is_symlink():
        if not opt.is_symlink() or not opt.resolve().is_relative_to(cellar):
            raise RuntimeError(f"refusing unexpected formula link: {opt}")
        paths.append(opt)
    owner = f"{os.getuid()}:{os.getgid()}"
    for path in paths:
        if path.lstat().st_uid == 0:
            _execute(["sudo", "/usr/sbin/chown", "-h", owner, str(path)], dry_run=dry_run)


def retire_daemons(
    home: Path,
    *,
    dry_run: bool = False,
    system_directory: Path = Path("/Library/LaunchDaemons"),
) -> None:
    definitions: list[tuple[Path, str, list[str]]] = []
    for directory, domain, prefix in (
        (system_directory, "system", ["sudo"]),
        (home / "Library/LaunchAgents", f"gui/{os.getuid()}", []),
    ):
        for label in DAEMON_LABELS:
            path = directory / f"{label}.plist"
            if path.exists() or path.is_symlink():
                validate_daemon(path, label)
                definitions.append((path, f"{domain}/{label}", prefix))

    # Validate every target before stopping or removing any service.
    suffix = datetime.now().strftime("%Y%m%d%H%M%S%f")
    for path, service, prefix in definitions:
        backup = path.with_name(f"{path.name}.mise-darwin-backup-{suffix}")
        if backup.exists() or backup.is_symlink():
            raise RuntimeError(f"refusing to overwrite service backup: {backup}")
        _execute([*prefix, "/bin/cp", "-p", str(path), str(backup)], dry_run=dry_run)
        loaded = run(["launchctl", "print", service], quiet=True, check=False)
        if loaded.returncode == 0:
            _execute([*prefix, "launchctl", "bootout", service], dry_run=dry_run)
        _execute([*prefix, "/bin/rm", str(path)], dry_run=dry_run)

    formula = run(["brew", "list", "--formula", "tailscale"], quiet=True, check=False)
    if formula.returncode == 0:
        restore_formula_ownership(dry_run=dry_run)
        _execute(["brew", "uninstall", "--formula", "tailscale"], dry_run=dry_run)


def configure_policies(home: Path, *, dry_run: bool = False) -> None:
    # The standalone variant requires this explicit path, not a sandbox domain.
    preferences = home / "Library/Preferences/io.tailscale.ipn.macsys.plist"
    for key, kind, value, expected in POLICIES:
        current = run(["defaults", "read", preferences, key], capture=True, check=False)
        if current.returncode != 0 or current.stdout.strip() != expected:
            _execute(
                ["defaults", "write", str(preferences), key, kind, value],
                dry_run=dry_run,
            )


def prepare(home: Path, *, dry_run: bool = False) -> None:
    # Set the incoming policy before the package's postinstall launches the app.
    configure_policies(home, dry_run=dry_run)
    retire_daemons(home, dry_run=dry_run)


def install_cli(home: Path, *, dry_run: bool = False) -> None:
    launcher = home / ".local/bin/tailscale"
    content = (
        f"#!{sys.executable}\n"
        f"{CLI_MARKER}\n"
        "import os\n"
        "import sys\n"
        f"executable = {str(APP_CLI)!r}\n"
        "environment = dict(os.environ, TAILSCALE_BE_CLI='1')\n"
        "os.execve(executable, [executable, *sys.argv[1:]], environment)\n"
    )
    if launcher.is_symlink() or (
        launcher.exists()
        and (not launcher.is_file() or CLI_MARKER not in launcher.read_text(encoding="utf-8"))
    ):
        raise RuntimeError(f"refusing to overwrite unmanaged CLI launcher: {launcher}")
    if launcher.is_file() and launcher.read_text(encoding="utf-8") == content:
        if launcher.stat().st_mode & 0o777 == 0o755:
            return
    if dry_run:
        print(f"would install managed Python CLI launcher: {launcher}")
    else:
        atomic_write(launcher, content, mode=0o755)


def apply(*, dry_run: bool = False) -> None:
    prepare(Path.home(), dry_run=dry_run)
    installed = run(["brew", "list", "--cask", "tailscale-app"], quiet=True, check=False)
    if installed.returncode != 0:
        _execute(["brew", "install", "--cask", "tailscale-app"], dry_run=dry_run)
    if not dry_run and not APP.is_dir():
        raise RuntimeError("tailscale-app is registered but Tailscale.app is missing")
    install_cli(Path.home(), dry_run=dry_run)
    running = run(["pgrep", "-x", "Tailscale"], quiet=True, check=False)
    if running.returncode != 0:
        _execute(["open", "-a", str(APP)], dry_run=dry_run)
    if not dry_run:
        reload_policy = run(
            [APP_CLI, "syspolicy", "reload"],
            env=dict(os.environ, TAILSCALE_BE_CLI="1"),
            capture=True,
            check=False,
        )
        if reload_policy.returncode != 0:
            print("warning: Tailscale policy reload unavailable; relaunch the app after onboarding")
    print("Tailscale: approve the macOS extension/VPN and sign in if prompted.")
