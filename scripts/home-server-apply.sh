#!/usr/bin/env bash
set -euo pipefail

repo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
data_root=${HOME_SERVER_DATA_ROOT:-/Volumes/Data}
backup_root=${HOME_SERVER_BACKUP_ROOT:-/Volumes/Backup}
service_root=${HOME_SERVER_SERVICE_ROOT:-$HOME/home-server}
etc_root=/etc/darwin-mac-home-server

render_and_install() {
  local source=$1 destination=$2 temp
  temp=$(mktemp "${TMPDIR:-/tmp}/mise-darwin-server.XXXXXX")
  sed \
    -e "s|__SERVICE_ROOT__|$service_root|g" \
    -e "s|__DATA_ROOT__|$data_root|g" \
    -e "s|__BACKUP_ROOT__|$backup_root|g" \
    "$source" >"$temp"
  sudo install -m 0644 "$temp" "$destination"
  rm -f "$temp"
}

sudo install -d -m 0755 "$etc_root"
render_and_install "$repo_dir/home-server/compose.yaml" "$etc_root/compose.yaml"
render_and_install "$repo_dir/home-server/Caddyfile" "$etc_root/Caddyfile"
render_and_install "$repo_dir/home-server/README.md" "$etc_root/README.md"

install -d -m 0755 "$service_root" "$service_root/state" "$service_root/backups"
ln -sfn "$etc_root/compose.yaml" "$service_root/compose.yaml"
ln -sfn "$etc_root/Caddyfile" "$service_root/Caddyfile"
ln -sfn "$etc_root/README.md" "$service_root/README.md"

if [[ -d "$data_root" ]]; then
  install -d -m 0755 "$data_root/Photos" "$data_root/Videos" "$data_root/Files"
else
  echo "data volume is not mounted; skipped $data_root subdirectories" >&2
fi
if [[ -d "$backup_root" ]]; then
  install -d -m 0755 "$backup_root/home-server"
else
  echo "backup volume is not mounted; skipped $backup_root/home-server" >&2
fi

if command -v brew >/dev/null 2>&1 && brew services list | grep -q '^colima '; then
  brew services start colima >/dev/null
fi
