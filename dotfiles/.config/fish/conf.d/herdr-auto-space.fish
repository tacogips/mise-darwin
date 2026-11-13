# Keep directory routing local to Fish; no Herdr plugin or watcher is needed.
function __taco_herdr_auto_space_route
    set -q HERDR_PANE_ID; or return 0
    test -n "$HERDR_PANE_ID"; or return 0
    test "$HERDR_AUTO_SPACE_DISABLE" != 1; or return 0
    command -sq jq; or return 0

    set -l herdr_bin herdr
    if set -q HERDR_BIN_PATH; and test -n "$HERDR_BIN_PATH"
        set herdr_bin "$HERDR_BIN_PATH"
    end
    command -sq "$herdr_bin"; or return 0

    set -l root
    if command -sq git
        set root (command git -C "$PWD" rev-parse --show-toplevel 2>/dev/null | string collect)
    end
    test -n "$root"; or set root "$PWD"
    set -l label (path basename "$root")

    # Herdr resolves launch-time pane aliases after cross-Space moves.
    set -l terminal (command "$herdr_bin" pane get "$HERDR_PANE_ID" 2>/dev/null | command jq -er '.result.pane.terminal_id' 2>/dev/null | string collect)
    test -n "$terminal"; or return 0
    set -l snapshot (command "$herdr_bin" api snapshot 2>/dev/null | string collect)
    test -n "$snapshot"; or return 0

    # NUL-delimited argv preserves spaces and shell metacharacters in labels.
    # Never detach one pane from an existing split layout or choose among
    # duplicate Space labels. A missing Space receives the running pane.
    set -l move_args (printf '%s' "$snapshot" | command jq -jr --arg terminal "$terminal" --arg label "$label" '
        .result.snapshot
        | . as $snapshot
        | [.panes[] | select(.terminal_id == $terminal)]
        | select(length == 1) | .[0] as $pane
        | select([$snapshot.panes[] | select(.tab_id == $pane.tab_id)] | length == 1)
        | [$snapshot.workspaces[] | select(.label == $label)] as $targets
        | if ($targets | length) == 0 then
            ["pane", "move", $pane.pane_id, "--new-workspace", "--label", $label, "--focus"]
          elif ($targets | length) == 1 and $targets[0].workspace_id != $pane.workspace_id then
            ["pane", "move", $pane.pane_id, "--new-tab", "--workspace", $targets[0].workspace_id, "--focus"]
          else [] end
        | .[] | ., "\u0000"
    ' 2>/dev/null | string split0)
    test (count $move_args) -gt 0; or return 0
    command "$herdr_bin" $move_args
end

function __taco_herdr_auto_space_on_pwd --on-variable PWD
    # Optional integration must never print errors or change cd's exit status.
    __taco_herdr_auto_space_route >/dev/null 2>&1
    return 0
end
