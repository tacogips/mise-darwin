#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

case "$(uname -s)" in
  Linux)
    exec "$script_dir/cursor-agent-monitor-linux.sh" "$@"
    ;;
  Darwin)
    exec "$script_dir/cursor-agent-monitor-darwin.sh" "$@"
    ;;
  *)
    printf 'unsupported platform for cursor-agent-monitor.sh: %s\n' "$(uname -s)" >&2
    exit 1
    ;;
esac
