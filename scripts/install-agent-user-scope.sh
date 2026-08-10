#!/usr/bin/env bash
set -euo pipefail

repo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
source_root="$repo_dir/agent-user-scope"
profile=${MISE_DARWIN_PROFILE:-desktop}

sync_directory() {
  local source_dir=$1
  local target_dir=$2

  mkdir -p "$(dirname "$target_dir")" "$target_dir"
  rsync -a --delete "$source_dir/" "$target_dir/"
}

sync_file() {
  local source_file=$1
  local target_file=$2

  mkdir -p "$(dirname "$target_file")"
  rsync -a "$source_file" "$target_file"
}

# Codex and other OpenAI-compatible agents discover shared user skills here.
for source_dir in "$source_root"/agents/skills/*; do
  [[ -d "$source_dir" ]] || continue
  sync_directory "$source_dir" "$HOME/.agents/skills/$(basename "$source_dir")"
done

# Wrike Gateway is shared by Codex-compatible agents and Claude Code. Keep one
# canonical copy in the shared skill source and synchronize it to both roots.
sync_directory \
  "$source_root/agents/skills/wrike-via-gateway" \
  "$HOME/.claude/skills/wrike-via-gateway"

# Claude Code still uses its own command and skill roots.
for source_file in "$source_root"/claude/commands/*.md; do
  [[ -f "$source_file" ]] || continue
  sync_file "$source_file" "$HOME/.claude/commands/$(basename "$source_file")"
done

# Remove the old pre-user-prefix command names only when they are still Home
# Manager links. Real user files with those names are never touched.
legacy_claude_commands=(
  add-local-command.md
  add-local-subagent.md
  cc.md
  commit-diff.md
  cont-handover.md
  eng.md
  handover.md
  output-design.md
  read-commit-logs.md
  reload.md
  show-github-url.md
)
for command_name in "${legacy_claude_commands[@]}"; do
  command_path="$HOME/.claude/commands/$command_name"
  if [[ -L "$command_path" && $(readlink "$command_path") == /nix/store/* ]]; then
    rm "$command_path"
  fi
done
for source_dir in "$source_root"/claude/skills/*; do
  [[ -d "$source_dir" ]] || continue
  sync_directory "$source_dir" "$HOME/.claude/skills/$(basename "$source_dir")"
done

# Cursor's base CLI policy applied on both Darwin hosts. Peekaboo is a desktop
# package, so its MCP server and skill are installed only for that profile.
sync_file "$source_root/cursor/cli-config.json" "$HOME/.cursor/cli-config.json"
if [[ "$profile" == desktop ]]; then
  sync_file "$source_root/cursor/mcp.json" "$HOME/.cursor/mcp.json"
  sync_directory "$source_root/cursor/skills/peekaboo" "$HOME/.cursor/skills/peekaboo"
fi
