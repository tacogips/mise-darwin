#!/usr/bin/env bash
set -euo pipefail

mkdir -p "$HOME/.local/bin" "$HOME/.cache" "$HOME/.local/share"

# Third-party taps without generated API metadata cannot be installed by
# mise's direct brew manager. Homebrew Bundle converges this small remainder.
repo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
profile=${MISE_DARWIN_PROFILE:-desktop}
brewfile="$repo_dir/Brewfile.$profile"
common_brewfile="$repo_dir/Brewfile.common"
if [[ -f "$common_brewfile" ]]; then
  brew bundle check --file "$common_brewfile" >/dev/null 2>&1 || brew bundle --file "$common_brewfile" --no-lock
fi
if [[ -f "$brewfile" ]]; then
  if [[ "$profile" == desktop ]]; then
    brew trust --tap tacogips/tap tonyxiao/tap steipete/tap slp/krunkit nikitabobko/tap
  else
    brew trust --tap slp/krunkit
  fi
  brew bundle check --file "$brewfile" >/dev/null 2>&1 || brew bundle --file "$brewfile" --no-lock
fi


# Retire links left by older standalone installers and Home Manager.
rm -f "$HOME/.local/bin/codex" "$HOME/.local/bin/codex-code-mode-host"
legacy_tmux_agent="$HOME/Library/LaunchAgents/com.taco.tmux-window-title.plist"
if [[ -e "$legacy_tmux_agent" ]]; then
  launchctl bootout "gui/$UID" "$legacy_tmux_agent" 2>/dev/null || true
  rm -f "$legacy_tmux_agent"
fi

# Keep Docker's Homebrew CLI plugin locations visible.
mkdir -p "$HOME/.docker"
docker_config="$HOME/.docker/config.json"
docker_tmp=$(mktemp "${TMPDIR:-/tmp}/mise-darwin-docker.XXXXXX")
trap 'rm -f "$docker_tmp"' EXIT
if [[ -s "$docker_config" ]] && jq -e . "$docker_config" >/dev/null 2>&1; then
  jq '.cliPluginsExtraDirs = (((.cliPluginsExtraDirs // []) + ["/opt/homebrew/lib/docker/cli-plugins", "/usr/local/lib/docker/cli-plugins"]) | unique)' \
    "$docker_config" >"$docker_tmp"
else
  printf '%s\n' '{"cliPluginsExtraDirs":["/opt/homebrew/lib/docker/cli-plugins","/usr/local/lib/docker/cli-plugins"]}' >"$docker_tmp"
fi
mv "$docker_tmp" "$docker_config"
trap - EXIT

if [[ -x /opt/homebrew/bin/podman-mac-helper ]]; then
  /opt/homebrew/bin/podman-mac-helper install || echo "warning: podman-mac-helper setup failed" >&2
fi

if [[ -d /Applications/chilla.app ]]; then
  xattr -rd com.apple.quarantine /Applications/chilla.app 2>/dev/null || true
  codesign --force --deep --sign - /Applications/chilla.app >/dev/null
fi

if command -v ya >/dev/null 2>&1; then
  ya pkg install
fi

developer_dir=/Applications/Xcode.app/Contents/Developer
if [[ -d "$developer_dir" ]]; then
  current=$(/usr/bin/xcode-select -p 2>/dev/null || true)
  if [[ "$current" != "$developer_dir" ]]; then
    sudo /usr/bin/xcode-select -s "$developer_dir"
  fi
fi

if [[ "${MISE_DARWIN_PROFILE:-}" == home-server ]]; then
  "$(dirname "$0")/home-server-apply.sh"
fi
