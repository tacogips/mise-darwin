#!/usr/bin/env bash
set -euo pipefail

if ! command -v brew >/dev/null 2>&1; then
  exit 0
fi

# Remove mutually exclusive legacy variants before mise converges packages.
if brew list --cask claude-code >/dev/null 2>&1; then
  brew uninstall --cask claude-code
fi
if brew list --formula riela >/dev/null 2>&1; then
  brew uninstall --formula riela
fi
if brew list --formula tailscale >/dev/null 2>&1; then
  brew services stop tailscale >/dev/null 2>&1 || true
  brew uninstall --formula tailscale
fi
if brew list --formula docker-completion >/dev/null 2>&1; then
  brew unlink docker-completion || true
fi
