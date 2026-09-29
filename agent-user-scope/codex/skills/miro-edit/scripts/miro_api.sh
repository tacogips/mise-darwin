#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${MIRO_API_TOKEN:-}" ]]; then
  echo "MIRO_API_TOKEN is required" >&2
  exit 2
fi

board_url="${MIRO_BOARD_URL:-${KESTRA_WORKGROUP_TOPOLOGY_MIRO_URL:-}}"
if [[ -z "$board_url" ]]; then
  echo "Set MIRO_BOARD_URL or a project-specific *_MIRO_URL variable" >&2
  exit 2
fi

board_id="$(python3 - "$board_url" <<'PY'
import re
import sys
from urllib.parse import unquote

url = sys.argv[1]
match = re.search(r"/board/([^/?#]+)", url)
if not match:
    raise SystemExit("Could not extract Miro board id from URL")
print(unquote(match.group(1)))
PY
)"

encoded_board="$(jq -rn --arg v "$board_id" '$v|@uri')"
api="https://api.miro.com/v2/boards/$encoded_board"

curl_miro() {
  curl -sS \
    -H "Authorization: Bearer $MIRO_API_TOKEN" \
    -H "Accept: application/json" \
    "$@"
}

case "${1:-}" in
  board)
    curl_miro "$api" | jq '{id, name, viewLink}'
    ;;
  items)
    curl_miro "$api/items?limit=50" \
      | jq -r '(.data // [])[] | [.type, .id, ((.data.content // "") | gsub("<[^>]+>"; " ") | gsub("[[:space:]]+"; " ") | .[0:100]), .position.x, .position.y, .geometry.width, .geometry.height] | @tsv'
    ;;
  connectors)
    curl_miro "$api/connectors?limit=50" \
      | jq -r '(.data // [])[] | [.id, (.captions[0].content // ""), .startItem.id, .endItem.id] | @tsv'
    ;;
  patch-shape)
    shape_id="${2:?shape id required}"
    payload="${3:?json payload required}"
    curl_miro -X PATCH "$api/shapes/$shape_id" \
      -H "Content-Type: application/json" \
      --data "$payload" \
      | jq '{id, data, position, geometry, style}'
    ;;
  create-shape)
    payload="${2:?json payload required}"
    curl_miro -X POST "$api/shapes" \
      -H "Content-Type: application/json" \
      --data "$payload" \
      | jq '{id, type, data, position, geometry, style}'
    ;;
  create-connector)
    payload="${2:?json payload required}"
    curl_miro -X POST "$api/connectors" \
      -H "Content-Type: application/json" \
      --data "$payload" \
      | jq '{id, type, captions, startItem, endItem, style}'
    ;;
  *)
    echo "Usage: $0 {board|items|connectors|patch-shape|create-shape|create-connector}" >&2
    exit 2
    ;;
esac
