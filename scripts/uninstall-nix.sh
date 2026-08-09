#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
usage: uninstall-nix.sh --confirm [--dry-run]

Permanently remove nix-darwin and Nix from macOS. Run the profile bootstrap
and verify task first. --dry-run performs preflight checks and prints the
destructive operations without changing the system.
EOF
}

confirmed=false
dry_run=false
for argument in "$@"; do
  case "$argument" in
    --confirm) confirmed=true ;;
    --dry-run) dry_run=true ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      usage >&2
      exit 64
      ;;
  esac
done

if [[ "$confirmed" != true ]]; then
  usage >&2
  exit 64
fi
if [[ $(uname -s) != Darwin ]]; then
  echo "This task only supports macOS." >&2
  exit 1
fi

current_user=$(id -un)
user_home=$(dscl . -read "/Users/$current_user" NFSHomeDirectory 2>/dev/null | awk '{print $2}')
if [[ -z "$user_home" || "$user_home" != /Users/* || "$user_home" == /Users ]]; then
  printf 'error: refusing to use unexpected user home: %s\n' "${user_home:-<empty>}" >&2
  exit 1
fi

profile=${MISE_DARWIN_PROFILE:-desktop}
repo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
failures=0

preflight_error() {
  printf 'error: %s\n' "$1" >&2
  failures=$((failures + 1))
}

login_shell=$(dscl . -read "/Users/$current_user" UserShell 2>/dev/null | awk '{print $2}')
if [[ "$login_shell" == /nix/* || ! -x "$login_shell" ]]; then
  preflight_error "login shell must be switched from Nix to an existing Homebrew shell (current: ${login_shell:-unknown})"
fi

managed_roots=(
  "$user_home/.config"
  "$user_home/.local/bin"
  "$user_home/.agents"
  "$user_home/.claude"
  "$user_home/.codex"
  "$user_home/.cursor"
  "$user_home/Library/LaunchAgents"
)
for managed_root in "${managed_roots[@]}"; do
  [[ -d "$managed_root" ]] || continue
  while IFS= read -r nix_link; do
    preflight_error "user-scope link still points into the Nix Store: $nix_link"
  done < <(find "$managed_root" -type l -lname '/nix/store/*' -print 2>/dev/null)
done

if ! MISE_DARWIN_PROFILE="$profile" "$repo_dir/scripts/verify.sh"; then
  preflight_error "mise-darwin verification failed for profile: $profile"
fi

volume_info=$(diskutil info /nix 2>/dev/null || true)
if [[ -z "$volume_info" ]]; then
  preflight_error "/nix is not a mounted volume"
else
  mount_point=$(awk -F: '/Mount Point/ {sub(/^[[:space:]]+/, "", $2); print $2}' <<<"$volume_info")
  filesystem=$(awk -F: '/Type \(Bundle\)/ {sub(/^[[:space:]]+/, "", $2); print $2}' <<<"$volume_info")
  if [[ "$mount_point" != /nix || "$filesystem" != apfs ]]; then
    preflight_error "refusing to delete a volume that is not the APFS /nix mount"
  fi
fi

if ((failures > 0)); then
  printf '%d preflight check(s) failed; Nix was not removed\n' "$failures" >&2
  exit 2
fi

backup_root="/var/backups/mise-darwin-nix-uninstall-$(date +%Y%m%d-%H%M%S)"
darwin_uninstaller=/run/current-system/sw/bin/darwin-uninstaller
determinate_installer=
if [[ -x /nix/nix-installer ]]; then
  determinate_installer=/nix/nix-installer
elif command -v nix-installer >/dev/null 2>&1; then
  determinate_installer=$(command -v nix-installer)
fi

if [[ "$dry_run" == true ]]; then
  printf 'dry-run: would back up modified system files under %s\n' "$backup_root"
  [[ -x "$darwin_uninstaller" ]] && printf 'dry-run: would run %s\n' "$darwin_uninstaller"
  if [[ -n "$determinate_installer" ]]; then
    printf 'dry-run: would run %s uninstall\n' "$determinate_installer"
  else
    cat <<'EOF'
dry-run: would perform the official legacy macOS multi-user uninstall:
  - stop and remove Nix LaunchDaemons
  - remove nixbld users and group
  - remove the /nix fstab and synthetic.conf entries
  - remove Nix user/root state and /etc/nix
  - delete the verified APFS volume mounted at /nix
EOF
  fi
  exit 0
fi

sudo mkdir -p "$backup_root"

# nix-darwin must be removed while its current system closure is still
# available. Its uninstaller restores the installer-owned Nix daemon first.
if [[ -x "$darwin_uninstaller" ]]; then
  sudo "$darwin_uninstaller" </dev/null
fi

if [[ -n "$determinate_installer" ]]; then
  sudo "$determinate_installer" uninstall
  echo "Nix was removed by Determinate Nix Installer. Reboot, then run the mise verify task."
  exit 0
fi

backup_file() {
  local source_file=$1
  local backup_name=$2
  if [[ -e "$source_file" || -L "$source_file" ]]; then
    sudo cp -a "$source_file" "$backup_root/$backup_name"
  fi
}

rewrite_without_nix_mount() {
  local source_file=$1
  local mode=$2
  local temporary_file

  [[ -f "$source_file" ]] || return 0
  temporary_file=$(mktemp "${TMPDIR:-/tmp}/mise-darwin-uninstall.XXXXXX")
  if [[ "$mode" == fstab ]]; then
    awk '$2 != "/nix" && $1 != "LABEL=Nix\\040Store"' "$source_file" >"$temporary_file"
  else
    awk '$1 != "nix"' "$source_file" >"$temporary_file"
  fi
  sudo install -m 0644 "$temporary_file" "$source_file"
  rm "$temporary_file"
}

rewrite_without_nix_shell_block() {
  local destination_file=$1
  local source_file=$destination_file
  local temporary_file

  if [[ -L "$destination_file" ]]; then
    source_file="$destination_file.backup-before-nix"
    if [[ ! -f "$source_file" ]]; then
      printf 'error: cannot replace Nix-managed shell file without installer backup: %s\n' "$destination_file" >&2
      exit 1
    fi
  fi
  [[ -f "$source_file" ]] || return 0
  temporary_file=$(mktemp "${TMPDIR:-/tmp}/mise-darwin-uninstall.XXXXXX")
  awk '
    /^# Nix$/ { skipping = 1; next }
    skipping && /^# End Nix$/ { skipping = 0; next }
    !skipping { print }
  ' "$source_file" >"$temporary_file"
  if [[ -L "$destination_file" ]]; then
    sudo rm -f "$destination_file"
  fi
  sudo install -m 0644 "$temporary_file" "$destination_file"
  rm "$temporary_file"
}

for plist in \
  /Library/LaunchDaemons/org.nixos.nix-daemon.plist \
  /Library/LaunchDaemons/org.nixos.darwin-store.plist \
  /Library/LaunchDaemons/org.nixos.nix-garbage-collector.plist; do
  if [[ -e "$plist" ]]; then
    backup_file "$plist" "$(basename "$plist")"
    sudo launchctl bootout system "$plist" 2>/dev/null || sudo launchctl unload "$plist" 2>/dev/null || true
    sudo rm -f "$plist"
  fi
done

while IFS= read -r build_user; do
  [[ "$build_user" =~ ^_nixbld[0-9]+$ ]] || continue
  sudo dscl . -delete "/Users/$build_user"
done < <(dscl . -list /Users | awk '/^_nixbld[0-9]+$/')
if dscl . -read /Groups/nixbld >/dev/null 2>&1; then
  sudo dscl . -delete /Groups/nixbld
fi

backup_file /etc/fstab fstab
backup_file /etc/synthetic.conf synthetic.conf
rewrite_without_nix_mount /etc/fstab fstab
rewrite_without_nix_mount /etc/synthetic.conf synthetic

for shell_file in /etc/zshrc /etc/bashrc /etc/bash.bashrc; do
  if [[ -f "$shell_file" || -L "$shell_file" ]]; then
    backup_file "$shell_file" "$(basename "$shell_file")"
    rewrite_without_nix_shell_block "$shell_file"
  fi
done

user_nix_paths=(
  "$user_home/.nix-profile"
  "$user_home/.nix-defexpr"
  "$user_home/.nix-channels"
  "$user_home/.local/share/nix"
  "$user_home/.local/state/nix"
  "$user_home/.cache/nix"
)
sudo rm -rf -- \
  /etc/nix \
  /var/root/.nix-profile \
  /var/root/.nix-defexpr \
  /var/root/.nix-channels
rm -rf -- "${user_nix_paths[@]}"

# The volume identity and mount point were validated during preflight. Use
# diskutil instead of recursively deleting /nix.
sudo diskutil apfs deleteVolume /nix

cat <<EOF
Legacy multi-user Nix was removed.
System-file backups: $backup_root
Reboot macOS, open a new shell, and run:
  mise -E macos-arm64 -E $profile run verify
EOF
