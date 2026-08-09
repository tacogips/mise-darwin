# AGENTS.md for the repository root

This file is the canonical instruction entry point for AI assistants working in
this repository and its subdirectories.

## Response rules

- The first response in a conversation must state that this file was read and
  will be followed.
- Think and respond in English unless the user explicitly asks for another
  language.
- If the user's instruction is in English, begin the first response with
  `Your instruction is {corrected English}` using a grammatically corrected
  version of the request.
- Complete the applicable verification steps below after changing files.

## Repository purpose

This repository rebuilds Apple Silicon macOS hosts through mise, Homebrew,
dotfiles, and idempotent tasks. It replaces the former nix-darwin and Home
Manager configuration; do not add Nix as a runtime or bootstrap dependency.

Two host profiles are supported:

- `desktop` for the primary interactive Mac and GUI applications.
- `home-server` for server packages, templates, and privileged directories.

## Structure

```text
mise.toml                 Shared tools, environment, and tasks
mise.macos-arm64.toml     Shared Apple Silicon bootstrap resources
mise.desktop.toml         Desktop profile
mise.home-server.toml     Home-server profile
dotfiles/                 Symlinked user configuration
agent-user-scope/         Explicitly synchronized agent assets
home-server/              Home-server templates
scripts/                  Idempotent bootstrap and maintenance helpers
bootstrap                 Profile-aware bootstrap wrapper
```

Keep common resources in `mise.toml` or `mise.macos-arm64.toml`. Keep host-only
resources in the corresponding profile file. Prefer declarative mise bootstrap
resources; use a task only when the resource is unsupported or requires
explicit idempotent logic.

## Change procedure

After a code or configuration change:

1. Preserve the existing style and keep edits scoped to the request.
2. Validate mise configuration for each affected profile.
3. Run syntax and format checks appropriate to changed files.
4. Run the relevant verification or dry-run command.
5. Update README.md or MIGRATION.md when behavior, layout, or operation changes.

Do not weaken a check merely to make it pass. Explain host-state constraints if
a verification step cannot run on the current Mac.

## Verification commands

Validate profile composition:

```sh
mise -E macos-arm64 -E desktop config ls
mise -E macos-arm64 -E home-server config ls
```

Inspect bootstrap convergence without applying it:

```sh
mise -E macos-arm64 -E desktop bootstrap --dry-run
mise -E macos-arm64 -E desktop bootstrap status --missing
```

Run the host verification task when the current host matches the profile:

```sh
mise -E macos-arm64 -E desktop run verify
```

For shell changes, use the macOS system Bash explicitly so validation does not
depend on a user-managed shell:

```sh
/bin/bash -n scripts/*.sh
shellcheck scripts/*.sh
```

Use `fish -n` for changed Fish files, `jq empty` for changed JSON files, and
`git diff --check` before committing.

## Dotfile guidance

- Keep source files under `dotfiles/` at the same relative path as their target.
- Do not symlink an entire application config directory when the application
  writes logs, sessions, caches, backups, or mutable state there. Link only the
  managed configuration file or stable subdirectory.
- Preserve user data and unrelated user skills. Remove a legacy path only when
  it is a known Nix Store symlink or an explicitly retired managed asset.
- Keep Neovim configuration layered under `lua/taco/core/` and
  `lua/taco/plugins/` rather than collecting unrelated settings in one file.
- Keep generated lockfiles only when they intentionally pin reproducible inputs.

## Public repository safety

This is a public repository. Before every commit or push, inspect the exact
commit target and ensure it contains none of the following:

- Credentials, tokens, passwords, private keys, cookies, or secret values.
- Credential-bearing or private repository URLs.
- Machine-local absolute paths, usernames, hostnames, device identifiers, or
  private service endpoints.
- Generated logs, sessions, caches, backups, or environment-expanded secrets.

Environment-variable references such as `$GITHUB_TOKEN`, generic home-relative
paths such as `~/.config`, and public repository URLs are acceptable. Use the
`git-precommit-safety-check` skill before committing or pushing.

## GitHub authentication

Git operations use HTTPS and the `GITHUB_TOKEN` credential helper. Never embed
the token in Git configuration, remotes, scripts, documentation, or URLs.

## Destructive operations

Nix removal is irreversible. Never run the real uninstall merely as a test.
Require an explicit user request, run the dry-run first, confirm verification
passes, and preserve the documented system-file backup behavior.

```sh
mise run nix:uninstall -- --confirm --dry-run
```

Run `mise run nix:uninstall -- --confirm` only after those gates pass and the
user has clearly authorized Nix removal.

Do not delete or overwrite broad user directories. Back up conflicting real
files before applying `--force-dotfiles`.

## Documentation

- Keep repository documentation in English unless the user requests otherwise.
- Keep clean-machine instructions usable without Nix or direnv.
- Document Apple Silicon, App Store, Xcode, sudo, and profile-specific
  prerequisites where relevant.
