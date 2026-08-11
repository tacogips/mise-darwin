"""Install checksum-pinned HTTP tools into reusable temporary directories."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import time
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import cast
from urllib.parse import urlparse

from .command import atomic_write, remove_path, run

TEMPORARY_TOOL_ROOT = Path("/tmp")
MARKER_NAME = ".mise-darwin-temporary-tool.json"
DOWNLOAD_MARKER_NAME = ".mise-darwin-temporary-download"
DOWNLOAD_CACHE_MAX_AGE_SECONDS = 30 * 24 * 60 * 60
HDIUTIL_PATH = Path("/usr/bin/hdiutil")
OPEN_PATH = Path("/usr/bin/open")
_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_VERSION_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]*$")
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class HttpTool:
    """A checksum-pinned HTTPS artifact for temporary execution."""

    name: str
    version: str
    url: str
    sha256: str
    executable: str
    bin_path: str | None = None
    artifact_format: str = "auto"
    launch_kind: str = "executable"

    def validated(self) -> HttpTool:
        sha256 = self.sha256.lower()
        if not _NAME_PATTERN.fullmatch(self.name):
            raise ValueError(f"invalid temporary tool name: {self.name}")
        if (
            not self.version
            or len(self.version) > 128
            or any(character.isspace() for character in self.version)
            or (
                self.resolved_format == "mise"
                and not _VERSION_PATTERN.fullmatch(self.version)
            )
        ):
            raise ValueError(f"invalid temporary tool version: {self.version}")
        if not _SHA256_PATTERN.fullmatch(sha256):
            raise ValueError("sha256 must contain exactly 64 hexadecimal characters")
        if urlparse(self.url).scheme != "https":
            raise ValueError("temporary tool URL must use HTTPS")
        _validate_tool_option("url", self.url)
        executable = _relative_path("executable", self.executable)
        bin_path = (
            _relative_path("bin_path", self.bin_path)
            if self.bin_path is not None
            else None
        )
        if self.artifact_format not in {"archive", "auto", "dmg", "mise"}:
            raise ValueError("artifact_format must be archive, auto, dmg, or mise")
        if self.launch_kind not in {"app", "executable"}:
            raise ValueError("launch_kind must be app or executable")
        return HttpTool(
            name=self.name,
            version=self.version,
            url=self.url,
            sha256=sha256,
            executable=executable,
            bin_path=bin_path,
            artifact_format=self.artifact_format,
            launch_kind=self.launch_kind,
        )

    @property
    def cache_key(self) -> str:
        return self.sha256[:16]

    @property
    def destination(self) -> Path:
        return TEMPORARY_TOOL_ROOT / f"{self.name}-{self.cache_key}"

    @property
    def marker_content(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True) + "\n"

    @property
    def resolved_format(self) -> str:
        if self.artifact_format != "auto":
            return self.artifact_format
        return "dmg" if urlparse(self.url).path.lower().endswith(".dmg") else "mise"

    @property
    def mise_spec(self) -> str:
        options = [
            f"url={self.url}",
            f"checksum=sha256:{self.sha256}",
        ]
        if self.bin_path is not None:
            options.append(f"bin_path={self.bin_path}")
        return f"http:{self.name}[{','.join(options)}]@{self.version}"


def _validate_tool_option(label: str, value: str) -> None:
    if any(character in value for character in "[],"):
        raise ValueError(f"{label} contains unsupported mise option punctuation")


def _relative_path(label: str, value: str) -> str:
    _validate_tool_option(label, value)
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{label} must be a safe relative path")
    return path.as_posix()


def _marker_matches(destination: Path, tool: HttpTool) -> bool:
    marker = destination / MARKER_NAME
    try:
        destination_stat = destination.stat(follow_symlinks=False)
        marker_value_raw: object = json.loads(marker.read_text(encoding="utf-8"))
        if not isinstance(marker_value_raw, dict):
            return False
        marker_value = cast(dict[str, object], marker_value_raw)
        return (
            destination.is_dir()
            and not destination.is_symlink()
            and destination_stat.st_uid == os.getuid()
            and destination_stat.st_mode & 0o022 == 0
            and marker.is_file()
            and not marker.is_symlink()
            and marker_value.get("name") == tool.name
            and marker_value.get("url") == tool.url
            and marker_value.get("sha256") == tool.sha256
        )
    except (FileNotFoundError, IsADirectoryError, json.JSONDecodeError, OSError):
        return False


def _installed_target(destination: Path, tool: HttpTool) -> Path:
    target = destination / tool.executable
    if tool.launch_kind == "app":
        valid = target.is_dir() and not target.is_symlink()
    else:
        valid = (
            not target.is_symlink()
            and target.is_file()
            and os.access(target, os.X_OK)
        )
    if not valid:
        raise RuntimeError(
            f"installed target is missing or has the wrong type: {target}"
        )
    return target


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download_cache_root() -> Path:
    result = run(["mise", "cache", "path"], capture=True)
    cache_root = Path(result.stdout.strip())
    if not cache_root.is_absolute():
        raise RuntimeError("mise returned a non-absolute cache path")
    return cache_root / "mise-darwin-temporary-http"


def _prune_download_cache(cache_root: Path) -> None:
    if not cache_root.is_dir():
        return
    oldest_allowed = time.time() - DOWNLOAD_CACHE_MAX_AGE_SECONDS
    for candidate in cache_root.iterdir():
        marker = candidate / DOWNLOAD_MARKER_NAME
        try:
            stale = marker.is_file() and candidate.stat().st_mtime < oldest_allowed
        except OSError:
            continue
        if stale:
            remove_path(candidate)


def _download(tool: HttpTool) -> Path:
    cache_root = _download_cache_root()
    _prune_download_cache(cache_root)
    filename = Path(urlparse(tool.url).path).name
    if not filename or filename in {".", ".."}:
        raise ValueError("temporary tool URL must contain a filename")
    cache_directory = cache_root / tool.sha256
    artifact = cache_directory / filename
    if artifact.is_file() and _sha256(artifact) == tool.sha256:
        cache_directory.touch()
        return artifact

    cache_directory.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{filename}.", dir=cache_directory
    )
    temporary = Path(temporary_name)
    try:
        request = urllib.request.Request(
            tool.url,
            headers={"User-Agent": "mise-darwin-temporary-tool"},
        )
        with os.fdopen(descriptor, "wb") as target:
            with urllib.request.urlopen(request, timeout=30) as response:
                shutil.copyfileobj(response, target)
        actual_sha256 = _sha256(temporary)
        if actual_sha256 != tool.sha256:
            raise RuntimeError(
                f"sha256 mismatch for {tool.url}: expected {tool.sha256}, "
                f"got {actual_sha256}"
            )
        os.replace(temporary, artifact)
        atomic_write(cache_directory / DOWNLOAD_MARKER_NAME, "managed\n", mode=0o600)
        return artifact
    finally:
        temporary.unlink(missing_ok=True)


def _extract_dmg(tool: HttpTool, staging: Path) -> None:
    artifact = _download(tool)
    mountpoint = Path(
        tempfile.mkdtemp(prefix=f".{tool.name}-mount-", dir=TEMPORARY_TOOL_ROOT)
    )
    attached = False
    try:
        run(
            [
                HDIUTIL_PATH,
                "attach",
                "-readonly",
                "-nobrowse",
                "-mountpoint",
                mountpoint,
                artifact,
            ],
            quiet=True,
        )
        attached = True
        shutil.copytree(mountpoint, staging, dirs_exist_ok=True, symlinks=True)
    finally:
        if attached:
            run([HDIUTIL_PATH, "detach", mountpoint], quiet=True)
        if mountpoint.exists():
            remove_path(mountpoint)


def _extract_archive(tool: HttpTool, staging: Path) -> None:
    shutil.unpack_archive(_download(tool), staging)


def _populate_staging(tool: HttpTool, staging: Path) -> None:
    if tool.resolved_format == "dmg":
        _extract_dmg(tool, staging)
        return
    if tool.resolved_format == "archive":
        _extract_archive(tool, staging)
        return
    run(["mise", "install-into", "--yes", tool.mise_spec, staging])


def _validate_host_requirements(tool: HttpTool) -> None:
    if tool.launch_kind == "app" and sys.platform != "darwin":
        raise RuntimeError("temporary app bundles are supported only on macOS")
    if tool.resolved_format != "dmg":
        if tool.launch_kind == "app" and (
            not OPEN_PATH.is_file() or not os.access(OPEN_PATH, os.X_OK)
        ):
            raise RuntimeError(f"required macOS system tool is unavailable: {OPEN_PATH}")
        return
    if sys.platform != "darwin":
        raise RuntimeError("DMG temporary tools are supported only on macOS")
    for required in (HDIUTIL_PATH, OPEN_PATH if tool.launch_kind == "app" else None):
        if required is not None and (
            not required.is_file() or not os.access(required, os.X_OK)
        ):
            raise RuntimeError(f"required macOS system tool is unavailable: {required}")


def install(tool: HttpTool, *, dry_run: bool = False) -> Path:
    """Install one HTTP tool under /tmp and return its executable path."""
    tool = tool.validated()
    _validate_host_requirements(tool)
    destination = tool.destination

    if destination.exists():
        if not _marker_matches(destination, tool):
            raise RuntimeError(
                f"refusing to replace unmanaged temporary path: {destination}"
            )
        try:
            target = _installed_target(destination, tool)
            if (destination / MARKER_NAME).read_text(encoding="utf-8") != tool.marker_content:
                atomic_write(destination / MARKER_NAME, tool.marker_content, mode=0o600)
            return target
        except RuntimeError:
            if dry_run:
                print(f"would repair incomplete temporary tool: {destination}")
                return destination / tool.executable
            remove_path(destination)

    if dry_run:
        print(f"would install {tool.name}@{tool.version} into {destination}")
        return destination / tool.executable

    staging = Path(
        tempfile.mkdtemp(
            prefix=f".{tool.name}-{tool.cache_key}-",
            dir=TEMPORARY_TOOL_ROOT,
        )
    )
    try:
        _populate_staging(tool, staging)
        _installed_target(staging, tool)
        atomic_write(staging / MARKER_NAME, tool.marker_content, mode=0o600)
        try:
            staging.rename(destination)
        except FileExistsError:
            if not _marker_matches(destination, tool):
                raise RuntimeError(
                    f"temporary tool destination appeared during install: {destination}"
                )
            remove_path(staging)
        return _installed_target(destination, tool)
    finally:
        if staging.exists():
            remove_path(staging)


def execute(
    tool: HttpTool,
    arguments: list[str] | tuple[str, ...] = (),
    *,
    dry_run: bool = False,
) -> int:
    """Install a temporary tool when needed and execute it."""
    target = install(tool, dry_run=dry_run)
    if dry_run:
        rendered = " ".join([os.fspath(target), *arguments])
        print(f"would run {rendered}")
        return 0
    if tool.launch_kind == "app":
        command: list[str | os.PathLike[str]] = [OPEN_PATH, target]
        if arguments:
            command.extend(["--args", *arguments])
    else:
        command = [target, *arguments]
    return run(command, check=False).returncode


def prune(tool: HttpTool, *, dry_run: bool = False) -> bool:
    """Remove an exact managed temporary-tool directory."""
    tool = tool.validated()
    destination = tool.destination
    if not destination.exists():
        return False
    if not _marker_matches(destination, tool):
        raise RuntimeError(f"refusing to remove unmanaged temporary path: {destination}")
    if dry_run:
        print(f"would remove {destination}")
    else:
        remove_path(destination)
    return True
