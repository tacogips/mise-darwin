function __agent-loop-print-usage
    set -l loop_name $argv[1]
    set -l prompt_mode $argv[2]

    switch $prompt_mode
        case input codex_delegate_input
            echo "usage: $loop_name n [prompt]" >&2
            echo "   or: cat prompt.md | $loop_name n" >&2
        case fixed
            echo "usage: $loop_name n" >&2
        case '*'
            echo "$loop_name: internal error: unknown prompt_mode for usage: $prompt_mode" >&2
            return 1
    end
end
