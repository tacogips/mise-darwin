function __agent-loop-run
    set -l loop_name $argv[1]
    set -l runner $argv[2]
    set -l prompt_mode $argv[3]
    set -l loop_intent $argv[4]
    set -l fixed_prompt

    switch $loop_intent
        case implement review
        case '*'
            echo "$loop_name: internal error: unknown loop_intent: $loop_intent" >&2
            return 1
    end

    switch $prompt_mode
        case input codex_delegate_input
            set argv $argv[5..-1]
        case fixed
            set fixed_prompt $argv[5]
            set argv $argv[6..-1]
        case '*'
            echo "$loop_name: internal error: unknown prompt_mode for setup: $prompt_mode" >&2
            return 1
    end

    set -l n $argv[1]
    if test -z "$n"
        __agent-loop-print-usage $loop_name $prompt_mode
        return 1
    end

    if not string match -qr '^[1-9][0-9]*$' -- $n
        echo "$loop_name: n must be a positive integer" >&2
        return 1
    end

    set argv $argv[2..-1]

    set -l prompt

    switch $prompt_mode
        case input codex_delegate_input
            if test (count $argv) -gt 0
                set prompt (string join ' ' -- $argv)
            else if not isatty stdin
                set prompt (cat | string collect)
            else
                __agent-loop-print-usage $loop_name $prompt_mode
                return 1
            end
        case fixed
            if test (count $argv) -ne 0
                __agent-loop-print-usage $loop_name $prompt_mode
                return 1
            end
            set prompt $fixed_prompt
        case '*'
            echo "$loop_name: internal error: unknown prompt_mode for prompt collection: $prompt_mode" >&2
            return 1
    end

    # prompt_mode: input | fixed | codex_delegate_input (see __agent-loop-print-usage / wrappers)
    set -l progress_note
    set -l loop_suffix
    switch $loop_intent
        case implement
            set loop_suffix "Also review the current git diff and take it into account."
        case review
            set loop_suffix "Also review the current git diff and take it into account."
        case '*'
            echo "$loop_name: internal error: unknown loop_intent for finalization: $loop_intent" >&2
            return 1
    end

    switch $prompt_mode
        case codex_delegate_input
            set prompt (
      printf '%s\n%s\n\n%s' \
        "Use \$code-with-cursor for implementation work in this run.

Within this Codex run, do the following:
1. Always preserve the user's request verbatim and pass it to Cursor Agent in a section labeled exactly `Original prompt:`.
2. If there is no impl-plan, synthesize a concrete initial implementation brief yourself and send it to Cursor Agent together with the `Original prompt:` section.
3. If there is an impl-plan, tell Cursor Agent to read it first, but still include the `Original prompt:` section in the Cursor-facing instruction so the original intent is not lost.
4. Delegate implementation through \$code-with-cursor for a single pass only.
5. Wait for the first concrete Cursor result. If Cursor reports a blocker, failing command, or failing test, summarize that result and stop instead of starting another delegated cycle.
6. Review the resulting code yourself with a code-review mindset focused on bugs, regressions, missing tests, architectural drift, and weak reasoning, but keep that review in this Codex run.
7. Do not send follow-up instructions back to Cursor Agent, do not ask it for status again, and do not resume the delegated run unless the user explicitly asks for another pass.
8. Prefer concrete file- and command-level guidance over general advice.
9. At the end, summarize Cursor's implementation status, your review findings, remaining risks, and what still needs follow-up.

Original prompt:
" \
        "$prompt" \
        "$loop_suffix" | string collect
    )
            set progress_note "(Codex delegates one Cursor pass, then reviews locally)..."
        case input fixed
            set prompt (printf '%s\n\n%s' "$prompt" "$loop_suffix" | string collect)
            set progress_note "(agent may stay quiet until it produces text; large repos take longer)..."
        case '*'
            echo "$loop_name: internal error: unknown prompt_mode for finalization: $prompt_mode" >&2
            return 1
    end

    for i in (seq $n)
        echo "[$loop_name] iteration $i of $n $progress_note" >&2
        set -l step_status 0
        switch $runner
            case codex
                command codex --dangerously-bypass-approvals-and-sandbox --model gpt-5.6-sol -c 'model_reasoning_effort="high"' exec "$prompt"
                set step_status $status
            case cursor
                command cursor-agent --yolo --approve-mcps --model composer-2.5 --print --output-format stream-json --stream-partial-output --trust "$prompt"
                set step_status $status
            case '*'
                echo "$loop_name: internal error: unknown runner for iteration: $runner" >&2
                return 1
        end
        if test $step_status -ne 0
            echo "[$loop_name] iteration $i failed (exit $step_status)" >&2
            return $step_status
        end
        echo "[$loop_name] iteration $i of $n finished." >&2
    end
end
