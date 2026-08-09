function co-review-today
    command codex --dangerously-bypass-approvals-and-sandbox --model gpt-5.6-sol -c 'model_reasoning_effort="high"' exec "Review the code changes made today and improve low-quality code. The review and fixes should cover code that is generally considered low quality, unused code, deprecated code that still remains, unnecessary hardcoding, places that can be made DRY, places that are not aligned with SOLID principles without a clear reason, inappropriate variable names, cases not covered by tests, overlooked considerations, and bugs.

Also review the current git diff and take it into account.
"
end
