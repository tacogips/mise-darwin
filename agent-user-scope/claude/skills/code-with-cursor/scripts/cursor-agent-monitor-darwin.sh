#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  cursor-agent-monitor-darwin.sh start --state-dir DIR --workspace DIR --model MODEL --prompt-file FILE [-- extra cursor-agent args...]
  cursor-agent-monitor-darwin.sh poll --state-dir DIR
  cursor-agent-monitor-darwin.sh status --state-dir DIR

This helper starts Cursor Agent in the background, stores the raw NDJSON stream,
and lets a parent agent poll concise progress updates without blocking on one
opaque foreground command.
EOF
}

can_use_launchd_user() {
  [ "$(uname -s)" = "Darwin" ] || return 1
  command -v launchctl >/dev/null 2>&1 || return 1
  launchctl help >/dev/null 2>&1
}

require_file() {
  local path="$1"
  if [ ! -e "$path" ]; then
    printf 'missing required path: %s\n' "$path" >&2
    exit 1
  fi
}

collapse_text() {
  tr '\n' ' ' | sed -E 's/[[:space:]]+/ /g; s/^ //; s/ $//'
}

render_json_line() {
  local line="$1"
  if ! printf '%s\n' "$line" | jq -e . >/dev/null 2>&1; then
    return 0
  fi

  printf '%s\n' "$line" | jq -r '
    def trunc:
      if type == "string" and (length > 180) then .[0:177] + "..."
      else .
      end;
    def text_chunk:
      ([.message.content[]? | select(.type == "text") | .text] | join(" ")) | gsub("\\s+"; " ") | trunc;
    def tool_key:
      (.tool_call | keys[0] // "");
    def tool_args:
      .tool_call[(.tool_call | keys[0] // "")].args // {};
    if .type == "system" and .subtype == "init" then
      "INIT model=" + (.model // "?") + " cwd=" + (.cwd // "?")
    elif .type == "assistant" then
      (text_chunk) as $text
      | if ($text | length) == 0 then empty else "ASSISTANT " + $text end
    elif .type == "tool_call" then
      (tool_key) as $key
      | (tool_args) as $args
      | if $key == "readToolCall" then
          "TOOL " + (.subtype // "?") + " read " + (($args.path // "?") | tostring)
        elif $key == "writeToolCall" then
          "TOOL " + (.subtype // "?") + " write " + (($args.path // "?") | tostring)
        elif (($args.command // "") | tostring | length) > 0 then
          "TOOL " + (.subtype // "?") + " " + $key + " " + (($args.command | tostring | gsub("\\s+"; " ")) | trunc)
        else
          "TOOL " + (.subtype // "?") + " " + $key
        end
    elif .type == "result" then
      "RESULT " + (.subtype // "unknown") + " duration_ms=" + ((.duration_ms // 0) | tostring)
    else
      empty
    end
  ' | collapse_text
}

start_run() {
  local state_dir=""
  local workspace=""
  local model=""
  local prompt_file=""
  local extra_args=()

  while [ "$#" -gt 0 ]; do
    case "$1" in
      --state-dir)
        state_dir="$2"
        shift 2
        ;;
      --workspace)
        workspace="$2"
        shift 2
        ;;
      --model)
        model="$2"
        shift 2
        ;;
      --prompt-file)
        prompt_file="$2"
        shift 2
        ;;
      --)
        shift
        extra_args=("$@")
        break
        ;;
      *)
        printf 'unknown start argument: %s\n' "$1" >&2
        usage
        exit 1
        ;;
    esac
  done

  if [ -z "$state_dir" ] || [ -z "$workspace" ] || [ -z "$model" ] || [ -z "$prompt_file" ]; then
    usage
    exit 1
  fi

  require_file "$prompt_file"
  mkdir -p "$state_dir"

  local raw_log="$state_dir/raw.ndjson"
  local stderr_log="$state_dir/stderr.log"
  local pid_file="$state_dir/pid"
  local exit_file="$state_dir/exit-code"
  local offset_file="$state_dir/line-offset"
  local runner_script="$state_dir/run-cursor.sh"
  local launchd_domain_file="$state_dir/launchd-domain"
  local launchd_label_file="$state_dir/launchd-label"
  local launchd_plist="$state_dir/launchd-agent.plist"

  : > "$raw_log"
  : > "$stderr_log"
  printf '0\n' > "$offset_file"
  rm -f "$exit_file"
  rm -f "$launchd_domain_file" "$launchd_label_file" "$launchd_plist"

  {
    printf '#!/usr/bin/env bash\n'
    printf 'set +e\n'
    printf 'cursor-agent --print --output-format stream-json --stream-partial-output --trust'
    printf ' --workspace %q' "$workspace"
    printf ' --model %q' "$model"
    for arg in "${extra_args[@]}"; do
      printf ' %q' "$arg"
    done
    printf ' "$(cat %q)" >%q 2>%q\n' "$prompt_file" "$raw_log" "$stderr_log"
    printf 'status=$?\n'
    printf 'printf %q "$status" > %q\n' '%s\n' "$exit_file"
  } > "$runner_script"
  chmod +x "$runner_script"

  printf 'STATE_DIR=%s\n' "$state_dir"
  printf 'RAW_LOG=%s\n' "$raw_log"
  printf 'STDERR_LOG=%s\n' "$stderr_log"
  printf 'EXIT_FILE=%s\n' "$exit_file"
  printf 'RUNNER_SCRIPT=%s\n' "$runner_script"

  if can_use_launchd_user; then
    # Run Cursor under a temporary LaunchAgent rather than a persistent service.
    # Nested Codex/Claude shell commands can reap plain background children
    # before they flush NDJSON or exit status, but a launchd-managed child
    # survives that parent-command teardown and can be booted out after exit.
    local launchd_domain launchd_label
    launchd_domain="gui/$(id -u)"
    launchd_label="code-with-cursor.$(basename "$state_dir" | tr -c 'A-Za-z0-9_.-' '-')"
    cat > "$launchd_plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${launchd_label}</string>
  <key>ProgramArguments</key>
  <array>
    <string>${runner_script}</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <false/>
</dict>
</plist>
EOF
    if launchctl bootstrap "$launchd_domain" "$launchd_plist" >/dev/null 2>&1; then
      launchctl kickstart -k "$launchd_domain/$launchd_label" >/dev/null 2>&1 || true
      printf '%s\n' "$launchd_domain" > "$launchd_domain_file"
      printf '%s\n' "$launchd_label" > "$launchd_label_file"
      printf 'LAUNCHD_DOMAIN=%s\n' "$launchd_domain"
      printf 'LAUNCHD_LABEL=%s\n' "$launchd_label"
      printf 'LAUNCHD_PLIST=%s\n' "$launchd_plist"
      return 0
    fi
  fi

  nohup "$runner_script" >/dev/null 2>&1 < /dev/null &
  local pid="$!"
  printf '%s\n' "$pid" > "$pid_file"
  printf 'PID=%s\n' "$pid"
}

poll_run() {
  local state_dir=""
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --state-dir)
        state_dir="$2"
        shift 2
        ;;
      *)
        printf 'unknown poll argument: %s\n' "$1" >&2
        usage
        exit 1
        ;;
    esac
  done

  if [ -z "$state_dir" ]; then
    usage
    exit 1
  fi

  local raw_log="$state_dir/raw.ndjson"
  local offset_file="$state_dir/line-offset"
  require_file "$raw_log"
  require_file "$offset_file"

  local current_offset current_lines
  current_offset="$(cat "$offset_file")"
  current_lines="$(wc -l < "$raw_log" | tr -d ' ')"

  if [ "$current_lines" -le "$current_offset" ]; then
    exit 0
  fi

  sed -n "$((current_offset + 1)),$((current_lines))p" "$raw_log" | while IFS= read -r line; do
    local rendered=""
    rendered="$(render_json_line "$line")"
    if [ -n "$rendered" ]; then
      printf '%s\n' "$rendered"
    fi
  done

  printf '%s\n' "$current_lines" > "$offset_file"
}

status_run() {
  local state_dir=""
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --state-dir)
        state_dir="$2"
        shift 2
        ;;
      *)
        printf 'unknown status argument: %s\n' "$1" >&2
        usage
        exit 1
        ;;
    esac
  done

  if [ -z "$state_dir" ]; then
    usage
    exit 1
  fi

  local pid_file="$state_dir/pid"
  local exit_file="$state_dir/exit-code"
  local stderr_log="$state_dir/stderr.log"
  local launchd_domain_file="$state_dir/launchd-domain"
  local launchd_label_file="$state_dir/launchd-label"
  local launchd_plist="$state_dir/launchd-agent.plist"

  if [ -f "$exit_file" ]; then
    if [ -f "$launchd_domain_file" ] && [ -f "$launchd_label_file" ] && [ -f "$launchd_plist" ]; then
      launchctl bootout "$(cat "$launchd_domain_file")" "$launchd_plist" >/dev/null 2>&1 || true
    fi
    printf 'STATUS=exited\n'
    printf 'EXIT_CODE=%s\n' "$(cat "$exit_file")"
    if [ -s "$stderr_log" ]; then
      printf 'STDERR_TAIL=%s\n' "$(tail -n 5 "$stderr_log" | collapse_text)"
    fi
    exit 0
  fi

  if [ -f "$launchd_domain_file" ] && [ -f "$launchd_label_file" ]; then
    local launchd_domain launchd_label
    launchd_domain="$(cat "$launchd_domain_file")"
    launchd_label="$(cat "$launchd_label_file")"
    if launchctl print "$launchd_domain/$launchd_label" >/dev/null 2>&1; then
      printf 'STATUS=running\n'
      printf 'LAUNCHD_DOMAIN=%s\n' "$launchd_domain"
      printf 'LAUNCHD_LABEL=%s\n' "$launchd_label"
      exit 0
    fi
    printf 'STATUS=unknown\n'
    printf 'LAUNCHD_DOMAIN=%s\n' "$launchd_domain"
    printf 'LAUNCHD_LABEL=%s\n' "$launchd_label"
    exit 0
  fi

  require_file "$pid_file"

  local pid
  pid="$(cat "$pid_file")"

  if kill -0 "$pid" >/dev/null 2>&1; then
    printf 'STATUS=running\n'
    printf 'PID=%s\n' "$pid"
    exit 0
  fi

  printf 'STATUS=unknown\n'
  printf 'PID=%s\n' "$pid"
}

subcommand="${1:-}"
if [ $# -gt 0 ]; then
  shift
fi

case "$subcommand" in
  start)
    start_run "$@"
    ;;
  poll)
    poll_run "$@"
    ;;
  status)
    status_run "$@"
    ;;
  *)
    usage
    exit 1
    ;;
esac
