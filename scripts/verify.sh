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

check_not_nix_symlink() {
  local label=$1
  local path=$2
  local target

  target=$(readlink "$path" 2>/dev/null || true)
  if [[ "$target" == /nix/store/* ]]; then
    printf 'ERR %s (still points into /nix/store)\n' "$label" >&2
    failures=$((failures + 1))
  else
    printf 'ok  %s\n' "$label"
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
check "fish: GitHub token helper" test -f "$HOME/.config/fish/functions/gh-token-save-shared.fish"
check "agent skill: credential guardrail" test -f "$HOME/.agents/skills/git-precommit-safety-check/SKILL.md"
check "agent skill: secure GitHub Actions" test -f "$HOME/.agents/skills/secure-github-action/SKILL.md"
check "agent skill: diagram design" test -f "$HOME/.agents/skills/diagram-design/SKILL.md"
check "agent skill: Wrike Gateway" test -f "$HOME/.agents/skills/wrike-via-gateway/SKILL.md"
check "Claude user command" test -f "$HOME/.claude/commands/user-git-create-pr.md"
check "Claude credential guardrail" test -f "$HOME/.claude/skills/git-precommit-safety-check/SKILL.md"
check "Claude Wrike Gateway skill" test -f "$HOME/.claude/skills/wrike-via-gateway/SKILL.md"
check "Cursor CLI config" test -f "$HOME/.cursor/cli-config.json"
check_not_nix_symlink "Cursor config ownership" "$HOME/.cursor/cli-config.json"

if [[ "$profile" == desktop ]]; then
  check "riela" command -v riela
  check "Riela Codex user skill" test -f "$HOME/.codex/skills/fable-and-improve-codex/SKILL.md"
  check "Riela Claude user skill" test -f "$HOME/.claude/skills/fable-and-improve-codex/SKILL.md"
  check "Cursor Peekaboo skill" test -f "$HOME/.cursor/skills/peekaboo/SKILL.md"

  while IFS= read -r package_id; do
    [[ -n "$package_id" && "$package_id" != \#* ]] || continue
    check "Riela package: $package_id" test -f "$HOME/.riela/packages/$package_id/riela-package.json"
  done <"$(dirname "$0")/../agent-user-scope/riela-packages.txt"
fi

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
