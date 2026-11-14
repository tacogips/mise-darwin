"""Idempotent post-tool bootstrap operations not modeled directly by mise."""

from __future__ import annotations

import hashlib
import json
import os
import plistlib
import shutil
import sys
from pathlib import Path
from typing import cast

from . import REPO_ROOT, agents, tailscale, wallpaper
from .command import atomic_write, command_exists, run

DOCKER_PLUGIN_DIRS = (
    "/opt/homebrew/lib/docker/cli-plugins",
    "/usr/local/lib/docker/cli-plugins",
)
HERDR_TARGETS = ("claude", "codex")
AEROSPACE_AGENT_LABEL = "com.taco.aerospace-display-sync"
BAT_THEME = REPO_ROOT / "dotfiles/.config/bat/themes/Sora.tmTheme"
# Former user-scope packages replaced by opus-luna-design-and-implement-review-loop.
RETIRED_RIELA_PACKAGES = (
    "fable-and-improve",
    "fable-and-improve-codex",
    "fable-and-improve-opus",
)
RIELA_CLI = Path("/opt/homebrew/bin/riela")
REQUIRED_USER_SKILLS = (
    ("codex", "codex-design-and-implement-review-loop"),
    ("claude", "opus-luna-design-and-implement-review-loop"),
)


def _converge_brewfiles(profile: str) -> None:
    for brewfile in (REPO_ROOT / "Brewfile.common", REPO_ROOT / f"Brewfile.{profile}"):
        if not brewfile.is_file():
            continue
        status = run(["brew", "bundle", "check", "--file", brewfile], quiet=True, check=False)
        if status.returncode != 0:
            run(["brew", "bundle", "--file", brewfile])


def _trust_brew_taps(profile: str) -> None:
    taps = (
        ("tacogips/tap", "tonyxiao/tap", "steipete/tap", "slp/krunkit", "nikitabobko/tap")
        if profile == "desktop"
        else ("slp/krunkit",)
    )
    run(["brew", "trust", "--tap", *taps])


def converge_riela_packages(home: Path) -> None:
    if not command_exists("riela"):
        print("warning: riela is not installed; skipping user package installation")
        return

    converge_riela_cli_quarantine()
    configured_checkout = os.environ.get("RIELA_PACKAGES_CHECKOUT") or None
    checkout = Path(configured_checkout or home / "gits/tacogips/riela-packages")
    git_executable = os.environ.get("RIELA_GIT_EXECUTABLE") or "git"
    packages = checkout / "packages"
    if not packages.is_dir():
        if checkout.exists():
            raise RuntimeError(f"{checkout} exists but has no packages directory")
        checkout.parent.mkdir(parents=True, exist_ok=True)
        run([git_executable, "clone", "https://github.com/tacogips/riela-packages.git", checkout])
    elif configured_checkout is None:
        if not (checkout / ".git").exists():
            raise RuntimeError(f"default Riela package checkout is not a Git repository: {checkout}")
        run([git_executable, "-C", checkout, "pull", "--ff-only"])

    retire_riela_user_packages(home, RETIRED_RIELA_PACKAGES)
    for package_id in agents.riela_package_ids():
        source = packages / package_id
        if not source.is_dir():
            raise RuntimeError(f"required Riela package source is missing: {source}")
        installed = home / ".riela/packages" / package_id
        if installed.exists() and not (installed / "riela-package.json").is_file():
            raise RuntimeError(f"Riela package destination exists without a manifest: {installed}")
        installed_now = (installed / "riela-package.json").is_file()
        print(f"{'updating' if installed_now else 'installing'} Riela user package: {package_id}")
        # Riela's own skill projections are discarded by agents.refresh_skills,
        # so a fresh install may overwrite leftovers from the previous refresh.
        action = ["update", package_id] if installed_now else ["install", package_id, "--overwrite"]
        run(
            [
                "riela",
                "package",
                *action,
                "--source",
                source,
                "--scope",
                "user",
                "--output",
                "json",
            ],
            quiet=True,
        )


def verify_required_user_skills(home: Path) -> None:
    agent_paths = agents.AgentPaths(home)
    for agent, name in REQUIRED_USER_SKILLS:
        path = agent_paths.skills(agent) / name / "SKILL.md"
        if not path.is_file():
            raise RuntimeError(f"required {agent} user skill is missing after refresh: {path}")


def converge_riela_cli_quarantine(cli: Path = RIELA_CLI) -> None:
    """Remove a cask quarantine attribute that can stall the signed Riela CLI."""

    if not cli.is_file():
        return
    quarantine = run(
        ["xattr", "-p", "com.apple.quarantine", cli], quiet=True, check=False
    )
    if quarantine.returncode == 0:
        run(["xattr", "-d", "com.apple.quarantine", cli])


def retire_riela_user_packages(home: Path, package_ids: tuple[str, ...]) -> None:
    """Uninstall retired user-scope packages; the skill refresh drops their skills."""

    lock_path = home / ".riela/riela-lock.json"
    for package_id in package_ids:
        installed = home / ".riela/packages" / package_id
        if not (installed / "riela-package.json").is_file():
            continue
        print(f"retiring Riela user package: {package_id}")
        shutil.rmtree(installed)
        if lock_path.is_file():
            lock = json.loads(lock_path.read_text(encoding="utf-8"))
            if lock.get("packages", {}).pop(package_id, None) is not None:
                atomic_write(lock_path, json.dumps(lock, indent=2) + "\n")


def _install_herdr_integrations() -> None:
    if not command_exists("herdr"):
        raise RuntimeError("herdr is required before installing agent integrations")
    status = run(["herdr", "integration", "status"], capture=True).stdout
    for target in HERDR_TARGETS:
        if any(line.startswith(f"{target}: current ") for line in status.splitlines()):
            continue
        run(["herdr", "integration", "install", target])


def converge_bat_theme_cache(home: Path) -> None:
    """Rebuild bat's cache only when the managed Sora theme changes."""
    if not command_exists("bat"):
        print("warning: bat is not installed; skipping Sora theme cache")
        return

    digest = hashlib.sha256(BAT_THEME.read_bytes()).hexdigest()
    stamp = home / ".cache/mise-darwin/bat-sora.sha256"
    try:
        current = stamp.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        current = ""
    if current == digest:
        return

    run(["bat", "cache", "--build"])
    atomic_write(stamp, f"{digest}\n", mode=0o600)


def _retire_legacy_assets(home: Path) -> None:
    for path in (home / ".local/bin/codex", home / ".local/bin/codex-code-mode-host"):
        if path.is_file() or path.is_symlink():
            path.unlink()

    launch_agent = home / "Library/LaunchAgents/com.taco.tmux-window-title.plist"
    if launch_agent.exists() or launch_agent.is_symlink():
        run(
            ["launchctl", "bootout", f"gui/{os.getuid()}", launch_agent],
            quiet=True,
            check=False,
        )
        launch_agent.unlink()


def converge_docker_config(home: Path) -> None:
    path = home / ".docker/config.json"
    try:
        decoded: object = (
            cast(object, json.loads(path.read_text(encoding="utf-8")))
            if path.stat().st_size
            else cast(object, {})
        )
        if isinstance(decoded, dict):
            raw_config = cast(dict[object, object], decoded)
            config = {str(key): value for key, value in raw_config.items()}
        else:
            config = {}
    except (FileNotFoundError, json.JSONDecodeError):
        config = {}

    current = config.get("cliPluginsExtraDirs")
    entries = (
        [entry for entry in cast(list[object], current) if isinstance(entry, str)]
        if isinstance(current, list)
        else []
    )
    config["cliPluginsExtraDirs"] = sorted({*entries, *DOCKER_PLUGIN_DIRS})
    atomic_write(path, json.dumps(config, indent=2, sort_keys=True) + "\n", mode=0o600)


def converge_aerospace_sync(home: Path, *, load_agent: bool = True) -> None:
    """Install the topology synchronizer and its periodic user LaunchAgent."""
    launcher = home / ".local/bin/aerospace-display-sync"
    source = REPO_ROOT / "scripts/mise_darwin/aerospace_sync.py"
    launcher_content = (
        f"#!{sys.executable}\n"
        "import runpy\n"
        f"runpy.run_path({str(source)!r}, run_name='__main__')\n"
    )
    if not launcher.is_file() or launcher.read_text(encoding="utf-8") != launcher_content:
        atomic_write(launcher, launcher_content, mode=0o755)

    state_dir = home / ".local/state/aerospace"
    state_dir.mkdir(parents=True, exist_ok=True)
    agent = home / "Library/LaunchAgents" / f"{AEROSPACE_AGENT_LABEL}.plist"
    payload = plistlib.dumps(
        {
            "Label": AEROSPACE_AGENT_LABEL,
            "ProgramArguments": [str(launcher)],
            "RunAtLoad": True,
            "StartInterval": 5,
            "StandardOutPath": str(state_dir / "display-sync.log"),
            "StandardErrorPath": str(state_dir / "display-sync.log"),
        },
        sort_keys=True,
    )
    changed = not agent.is_file() or agent.read_bytes() != payload
    if changed:
        atomic_write(agent, payload.decode("utf-8"), mode=0o644)

    if not load_agent:
        return
    domain = f"gui/{os.getuid()}"
    service = f"{domain}/{AEROSPACE_AGENT_LABEL}"
    loaded = run(["launchctl", "print", service], quiet=True, check=False).returncode == 0
    if changed and loaded:
        run(["launchctl", "bootout", service], quiet=True, check=False)
        loaded = False
    if not loaded:
        run(["launchctl", "bootstrap", domain, agent])


def _configure_optional_tools() -> None:
    podman_helper = Path("/opt/homebrew/bin/podman-mac-helper")
    if podman_helper.is_file() and os.access(podman_helper, os.X_OK):
        result = run([podman_helper, "install"], check=False)
        if result.returncode != 0:
            print("warning: podman-mac-helper setup failed")

    chilla = Path("/Applications/chilla.app")
    if chilla.is_dir():
        run(["xattr", "-rd", "com.apple.quarantine", chilla], quiet=True, check=False)
        run(["codesign", "--force", "--deep", "--sign", "-", chilla], quiet=True)

    developer_dir = Path("/Applications/Xcode.app/Contents/Developer")
    if developer_dir.is_dir():
        selected = run(["/usr/bin/xcode-select", "-p"], capture=True, check=False).stdout.strip()
        if selected != str(developer_dir):
            run(["sudo", "/usr/bin/xcode-select", "-s", developer_dir])


def apply(profile: str) -> None:
    home = Path.home()
    for path in (home / ".local/bin", home / ".cache", home / ".local/share"):
        path.mkdir(parents=True, exist_ok=True)

    _trust_brew_taps(profile)
    if profile == "desktop":
        tailscale.apply()
    _converge_brewfiles(profile)
    converge_riela_packages(home)
    agents.install(profile=profile, home=home)
    if command_exists("riela"):
        verify_required_user_skills(home)
    agents.converge_codex_skill_visibility(home)
    _install_herdr_integrations()
    converge_bat_theme_cache(home)
    _retire_legacy_assets(home)
    converge_docker_config(home)
    if profile == "desktop":
        wallpaper.apply()
        converge_aerospace_sync(home)
    _configure_optional_tools()
