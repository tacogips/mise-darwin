#!/usr/bin/env bash
set -euo pipefail

profile=${MISE_DARWIN_PROFILE:-desktop}
failures=0

check() {
  local label=$1
  shift
  if "$@" >/dev/null 2>&1; then
    printf 'ok  %s\n' "$label"
  else
    printf 'ERR %s\n' "$label" >&2
    failures=$((failures + 1))
  fi
}

check "mise config" mise config ls
check "mise doctor" mise doctor
check "fish" command -v fish
check "neovim" command -v nvim
check "git" command -v git
check "ripgrep" command -v rg
check "jq" command -v jq
check "dotfile: nvim" test -e "$HOME/.config/nvim/init.lua"
check "dotfile: fish" test -e "$HOME/.config/fish/config.fish"
check "dotfile: git" test -e "$HOME/.gitconfig"

if [[ -d /Applications/Xcode.app ]]; then
  check "Xcode selection" test "$(xcode-select -p)" = /Applications/Xcode.app/Contents/Developer
  check "Swift" xcrun --find swift
  check "sourcekit-lsp" xcrun --find sourcekit-lsp
fi

if [[ "$profile" == home-server ]]; then
  check "home-server config" test -f /etc/darwin-mac-home-server/compose.yaml
  check "home-server workspace" test -L "$HOME/home-server/compose.yaml"
fi

if (( failures > 0 )); then
  printf '%d verification check(s) failed\n' "$failures" >&2
  exit 1
fi

echo "mise-darwin verification passed for profile: $profile"
