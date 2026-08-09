function __claude-run
    set -l model $argv[1]
    set -e argv[1]

    command env CLAUDE_CODE_EFFORT_LEVEL=high env NODE_OPTIONS='--max-old-space-size=16384' CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 claude --permission-mode bypassPermissions --dangerously-skip-permissions --model $model $argv
end
