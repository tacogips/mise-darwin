"""Converge privileged and user-scoped home-server resources."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from . import REPO_ROOT
from .command import command_exists, run

ETC_ROOT = Path("/etc/darwin-mac-home-server")


def _render(source: Path, replacements: dict[str, str]) -> str:
    content = source.read_text(encoding="utf-8")
    for marker, value in replacements.items():
        content = content.replace(marker, value)
    return content


def _sudo_install(content: str, destination: Path) -> None:
    descriptor, temporary_name = tempfile.mkstemp(prefix="mise-darwin-server.")
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
        run(["sudo", "install", "-m", "0644", temporary, destination])
    finally:
        temporary.unlink(missing_ok=True)


def _ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    path.chmod(0o755)


def apply() -> None:
    home = Path.home()
    data_root = Path(os.environ.get("HOME_SERVER_DATA_ROOT", "/Volumes/Data"))
    backup_root = Path(os.environ.get("HOME_SERVER_BACKUP_ROOT", "/Volumes/Backup"))
    service_root = Path(os.environ.get("HOME_SERVER_SERVICE_ROOT", home / "home-server"))
    replacements = {
        "__SERVICE_ROOT__": str(service_root),
        "__DATA_ROOT__": str(data_root),
        "__BACKUP_ROOT__": str(backup_root),
    }

    run(["sudo", "install", "-d", "-m", "0755", ETC_ROOT])
    for name in ("compose.yaml", "Caddyfile", "README.md"):
        _sudo_install(_render(REPO_ROOT / "home-server" / name, replacements), ETC_ROOT / name)

    for directory in (service_root, service_root / "state", service_root / "backups"):
        _ensure_directory(directory)
    for name in ("compose.yaml", "Caddyfile", "README.md"):
        link = service_root / name
        expected = ETC_ROOT / name
        if link.is_symlink() and link.resolve(strict=False) == expected:
            continue
        if link.exists() or link.is_symlink():
            link.unlink()
        link.symlink_to(expected)

    if data_root.is_dir():
        for name in ("Photos", "Videos", "Files"):
            _ensure_directory(data_root / name)
    else:
        print(f"warning: data volume is not mounted; skipped {data_root} subdirectories")

    if backup_root.is_dir():
        _ensure_directory(backup_root / "home-server")
    else:
        print(f"warning: backup volume is not mounted; skipped {backup_root}/home-server")

    if command_exists("brew"):
        services = run(["brew", "services", "list"], capture=True, check=False)
        if any(line.startswith("colima ") for line in services.stdout.splitlines()):
            run(["brew", "services", "start", "colima"], quiet=True)
