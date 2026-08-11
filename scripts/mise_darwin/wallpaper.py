"""Converge the managed macOS desktop wallpaper."""

from __future__ import annotations

from pathlib import Path

from . import REPO_ROOT
from .command import run

WALLPAPER = REPO_ROOT / "assets/wallpapers/sora-sea.jpg"

READ_DESKTOP_PICTURES = """
tell application "System Events"
  set picturePaths to {}
  repeat with desktopItem in desktops
    set picturePath to picture of desktopItem
    if picturePath is not missing value then
      set end of picturePaths to picturePath as text
    end if
  end repeat
end tell
set AppleScript's text item delimiters to linefeed
return picturePaths as text
"""

SET_DESKTOP_PICTURES = """
on run argv
  set wallpaperFile to POSIX file (item 1 of argv)
  tell application "System Events"
    repeat with desktopItem in desktops
      set picture of desktopItem to wallpaperFile
    end repeat
  end tell
end run
"""


def desktop_pictures() -> tuple[Path, ...]:
    result = run(
        ["/usr/bin/osascript", "-e", READ_DESKTOP_PICTURES],
        capture=True,
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"could not inspect desktop wallpaper: {detail}")
    return tuple(Path(line) for line in result.stdout.splitlines() if line)


def apply() -> None:
    target = WALLPAPER.resolve(strict=True)
    current = desktop_pictures()
    if current and all(path.resolve(strict=False) == target for path in current):
        return

    run(["/usr/bin/osascript", "-e", SET_DESKTOP_PICTURES, "--", target])
    updated = desktop_pictures()
    if updated and not all(path.resolve(strict=False) == target for path in updated):
        raise RuntimeError("macOS did not apply the managed wallpaper to every desktop")
