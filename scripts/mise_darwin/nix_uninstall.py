"""Guarded macOS Nix removal, ported from the legacy shell implementation."""

from __future__ import annotations

import os
import platform
import re
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from .command import remove_path, run
from .verify import verify

LAUNCH_DAEMONS = (
    Path("/Library/LaunchDaemons/org.nixos.nix-daemon.plist"),
    Path("/Library/LaunchDaemons/org.nixos.darwin-store.plist"),
    Path("/Library/LaunchDaemons/org.nixos.nix-garbage-collector.plist"),
)
SHELL_FILES = (Path("/etc/zshrc"), Path("/etc/bashrc"), Path("/etc/bash.bashrc"))


def _dscl_value(record: str, attribute: str) -> str:
    result = run(["dscl", ".", "-read", record, attribute], capture=True, check=False)
    if result.returncode != 0 or ":" not in result.stdout:
        return ""
    return result.stdout.partition(":")[2].strip()


def _nix_symlinks(roots: tuple[Path, ...]) -> list[Path]:
    matches: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        for directory, names, files in os.walk(root, followlinks=False):
            base = Path(directory)
            for name in [*names, *files]:
                path = base / name
                try:
                    if path.is_symlink() and os.readlink(path).startswith("/nix/store/"):
                        matches.append(path)
                except OSError:
                    continue
    return matches


def _diskutil_field(output: str, label: str) -> str:
    for line in output.splitlines():
        key, separator, value = line.partition(":")
        if separator and key.strip() == label:
            return value.strip()
    return ""


def filter_nix_mount(content: str, *, synthetic: bool) -> str:
    kept: list[str] = []
    for line in content.splitlines(keepends=True):
        fields = line.split()
        remove = bool(fields) and (
            fields[0] == "nix"
            if synthetic
            else len(fields) >= 2
            and (fields[1] == "/nix" or fields[0] == r"LABEL=Nix\040Store")
        )
        if not remove:
            kept.append(line)
    return "".join(kept)


def strip_nix_shell_block(content: str) -> str:
    kept: list[str] = []
    skipping = False
    for line in content.splitlines(keepends=True):
        marker = line.rstrip("\r\n")
        if marker == "# Nix":
            skipping = True
            continue
        if skipping and marker == "# End Nix":
            skipping = False
            continue
        if not skipping:
            kept.append(line)
    return "".join(kept)


def _backup(source: Path, destination: Path) -> None:
    if source.exists() or source.is_symlink():
        run(["sudo", "cp", "-a", source, destination])


def _sudo_replace(path: Path, content: str) -> None:
    descriptor, temporary_name = tempfile.mkstemp(prefix="mise-darwin-uninstall.")
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
        run(["sudo", "install", "-m", "0644", temporary, path])
    finally:
        temporary.unlink(missing_ok=True)


def _rewrite_mount_file(path: Path, *, synthetic: bool) -> None:
    if path.is_file():
        content = path.read_text(encoding="utf-8")
        _sudo_replace(path, filter_nix_mount(content, synthetic=synthetic))


def _rewrite_shell_file(path: Path) -> None:
    source = path
    if path.is_symlink():
        source = path.with_name(f"{path.name}.backup-before-nix")
        if not source.is_file():
            raise RuntimeError(
                f"cannot replace Nix-managed shell file without installer backup: {path}"
            )
    if not source.is_file():
        return
    content = strip_nix_shell_block(source.read_text(encoding="utf-8"))
    if path.is_symlink():
        run(["sudo", "rm", "-f", path])
    _sudo_replace(path, content)


def _preflight(profile: str) -> tuple[Path, list[str]]:
    failures: list[str] = []
    current_user = run(["id", "-un"], capture=True).stdout.strip()
    home_text = _dscl_value(f"/Users/{current_user}", "NFSHomeDirectory")
    if not home_text.startswith("/Users/") or home_text == "/Users":
        raise RuntimeError(f"refusing to use unexpected user home: {home_text or '<empty>'}")
    user_home = Path(home_text)

    login_shell = _dscl_value(f"/Users/{current_user}", "UserShell")
    if login_shell.startswith("/nix/") or not os.access(login_shell, os.X_OK):
        failures.append(
            "login shell must be switched from Nix to an existing Homebrew shell "
            f"(current: {login_shell or 'unknown'})"
        )

    managed_roots = (
        user_home / ".config",
        user_home / ".local/bin",
        user_home / ".agents",
        user_home / ".claude",
        user_home / ".codex",
        user_home / ".cursor",
        user_home / "Library/LaunchAgents",
    )
    failures.extend(
        f"user-scope link still points into the Nix Store: {path}"
        for path in _nix_symlinks(managed_roots)
    )

    if not verify(profile, home=user_home):
        failures.append(f"mise-darwin verification failed for profile: {profile}")

    volume = run(["diskutil", "info", "/nix"], capture=True, check=False)
    if volume.returncode != 0 or not volume.stdout.strip():
        failures.append("/nix is not a mounted volume")
    else:
        mount_point = _diskutil_field(volume.stdout, "Mount Point")
        filesystem = _diskutil_field(volume.stdout, "Type (Bundle)")
        if mount_point != "/nix" or filesystem != "apfs":
            failures.append("refusing to delete a volume that is not the APFS /nix mount")
    return user_home, failures


def _find_determinate_installer() -> Path | None:
    installed = Path("/nix/nix-installer")
    if installed.is_file() and os.access(installed, os.X_OK):
        return installed
    executable = shutil.which("nix-installer")
    return Path(executable) if executable else None


def uninstall(*, profile: str, confirmed: bool, dry_run: bool) -> int:
    if not confirmed:
        print("error: --confirm is required", file=sys.stderr)
        return 64
    if platform.system() != "Darwin":
        print("This task only supports macOS.", file=sys.stderr)
        return 1

    user_home, failures = _preflight(profile)
    for failure in failures:
        print(f"error: {failure}", file=sys.stderr)
    if failures:
        print(
            f"{len(failures)} preflight check(s) failed; Nix was not removed",
            file=sys.stderr,
        )
        return 2

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root = Path(f"/var/backups/mise-darwin-nix-uninstall-{timestamp}")
    darwin_uninstaller = Path("/run/current-system/sw/bin/darwin-uninstaller")
    determinate_installer = _find_determinate_installer()

    if dry_run:
        print(f"dry-run: would back up modified system files under {backup_root}")
        if darwin_uninstaller.is_file() and os.access(darwin_uninstaller, os.X_OK):
            print(f"dry-run: would run {darwin_uninstaller}")
        if determinate_installer:
            print(f"dry-run: would run {determinate_installer} uninstall")
        else:
            print(
                "dry-run: would perform the official legacy macOS multi-user uninstall:\n"
                "  - stop and remove Nix LaunchDaemons\n"
                "  - remove nixbld users and group\n"
                "  - remove the /nix fstab and synthetic.conf entries\n"
                "  - remove Nix user/root state and /etc/nix\n"
                "  - delete the verified APFS volume mounted at /nix"
            )
        return 0

    run(["sudo", "mkdir", "-p", backup_root])
    if darwin_uninstaller.is_file() and os.access(darwin_uninstaller, os.X_OK):
        run(["sudo", darwin_uninstaller], input_text="")
    if determinate_installer:
        run(["sudo", determinate_installer, "uninstall"])
        print("Nix was removed by Determinate Nix Installer. Reboot, then run the mise verify task.")
        return 0

    for plist in LAUNCH_DAEMONS:
        if not plist.exists():
            continue
        _backup(plist, backup_root / plist.name)
        stopped = run(["sudo", "launchctl", "bootout", "system", plist], quiet=True, check=False)
        if stopped.returncode != 0:
            run(["sudo", "launchctl", "unload", plist], quiet=True, check=False)
        run(["sudo", "rm", "-f", plist])

    users = run(["dscl", ".", "-list", "/Users"], capture=True).stdout.splitlines()
    for user in users:
        if re.fullmatch(r"_nixbld[0-9]+", user):
            run(["sudo", "dscl", ".", "-delete", f"/Users/{user}"])
    if run(["dscl", ".", "-read", "/Groups/nixbld"], quiet=True, check=False).returncode == 0:
        run(["sudo", "dscl", ".", "-delete", "/Groups/nixbld"])

    for path in (Path("/etc/fstab"), Path("/etc/synthetic.conf")):
        _backup(path, backup_root / path.name)
    _rewrite_mount_file(Path("/etc/fstab"), synthetic=False)
    _rewrite_mount_file(Path("/etc/synthetic.conf"), synthetic=True)

    for path in SHELL_FILES:
        if path.exists() or path.is_symlink():
            _backup(path, backup_root / path.name)
            _rewrite_shell_file(path)

    run(
        [
            "sudo",
            "rm",
            "-rf",
            "--",
            "/etc/nix",
            "/var/root/.nix-profile",
            "/var/root/.nix-defexpr",
            "/var/root/.nix-channels",
        ]
    )
    for path in (
        user_home / ".nix-profile",
        user_home / ".nix-defexpr",
        user_home / ".nix-channels",
        user_home / ".local/share/nix",
        user_home / ".local/state/nix",
        user_home / ".cache/nix",
    ):
        remove_path(path)

    run(["sudo", "diskutil", "apfs", "deleteVolume", "/nix"])
    print(
        "Legacy multi-user Nix was removed.\n"
        f"System-file backups: {backup_root}\n"
        "Reboot macOS, open a new shell, and run:\n"
        f"  mise -E macos-arm64 -E {profile} run verify"
    )
    return 0
