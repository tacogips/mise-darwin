"""Command-line entry point used by mise tasks."""

from __future__ import annotations

import argparse
import os

from . import bootstrap, home_server, nix_uninstall, verify


class Arguments(argparse.Namespace):
    command: str = ""
    confirm: bool = False
    dry_run: bool = False


def _profile() -> str:
    profile = os.environ.get("MISE_DARWIN_PROFILE", "desktop")
    if profile not in {"desktop", "home-server"}:
        raise ValueError(f"unsupported MISE_DARWIN_PROFILE: {profile}")
    return profile


def parser() -> argparse.ArgumentParser:
    command_parser = argparse.ArgumentParser(prog="python -m scripts.mise_darwin")
    subcommands = command_parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("bootstrap", help="run idempotent post-tool configuration")
    subcommands.add_parser("verify", help="verify the current host profile")
    subcommands.add_parser("home-server-apply", help="converge home-server resources")
    uninstall = subcommands.add_parser("nix-uninstall", help="remove Nix from macOS")
    uninstall.add_argument("--confirm", action="store_true")
    uninstall.add_argument("--dry-run", action="store_true")
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
    if arguments.command == "nix-uninstall":
        return nix_uninstall.uninstall(
            profile=profile,
            confirmed=arguments.confirm,
            dry_run=arguments.dry_run,
        )
    return 64


if __name__ == "__main__":
    raise SystemExit(main())
