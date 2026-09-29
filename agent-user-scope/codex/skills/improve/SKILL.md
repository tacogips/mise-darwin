---
name: improve
description: Use when the user asks the current AI session to self-review its own recent work and improve it before final handoff, including prompts such as "do self review about your work and improve it".
allowed-tools: Bash, Read, Edit, MultiEdit, Grep, Glob
argument-hint: [optional focus area]
user-invocable: true
---

# Improve

Treat this as an instruction to do self review about your work and improve it.

## Workflow

1. Review the current work product, including relevant diffs, generated files, tests, and verification output.
2. Identify concrete issues: correctness bugs, incomplete requirements, unsafe assumptions, stale docs, excessive scope, missing verification, formatting problems, or brittle behavior.
3. Fix real issues immediately when the fix is within scope and low risk. Preserve unrelated user changes.
4. Re-run the relevant verification after edits.
5. Report what you found, what you changed, and any remaining risk.

Do not treat this as a request for a long retrospective. If the review finds no actionable issue, say that plainly and keep the response short.
