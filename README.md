# mise-darwin

This repository rebuilds the macOS configuration formerly managed in
`tacogips/nix` with mise as the entry point. It does not depend on the Nix Store
or nix-darwin generations.

## Repository layout

```text
mise.toml                    Shared tools, environment variables, and tasks
mise.macos-arm64.toml        Apple Silicon packages, defaults, and dotfiles
mise.desktop.toml            Desktop GUI and Mac App Store applications
mise.home-server.toml        Home-server service dependencies
dotfiles/.config/nvim/       Lua and lazy.nvim configuration
dotfiles/.agents/skills/     Apple Gateway user skills
agent-user-scope/            Claude, Codex, Cursor, and Riela user assets
home-server/                 Server templates converged under /etc
scripts/                     Idempotent helpers, verification, and Nix removal
Brewfile.*                   Casks and third-party tap packages
```

Commands load `mise.macos-arm64.toml` together with one host profile. The
`bootstrap` wrapper supplies those environments, so normal use does not require
passing `-E` manually.

## mise environments (`-E`)

`-E NAME` tells mise to additionally load `mise.NAME.toml`. This repository
defines the following environments:

| `-E` value | Configuration file | Purpose |
| --- | --- | --- |
| `macos-arm64` | `mise.macos-arm64.toml` | Shared Apple Silicon packages, dotfiles, macOS defaults, and login shell |
| `desktop` | `mise.desktop.toml` | Desktop packages, GUI applications, and `MISE_DARWIN_PROFILE=desktop` |
| `home-server` | `mise.home-server.toml` | Home-server packages, paths, and `MISE_DARWIN_PROFILE=home-server` |

Always combine `macos-arm64` with exactly one host profile:

```sh
# Desktop Mac
mise -E macos-arm64 -E desktop bootstrap status --missing

# Home-server Mac
mise -E macos-arm64 -E home-server bootstrap status --missing
```

Without `-E`, mise loads only `mise.toml`. Common tools, environment variables,
and tasks remain available, but the Homebrew packages, dotfiles, macOS defaults,
login shell, and host-specific resources are not loaded. Consequently, a plain
`mise bootstrap` is not a complete machine bootstrap.

Prefer the wrapper for applying a host because it expands profiles correctly:

```text
./bootstrap desktop      -> mise -E macos-arm64 -E desktop bootstrap --yes
./bootstrap home-server  -> mise -E macos-arm64 -E home-server bootstrap --yes
```

List profiles or display the mapping at any time:

```sh
./bootstrap --list-profiles
./bootstrap --help
```

## Set up a clean Mac

This repository targets Apple Silicon Macs with Homebrew installed under
`/opt/homebrew`.

First install the Xcode Command Line Tools. Wait for the installation dialog to
finish before continuing.

```sh
xcode-select --install
```

Run the [official Homebrew installer](https://docs.brew.sh/Installation), then
make Homebrew available in the current zsh session and future login sessions.

```sh
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

Install Git and mise. Homebrew is the
[recommended mise installation method on macOS](https://mise.jdx.dev/installing-mise.html).

```sh
brew install git mise
git --version
mise --version
```

Clone this public repository and apply the desktop profile. Bootstrap may ask
for the macOS password when changing system settings or the login shell. Sign in
to the App Store first if Mac App Store applications should be installed.

```sh
mkdir -p ~/gits/tacogips
git clone https://github.com/tacogips/mise-darwin.git ~/gits/tacogips/mise-darwin
cd ~/gits/tacogips/mise-darwin
mise trust
./bootstrap desktop
```

When bootstrap finishes, open a new Terminal window so the Homebrew Fish login
shell is active, then verify the complete configuration.

```sh
cd ~/gits/tacogips/mise-darwin
mise -E macos-arm64 -E desktop run verify
```

## Bootstrap an existing Mac

If Homebrew and mise are already installed, run:

```sh
mkdir -p ~/gits/tacogips
git clone https://github.com/tacogips/mise-darwin.git ~/gits/tacogips/mise-darwin
cd ~/gits/tacogips/mise-darwin
mise trust
./bootstrap desktop
```

Use the home-server profile on the server Mac:

```sh
./bootstrap home-server
```

Preview changes or inspect missing resources without applying them:

```sh
mise -E macos-arm64 -E desktop bootstrap --dry-run
mise -E macos-arm64 -E desktop bootstrap status --missing
```

Bootstrap stops instead of overwriting conflicting Home Manager links or local
files. Inspect and back up those paths before explicitly allowing replacement:

```sh
mise -E macos-arm64 -E desktop bootstrap --yes --force-dotfiles
```

## Neovim

The Neovim configuration translates the previous NVF setup into the layered
layout used by `dotfile_nvim`:

```text
dotfiles/.config/nvim/
├── init.lua
├── ftplugin/
└── lua/taco/
    ├── core/       Options, keymaps, and autocommands
    └── plugins/    Editor, UI, LSP, and completion plugins
```

The first Neovim launch installs `lazy.nvim`. mise tools and bootstrap Homebrew
packages provide language servers, formatters, and supporting CLI tools. Commit
`lazy-lock.json` after reviewing the generated plugin lock.

Yazi Git plugins and the Gruvbox flavor are pinned in `package.toml` and
installed with `ya pkg install` near the end of bootstrap. The Karabiner config
includes the migrated ANSI/Kana symbol mappings. Apple Gateway skills are
linked one skill directory at a time so unrelated user skills are preserved.

## AI agent user scope and Riela

`agent-user-scope/` contains the migrated Claude commands, shared Claude/Codex
skills, Cursor CLI configuration, Peekaboo MCP configuration, and Cursor skill.
Bootstrap synchronizes only known assets and does not remove skills managed by
Riela or other installers. The old `envrc-generate` skill is intentionally
excluded because this setup does not use direnv.

On desktop hosts, bootstrap installs the Riela application and all user-scope
workflow and skill packages listed in `agent-user-scope/riela-packages.txt`. If
the public `tacogips/riela-packages` checkout is absent, the installer clones it
under the standard checkout root.

GitHub HTTPS authentication uses the `GITHUB_TOKEN` credential helper. Fish
provides `gh-token-export`, `gh-token-save-shared`, `gh-token-refresh`,
`gh-token-reset`, and `gh-clone`. Claude and Codex expose the
`git-precommit-safety-check` user skill for credential review before commit or
push.

## Verification and Nix removal

Verify the migrated setup from a new shell:

```sh
mise -E macos-arm64 -E desktop run verify
```

Only remove Nix after verification succeeds. Preview the destructive operation
first:

```sh
mise run nix:uninstall -- --confirm --dry-run
```

Then run the uninstall task:

```sh
mise run nix:uninstall -- --confirm
```

The task first removes nix-darwin. It uses the Determinate uninstaller when
available and otherwise follows the
[official legacy macOS multi-user uninstall procedure](https://nix.dev/manual/nix/stable/installation/uninstall#macos).
The legacy path verifies the APFS `/nix` volume, login shell, and user-scope
links before making changes. Modified system files are backed up under
`/var/backups/mise-darwin-nix-uninstall-*`.

Nix removal is irreversible. Keep the former configuration repository only as
a migration reference until this repository passes verification.

## Current boundaries

- mise bootstrap converges sequentially and does not provide nix-darwin atomic
  switches or generation rollback.
- mise manages formulae directly. Homebrew Bundle handles casks and third-party
  taps without API metadata, avoiding conflicts with existing cask receipts.
- Mac App Store installation may require an Apple Account. Xcode may require a
  first launch and license acceptance.
- Add a dedicated, reviewable task and plist when a system LaunchDaemon becomes
  necessary.
- The `home-server:apply` task converges privileged `/etc` files and volume
  directories for the home-server profile.
