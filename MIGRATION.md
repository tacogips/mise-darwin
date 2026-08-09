# Migration status

Source: `tacogips/nix/nixos/darwin` and its shared Home Manager modules.

## Migrated

- Versioned Go, Rust, Python, Node, Bun, Zig, Java, and Julia toolchains
- Common CLI packages and Neovim LSP/formatter dependencies
- Desktop Homebrew formulae, casks, private taps, and Mac App Store apps
- Home-server packages, PiGallery2 Compose template, Caddy template, runtime directories, and volume directories
- Fish activation, environment variables, common aliases/functions, and Kinko shared-secret import
- Git identity, GitHub HTTPS URL conversion, token credential helper, and Delta integration
- Ghostty, Herdr, AeroSpace, full ANSI/Kana Karabiner mapping, LazyGit, and Yazi configuration
- macOS keyboard, trackpad, Finder, Dock, Safari, and control-center defaults
- Xcode selection and host toolchain environment
- Docker CLI plugin paths, Podman helper, Chilla signing workaround, and retired Codex/tmux links
- Hierarchical Neovim Lua configuration with lazy.nvim, LSP, completion, formatting, Telescope, Yazi, and filetype modules
- Pinned Yazi Git plugin, Gruvbox flavor, git-diff tree, enter-directory behavior, and custom keymap
- Apple Gateway, Calendar, Clock, Mail, Notes, Notifications, Reminders, and Schedule user skills
- Profile dry-runs, verification task, lockfile, and guarded Nix uninstall task

## Follow-up before deleting `tacogips/nix`

- Compare the new Fish aliases/functions with any personal commands still used from shared Home Manager.
- Run Neovim once, review the generated `lazy-lock.json`, and commit it.
- Apply and verify both physical hosts. Only then run `mise run nix:uninstall -- --confirm` on each host.

The old Nix garbage-collector LaunchDaemon is intentionally not recreated. It
is removed with Nix and has no purpose after migration.
