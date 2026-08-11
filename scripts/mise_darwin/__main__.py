"""Command-line entry point used by mise tasks."""

from __future__ import annotations

import argparse
import os

from . import (
    bootstrap,
    home_server,
    nix_uninstall,
    temporary_packages,
    upgrade_taco,
    verify,
)
from .temporary_tool import HttpTool, execute, install


class Arguments(argparse.Namespace):
    command: str = ""
    confirm: bool = False
    dry_run: bool = False


def _profile() -> str:
    profile = os.environ.get("MISE_DARWIN_PROFILE", "desktop")
    if profile not in {"desktop", "home-server"}:
        raise ValueError(f"unsupported MISE_DARWIN_PROFILE: {profile}")
    return profile


def command_arguments(arguments: list[str]) -> list[str]:
    return arguments[1:] if arguments[:1] == ["--"] else arguments


def shell_arguments(
    arguments: list[str], *, dry_run: bool, install_only: bool
) -> tuple[list[str], bool, bool]:
    if arguments[:1] == ["--"]:
        return arguments[1:], dry_run, install_only
    remaining = list(arguments)
    while remaining and remaining[0] in {"--dry-run", "--install-only"}:
        option = remaining.pop(0)
        dry_run = dry_run or option == "--dry-run"
        install_only = install_only or option == "--install-only"
    if remaining[:1] == ["--"]:
        remaining.pop(0)
    return remaining, dry_run, install_only


def parser() -> argparse.ArgumentParser:
    command_parser = argparse.ArgumentParser(prog="python -m scripts.mise_darwin")
    subcommands = command_parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("bootstrap", help="run idempotent post-tool configuration")
    subcommands.add_parser("verify", help="verify the current host profile")
    subcommands.add_parser("home-server-apply", help="converge home-server resources")
    subcommands.add_parser(
        "upgrade-taco", help="upgrade installed tacogips Homebrew formulae and casks"
    )
    uninstall = subcommands.add_parser("nix-uninstall", help="remove Nix from macOS")
    uninstall.add_argument("--confirm", action="store_true")
    uninstall.add_argument("--dry-run", action="store_true")
    shell = subcommands.add_parser(
        "shell", help="resolve and run a temporary mise or Homebrew Cask package"
    )
    shell.add_argument("package")
    shell.add_argument("--dry-run", action="store_true")
    shell.add_argument("--install-only", action="store_true")
    shell.add_argument("arguments", nargs=argparse.REMAINDER)
    temporary = subcommands.add_parser(
        "temp-install", help="install and run a checksum-pinned HTTP tool from /tmp"
    )
    temporary.add_argument("--name", required=True)
    temporary.add_argument("--version", required=True)
    temporary.add_argument("--url", required=True)
    temporary.add_argument("--sha256", required=True)
    temporary.add_argument("--executable", required=True)
    temporary.add_argument("--bin-path")
    temporary.add_argument(
        "--format",
        dest="artifact_format",
        choices=("auto", "archive", "dmg", "mise"),
        default="auto",
    )
    temporary.add_argument("--dry-run", action="store_true")
    temporary.add_argument("--install-only", action="store_true")
    temporary.add_argument("arguments", nargs=argparse.REMAINDER)
    return command_parser


def main() -> int:
    arguments = parser().parse_args(namespace=Arguments())
    profile = _profile()
    if arguments.command == "bootstrap":
        bootstrap.apply(profile)
        return 0
    if arguments.command == "verify":
        return 0 if verify.verify(profile) else 1
    if arguments.command == "home-server-apply":
        home_server.apply()
        return 0
    if arguments.command == "upgrade-taco":
        upgrade_taco.upgrade()
        return 0
    if arguments.command == "nix-uninstall":
        return nix_uninstall.uninstall(
            profile=profile,
            confirmed=arguments.confirm,
            dry_run=arguments.dry_run,
        )
    if arguments.command == "shell":
        shell_command_arguments, dry_run, install_only = shell_arguments(
            arguments.arguments,
            dry_run=arguments.dry_run,
            install_only=arguments.install_only,
        )
        return temporary_packages.run_package(
            arguments.package,
            shell_command_arguments,
            dry_run=dry_run,
            install_only=install_only,
        )
    if arguments.command == "temp-install":
        tool = HttpTool(
            name=arguments.name,
            version=arguments.version,
            url=arguments.url,
            sha256=arguments.sha256,
            executable=arguments.executable,
            bin_path=arguments.bin_path,
            artifact_format=arguments.artifact_format,
        )
        if arguments.install_only:
            executable = install(tool, dry_run=arguments.dry_run)
            print(executable)
            return 0
        return execute(
            tool,
            command_arguments(arguments.arguments),
            dry_run=arguments.dry_run,
        )
    return 64


if __name__ == "__main__":
    raise SystemExit(main())
