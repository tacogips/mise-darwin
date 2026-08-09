#!/usr/bin/env bash
set -euo pipefail

repo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
package_manifest="$repo_dir/agent-user-scope/riela-packages.txt"
packages_checkout=${RIELA_PACKAGES_CHECKOUT:-"$HOME/gits/tacogips/riela-packages"}
packages_dir="$packages_checkout/packages"

if ! command -v riela >/dev/null 2>&1; then
  printf 'warning: riela is not installed; skipping user package installation\n' >&2
  exit 0
fi

if [[ ! -d "$packages_dir" ]]; then
  if [[ -e "$packages_checkout" ]]; then
    printf 'error: %s exists but has no packages directory\n' "$packages_checkout" >&2
    exit 1
  fi
  mkdir -p "$(dirname "$packages_checkout")"
  git clone https://github.com/tacogips/riela-packages.git "$packages_checkout"
fi

while IFS= read -r package_id; do
  [[ -n "$package_id" && "$package_id" != \#* ]] || continue
  package_source="$packages_dir/$package_id"
  if [[ ! -d "$package_source" ]]; then
    printf 'error: required Riela package source is missing: %s\n' "$package_source" >&2
    exit 1
  fi

  printf 'installing Riela user package: %s\n' "$package_id"
  riela package install "$package_id" \
    --source "$package_source" \
    --scope user \
    --overwrite \
    --output json >/dev/null
done <"$package_manifest"

required_skills=(
  "$HOME/.codex/skills/fable-and-improve-codex/SKILL.md"
  "$HOME/.claude/skills/fable-and-improve-codex/SKILL.md"
  "$HOME/.claude/skills/fable-and-improve-opus/SKILL.md"
)
for skill_file in "${required_skills[@]}"; do
  if [[ ! -f "$skill_file" ]]; then
    printf 'error: Riela did not install required user skill: %s\n' "$skill_file" >&2
    exit 1
  fi
done
