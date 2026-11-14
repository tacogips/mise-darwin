#!/usr/bin/env python3
"""Keep AeroSpace workspaces stable when the display topology changes."""

from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

STATE_VERSION = "external-workspace-assignment-v6"
ONE_DIGIT_WORKSPACE = re.compile(r"[1-9]")


@dataclass(frozen=True)
class Monitor:
    identifier: str
    name: str


@dataclass(frozen=True)
class Workspace:
    name: str
    monitor_id: str


@dataclass(frozen=True)
class Window:
    identifier: str
    workspace: str
    monitor_id: str


def _rows(output: str, fields: int) -> list[tuple[str, ...]]:
    rows: list[tuple[str, ...]] = []
    for line in output.splitlines():
        values = tuple(line.split("|", fields - 1))
        if len(values) == fields and values[0]:
            rows.append(values)
    return rows


def parse_monitors(output: str) -> list[Monitor]:
    return [Monitor(*row) for row in _rows(output, 2)]


def parse_workspaces(output: str) -> list[Workspace]:
    return [Workspace(*row) for row in _rows(output, 2)]


def parse_windows(output: str) -> list[Window]:
    return [Window(*row) for row in _rows(output, 3)]


def workspace_targets(monitors: list[Monitor]) -> dict[str, str]:
    """Return workspace-to-monitor assignments for up to two external displays."""
    built_in = next(
        (monitor.identifier for monitor in monitors if "built-in" in monitor.name.lower()),
        None,
    )
    external = [
        monitor.identifier for monitor in monitors if "built-in" not in monitor.name.lower()
    ]

    targets: dict[str, str] = {}
    if built_in:
        targets["9"] = built_in
    if external:
        targets["1"] = external[0]
        targets["2"] = external[1] if len(external) > 1 else external[0]
    return targets


def fallback_workspace(monitor_id: str, targets: dict[str, str]) -> str | None:
    if targets.get("9") == monitor_id:
        return "9"
    if targets.get("1") == monitor_id:
        return "1"
    if targets.get("2") == monitor_id:
        return "2"
    return None


class AeroSpace:
    def __init__(self) -> None:
        executable = shutil.which("aerospace")
        if executable is None and Path("/opt/homebrew/bin/aerospace").is_file():
            executable = "/opt/homebrew/bin/aerospace"
        if executable is None:
            raise FileNotFoundError("aerospace executable was not found")
        self.executable = executable

    def run(self, *arguments: str, capture: bool = False) -> str:
        result = subprocess.run(
            [self.executable, *arguments],
            check=True,
            capture_output=capture,
            text=True,
            timeout=5,
        )
        return result.stdout if capture else ""


def synchronize(*, force: bool = False, state_dir: Path | None = None) -> None:
    aerospace = AeroSpace()
    monitors_output = aerospace.run(
        "list-monitors", "--format", "%{monitor-id}|%{monitor-name}", capture=True
    )
    monitors = parse_monitors(monitors_output)
    targets = workspace_targets(monitors)
    if not targets:
        return

    workspaces = parse_workspaces(
        aerospace.run(
            "list-workspaces", "--all", "--format", "%{workspace}|%{monitor-id}", capture=True
        )
    )
    current_assignments = {workspace.name: workspace.monitor_id for workspace in workspaces}
    invalid = [
        workspace.name
        for workspace in workspaces
        if ONE_DIGIT_WORKSPACE.fullmatch(workspace.name) is None
    ]

    directory = state_dir or Path.home() / ".local/state/aerospace"
    state_file = directory / "monitor-topology"
    current_state = "\n".join(
        [STATE_VERSION, *(sorted(f"{item.identifier}|{item.name}" for item in monitors))]
    )
    previous_state = state_file.read_text(encoding="utf-8") if state_file.is_file() else ""
    assignments_match = all(current_assignments.get(name) == target for name, target in targets.items())
    if not force and current_state == previous_state and not invalid and assignments_match:
        return

    if invalid:
        windows = parse_windows(
            aerospace.run(
                "list-windows",
                "--all",
                "--format",
                "%{window-id}|%{workspace}|%{monitor-id}",
                capture=True,
            )
        )
        for window in windows:
            if ONE_DIGIT_WORKSPACE.fullmatch(window.workspace):
                continue
            target = fallback_workspace(window.monitor_id, targets)
            if target:
                aerospace.run(
                    "move-node-to-workspace", "--window-id", window.identifier, target
                )

    for workspace in ("9", "1", "2"):
        monitor_id = targets.get(workspace)
        if monitor_id:
            aerospace.run(
                "move-workspace-to-monitor", "--workspace", workspace, monitor_id
            )
            aerospace.run("workspace", workspace)

    directory.mkdir(parents=True, exist_ok=True)
    state_file.write_text(current_state, encoding="utf-8")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    arguments = parser.parse_args()
    try:
        synchronize(force=arguments.force)
    except (FileNotFoundError, subprocess.SubprocessError):
        # Display transitions and app startup can briefly make AeroSpace unavailable.
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
