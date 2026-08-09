function codex-step-loop
    set -l loop_name codex-step-loop
    set -l n $argv[1]
    set -l sleep_minutes $argv[2]

    if test -z "$n" -o -z "$sleep_minutes"
        echo "usage: $loop_name n sleep_minutes [prompt]" >&2
        echo "   or: cat prompt.md | $loop_name n sleep_minutes" >&2
        return 1
    end

    if not string match -qr '^[1-9][0-9]*$' -- $n
        echo "$loop_name: n must be a positive integer" >&2
        return 1
    end

    if not string match -qr '^(0|[1-9][0-9]*)(\.[0-9]+)?$' -- $sleep_minutes
        echo "$loop_name: sleep_minutes must be a non-negative number" >&2
        return 1
    end

    set argv $argv[3..-1]
    set -l prompt

    if test (count $argv) -gt 0
        set prompt (string join ' ' -- $argv)
    else if not isatty stdin
        set prompt (cat | string collect)
    else
        echo "usage: $loop_name n sleep_minutes [prompt]" >&2
        echo "   or: cat prompt.md | $loop_name n sleep_minutes" >&2
        return 1
    end

    set prompt (printf '%s\n\n%s' "$prompt" "Also review the current git diff and take it into account." | string collect)
    set -l progress_note "(agent may stay quiet until it produces text; large repos take longer)..."
    set -l sleep_seconds (math "$sleep_minutes * 60")

    for i in (seq $n)
        echo "[$loop_name] iteration $i of $n $progress_note" >&2
        command codex --dangerously-bypass-approvals-and-sandbox --model gpt-5.6-sol -c 'model_reasoning_effort="high"' exec "$prompt"
        set -l step_status $status
        if test $step_status -ne 0
            echo "[$loop_name] iteration $i failed (exit $step_status)" >&2
            return $step_status
        end
        echo "[$loop_name] iteration $i of $n finished." >&2
        if test $i -lt $n
            set -l next_iteration (math "$i + 1")
            echo "[$loop_name] sleeping for $sleep_minutes minute(s) before iteration $next_iteration." >&2
            sleep $sleep_seconds
        end
    end
end
