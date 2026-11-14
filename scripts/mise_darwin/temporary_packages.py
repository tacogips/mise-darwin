"""Resolve temporary packages through mise registry and Homebrew Cask API."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import urllib.error
import urllib.request
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import cast
from urllib.parse import quote, urlparse

from .command import atomic_write, remove_path, run
from .temporary_tool import HttpTool, execute, install

TEMPORARY_TOOL_ROOT = Path("/tmp")
MARKER_NAME = ".mise-darwin-temporary-mise-tool.json"
_PACKAGE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._@+-]*$")
type JsonValue = (
    None | bool | int | float | str | list[JsonValue] | dict[str, JsonValue]
)


@dataclass(frozen=True)
class MiseTool:
    name: str
    version: str
    backend: str

    @property
    def spec(self) -> str:
        return f"{self.backend}@{self.version}"

    @property
    def cache_key(self) -> str:
        value = f"mise:{self.name}:{self.spec}".encode()
        return hashlib.sha256(value).hexdigest()[:16]

    @property
    def destination(self) -> Path:
        return TEMPORARY_TOOL_ROOT / f"{self.name}-{self.cache_key}"

    @property
    def marker_content(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True) + "\n"


ResolvedPackage = HttpTool | MiseTool


def _validate_package_name(name: str) -> str:
    if not _PACKAGE_PATTERN.fullmatch(name):
        raise ValueError(f"invalid temporary package name: {name}")
    return name


def _objects(value: JsonValue) -> list[dict[str, JsonValue]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def cask_tool(payload: Mapping[str, JsonValue]) -> HttpTool:
    token = payload.get("token")
    version = payload.get("version")
    url = payload.get("url")
    sha256 = payload.get("sha256")
    artifacts = payload.get("artifacts")
    if not isinstance(token, str) or not isinstance(version, str):
        raise ValueError("Homebrew Cask metadata is incomplete")
    if not isinstance(url, str) or not isinstance(sha256, str):
        raise ValueError("Homebrew Cask metadata is incomplete")
    if not isinstance(artifacts, list):
        raise ValueError("Homebrew Cask metadata contains no artifacts")
    app_path: str | None = None
    for artifact in _objects(artifacts):
        app = artifact.get("app")
        if isinstance(app, list) and app and isinstance(app[0], str):
            app_path = app[0]
            break
    if app_path is None:
        raise ValueError(f"Homebrew Cask has no app artifact: {token}")
    artifact_format = (
        "dmg" if urlparse(url).path.lower().endswith(".dmg") else "archive"
    )
    return HttpTool(
        name=_validate_package_name(token),
        version=version,
        url=url,
        sha256=sha256,
        executable=app_path,
        artifact_format=artifact_format,
        launch_kind="app",
    ).validated()


def resolve_cask(name: str) -> HttpTool:
    name = _validate_package_name(name)
    url = f"https://formulae.brew.sh/api/cask/{quote(name, safe='')}.json"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "mise-darwin-temporary-package"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = cast(JsonValue, json.load(response))
    except urllib.error.HTTPError as error:
        if error.code == 404:
            raise ValueError(f"Homebrew Cask package not found: {name}") from error
        raise
    if not isinstance(payload, dict):
        raise ValueError("Homebrew Cask response is not an object")
    return cask_tool(payload)


def resolve_mise(name: str, *, required: bool = True) -> MiseTool | None:
    name = _validate_package_name(name)
    registry = run(["mise", "registry", name], capture=True, check=False)
    if registry.returncode != 0:
        if required:
            raise ValueError(f"mise registry package not found: {name}")
        return None
    backends = registry.stdout.split()
    if not backends:
        raise ValueError(f"mise registry returned no backend for: {name}")
    backend = backends[0]
    latest = run(["mise", "latest", name], capture=True)
    version = latest.stdout.strip()
    if not version or any(character.isspace() for character in version):
        raise ValueError(f"mise returned an invalid version for {name}: {version}")
    return MiseTool(name=name, version=version, backend=backend)


def resolve(package: str) -> ResolvedPackage:
    if package.startswith("mise:"):
        resolved = resolve_mise(package.removeprefix("mise:"))
        if resolved is None:  # pragma: no cover - required=True always raises
            raise ValueError(f"mise registry package not found: {package}")
        return resolved
    if package.startswith("brew-cask:"):
        return resolve_cask(package.removeprefix("brew-cask:"))
    name = _validate_package_name(package)
    return resolve_mise(name, required=False) or resolve_cask(name)


def _marker_matches(destination: Path, tool: MiseTool) -> bool:
    marker = destination / MARKER_NAME
    try:
        destination_stat = destination.stat(follow_symlinks=False)
        return (
            destination.is_dir()
            and not destination.is_symlink()
            and destination_stat.st_uid == os.getuid()
            and destination_stat.st_mode & 0o022 == 0
            and marker.is_file()
            and not marker.is_symlink()
            and marker.read_text(encoding="utf-8") == tool.marker_content
        )
    except (FileNotFoundError, IsADirectoryError, OSError):
        return False


def _executable_directories(destination: Path) -> tuple[Path, ...]:
    directories: set[Path] = set()
    for candidate in destination.rglob("*"):
        if (
            candidate.is_file()
            and not candidate.is_symlink()
            and os.access(candidate, os.X_OK)
        ):
            directories.add(candidate.parent)
    return tuple(sorted(directories))


def install_mise(tool: MiseTool, *, dry_run: bool = False) -> tuple[Path, ...]:
    destination = tool.destination
    if destination.exists():
        if not _marker_matches(destination, tool):
            raise RuntimeError(f"refusing to replace unmanaged temporary path: {destination}")
        directories = _executable_directories(destination)
        if directories:
            return directories
        if not dry_run:
            remove_path(destination)
    if dry_run:
        print(f"would install {tool.spec} into {destination}")
        return (destination,)

    staging = Path(
        tempfile.mkdtemp(
            prefix=f".{tool.name}-{tool.cache_key}-", dir=TEMPORARY_TOOL_ROOT
        )
    )
    try:
        run(["mise", "install-into", "--yes", tool.spec, staging])
        directories = _executable_directories(staging)
        if not directories:
            raise RuntimeError(f"mise installed no executables for {tool.spec}")
        atomic_write(staging / MARKER_NAME, tool.marker_content, mode=0o600)
        try:
            staging.rename(destination)
        except FileExistsError:
            if not _marker_matches(destination, tool):
                raise RuntimeError(
                    "temporary mise tool destination appeared during install: "
                    f"{destination}"
                )
            remove_path(staging)
        return _executable_directories(destination)
    finally:
        if staging.exists():
            remove_path(staging)


def run_mise_tool(
    tool: MiseTool,
    arguments: Sequence[str] = (),
    *,
    dry_run: bool = False,
    install_only: bool = False,
) -> int:
    directories = install_mise(tool, dry_run=dry_run)
    if install_only:
        print(tool.destination)
        return 0
    command = list(arguments) if arguments else [os.environ.get("SHELL", "/bin/sh")]
    if dry_run:
        print(f"would run {' '.join(command)} with {tool.name}@{tool.version} on PATH")
        return 0
    environment = os.environ.copy()
    environment["PATH"] = os.pathsep.join(
        [
            *(os.fspath(directory) for directory in directories),
            environment.get("PATH", ""),
        ]
    )
    return run(command, check=False, env=environment).returncode


def run_package(
    package: str,
    arguments: Sequence[str] = (),
    *,
    dry_run: bool = False,
    install_only: bool = False,
) -> int:
    resolved = resolve(package)
    if isinstance(resolved, MiseTool):
        return run_mise_tool(
            resolved,
            arguments,
            dry_run=dry_run,
            install_only=install_only,
        )
    if install_only:
        target = install(resolved, dry_run=dry_run)
        print(target)
        return 0
    return execute(resolved, tuple(arguments), dry_run=dry_run)
