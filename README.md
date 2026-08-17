# mise-darwin

This repository rebuilds the macOS configuration formerly managed in
`tacogips/nix` with mise as the entry point. It does not depend on the Nix Store
or nix-darwin generations.

## Repository layout

```text
.miserc.toml                 Default platform and desktop environments
mise.toml                    Shared tools, environment variables, and tasks
mise.macos-arm64.toml        Apple Silicon packages, defaults, and dotfiles
mise.desktop.toml            Desktop GUI and Mac App Store applications
mise.home-server.toml        Home-server service dependencies
dotfiles/.config/nvim/       Lua and lazy.nvim configuration
assets/wallpapers/           Git-managed desktop wallpaper
dotfiles/.agents/skills/     Apple Gateway user skills
agent-user-scope/            Claude, Codex, Cursor, and Riela user assets
home-server/                 Server templates converged under /etc
scripts/mise_darwin/         Standard-library Python provisioning commands
tests/                       Python provisioning unit tests
Brewfile.*                   Casks and third-party tap packages
```

`.miserc.toml` enables mise's platform environment detection and selects the
`desktop` host profile by default. On an Apple Silicon Mac, ordinary mise
commands therefore load `mise.macos-arm64.toml` and `mise.desktop.toml` without
requiring `-E`.

## mise environments (`-E`)

`-E NAME` tells mise to additionally load `mise.NAME.toml`. This repository
defines the following environments:

| `-E` value | Configuration file | Purpose |
| --- | --- | --- |
| `macos-arm64` | `mise.macos-arm64.toml` | Shared Apple Silicon packages, dotfiles, macOS defaults, and login shell |
| `desktop` | `mise.desktop.toml` | Desktop packages, GUI applications, and `MISE_DARWIN_PROFILE=desktop` |
| `home-server` | `mise.home-server.toml` | Home-server packages, paths, and `MISE_DARWIN_PROFILE=home-server` |

Desktop commands use the defaults directly. Override the host profile for a
home-server command:

```sh
# Desktop Mac
mise bootstrap status --missing

# Home-server Mac
mise -E home-server bootstrap status --missing
```

The early `.miserc.toml` setting is required because platform and host
environments must be selected before `mise.toml` is discovered. An explicit
`-E` overrides the default `desktop` environment; `macos-arm64` remains
automatic on Apple Silicon.

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

From Fish, update the shared mise tools followed by configured Desktop
Homebrew formulae, casks, and Mac App Store packages with one command:

```sh
mupgrade-all
```

The same non-interactive operation is available directly as a mise task:

```sh
mise run upgrade-all
```

Run an individual update group when needed:

```sh
mise run upgrade-tools
mise run upgrade-packages
mise run upgrade-brew-common
mise run upgrade-brew-desktop
```

Update only installed formulae and casks from `tacogips/tap` without a
confirmation prompt:

```sh
mise run upgrade-taco
mupgrade-taco
```

## Temporary packages

Run the latest official qFlipper release without copying it into
`/Applications`:

```sh
mise run shell -- qflipper
```

The task first searches mise's registry. When the name is not present there, it
queries the Homebrew Cask API and verifies the Cask's published SHA-256. DMGs
are stored under mise's cache root and extracted with macOS system tool
`/usr/bin/hdiutil`; its presence and executable permission are checked before
use. Ordinary mise tools are installed with `mise install-into`.
The extracted application is reused from `/tmp/qflipper-<sha256-prefix>` while
that directory exists. The temporary HTTP download cache is pruned after 30
days without reuse. No Fish alias is installed for qFlipper.

Unprefixed names search mise first and Homebrew Cask second. Prefix a name to
select one resolver explicitly:

```sh
mise run shell -- brew-cask:qflipper
mise run shell -- mise:ripgrep
```

For a Cask app, `shell` launches the temporary `.app`. For a mise CLI tool it
starts `$SHELL` with the tool's executable directories prepended to `PATH`.
Pass a command after another `--` to run it directly instead:

```sh
mise run shell -- mise:ripgrep -- rg --version
```

The same temporary installer can run another checksum-pinned HTTPS artifact:

```sh
mise run temp-install -- \
  --name example \
  --version 1.2.3 \
  --url https://example.com/example-1.2.3.tar.gz \
  --sha256 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef \
  --executable bin/example \
  --bin-path bin \
  --format auto \
  -- --help
```

The managed destination is `/tmp/<name>-<sha256-prefix>`. Existing paths are
reused only when their ownership marker and artifact identity (name, URL, and
SHA-256) match; an unrelated path is never overwritten. Add `--dry-run` before
the final `--` to inspect the destination and command without installing or
launching the tool. Use `--install-only` to install and print the executable
path without launching it.
Fish aliases for mise itself and the upgrade tasks are kept separately in
`dotfiles/.config/fish/conf.d/mise-aliases.fish`.

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

Update Neovim plugins and Tree-sitter parsers through the shared mise entry
point, then review and commit the resulting `lazy-lock.json` changes:

```sh
mise run nvim:update
```

Yazi Git plugins are pinned in `package.toml`, and their pinned contents are
checked into the managed dotfiles. Sora colors are shared by Neovim, Ghostty,
Herdr, LazyGit, Yazi, bat/Delta, fzf, and eza. The Karabiner config
includes the migrated ANSI/Kana symbol mappings. Desktop bootstrap applies the
Git-managed Sora sea image to every macOS desktop. Apple Gateway skills are
linked one skill directory at a time so unrelated user skills are preserved.

## AI agent user scope and Riela

`agent-user-scope/` contains the migrated Claude commands, shared Claude/Codex
skills, including the Wrike Gateway skill, Cursor CLI configuration, Peekaboo
MCP configuration, and Cursor skill.
Bootstrap synchronizes only known assets and does not remove skills managed by
Riela or other installers. The old `envrc-generate` skill is intentionally
excluded because this setup does not use direnv.

Codex keeps only `user-skill-router` implicitly visible. Detailed user skills
remain explicitly invocable and are loaded lazily through the router, avoiding
the 2% skill-metadata context limit without removing functionality. Bootstrap
derives the shared, Codex, Claude Code, and Cursor roots from one home-directory
path model instead of maintaining repeated absolute paths.

On desktop hosts, bootstrap installs the Riela application and all user-scope
workflow and skill packages listed in `agent-user-scope/riela-packages.txt`. If
the public `tacogips/riela-packages` checkout is absent, the installer clones it
under the standard checkout root.

GitHub HTTPS authentication uses the `GITHUB_TOKEN` credential helper. Fish
provides `gh-token-export`, `gh-token-save-shared`, `gh-token-refresh`,
`gh-token-reset`, and `gh-clone`. Claude and Codex expose the
`git-precommit-safety-check` user skill for credential review before commit or
push. Bootstrap also installs or updates Herdr's built-in Claude and Codex hooks
under each agent's home configuration while preserving their other settings.

For tracked changes, the Fish prompt shows added line totals in green and
deleted line totals in red next to the branch.

## Provisioning implementation

mise owns declarative packages, tools, dotfiles, defaults, and profile
composition. Custom convergence is implemented as a standard-library Python
package under `scripts/mise_darwin/`; it covers agent assets, Herdr and Riela
integration, Docker configuration, AeroSpace display-topology workspace
assignment, home-server resources, verification, and guarded Nix removal. On
the desktop profile, workspaces 1 and 2 follow the first two external displays
while workspace 9 follows the built-in display; a single external display owns
both workspaces 1 and 2. Run its unit tests with:

```sh
mise run test
```

Only the clean-machine `bootstrap` wrapper and the pre-package Homebrew conflict
hook remain as POSIX shell because both can run before mise installs Python.

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
