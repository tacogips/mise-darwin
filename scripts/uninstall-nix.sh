#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" != --confirm ]]; then
  cat >&2 <<'EOF'
This permanently removes Nix. First run:
  mise -E macos-arm64 -E desktop run verify

Then invoke:
  mise run nix:uninstall -- --confirm
EOF
  exit 64
fi

if [[ $(uname -s) != Darwin ]]; then
  echo "This task only supports macOS." >&2
  exit 1
fi

if [[ -x /nix/nix-installer ]]; then
  sudo /nix/nix-installer uninstall
elif command -v nix-installer >/dev/null 2>&1; then
  sudo nix-installer uninstall
else
  cat >&2 <<'EOF'
No Determinate Nix installer receipt was found, so automatic removal stopped.
Legacy multi-user Nix installations have installer-specific users, groups,
launch daemons, APFS volumes, and shell edits. Follow the uninstall procedure
for the installer originally used instead of deleting /nix directly.
EOF
  exit 2
fi

sudo launchctl bootout system /Library/LaunchDaemons/org.nixos.nix-garbage-collector.plist 2>/dev/null || true
sudo rm -f /Library/LaunchDaemons/org.nixos.nix-garbage-collector.plist
echo "Nix was removed. Open a new shell and run: mise -E macos-arm64 -E desktop run verify"
