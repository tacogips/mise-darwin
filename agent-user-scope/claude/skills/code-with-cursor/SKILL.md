---
name: code-with-cursor
description: Use this skill only when the user explicitly asks you to use $code-with-cursor, explicitly asks you to delegate implementation to Cursor Agent, or explicitly asks for composer-2/composer2 to implement code. This skill packages the concrete task and optional impl-plan, then runs local Cursor Agent headlessly with streaming output so the parent session does not appear stalled.
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
argument-hint: [implementation task or impl-plan path]
user-invocable: true
---

# Code With Cursor

Use this skill only for explicit Cursor delegation requests. Do not use it implicitly for normal Claude implementation work.

If the user did not explicitly ask for `code-with-cursor`, Cursor Agent, or
`composer-2` implementation, do not invoke this skill. In that case, normal
implementation should stay local to Claude.

## Delegation Contract

When this skill is invoked and the resolved branch is an implementation pass,
the implementation itself must be performed by a real `cursor-agent` run.

That rule applies only to the implementation branch of this skill. It does not
require a fake Cursor launch when the correct bounded outcome is review-only,
such as:

- no executable implementation slice can be justified after preflight
- the task is blocked before delegation by missing dependencies or missing repo context
- the skill intentionally falls back to review of the current diff

For implementation passes:

- do not use local write/edit tools for the implementation itself
- local edits are allowed only for temporary prompt/state files needed to launch
  `cursor-agent`
- if `cursor-agent` cannot be started, stop and report a blocker instead of
  implementing locally
- do not claim implementation success unless you observed actual `cursor-agent`
  execution output, such as monitor-helper start output or Cursor NDJSON
  `system/init` or `result` events

## What To Collect First

Before invoking Cursor Agent, gather the minimum concrete context it needs:

- workspace path
- exact implementation task
- acceptance criteria or expected behavior
- relevant file paths or directories
- verification commands if known
- optional `impl-plan` path if one already exists

If an `impl-plan` file already exists, prefer passing the path and telling Cursor to read it first instead of restating the entire plan inline.

## Non-Negotiable Sequence For Generic Impl-Plan Requests

If the user did not name a specific plan file or task:

1. Read `impl-plans/PROGRESS.json` first.
2. Select exactly one active plan or one executable task slice.
3. Read at most one selected plan file.
4. Read at most one relevant repository-native command doc such as `.agents/commands/impl-exec-auto.md` or `.agents/commands/impl-exec-specific.md` if it is needed for the handoff.
5. Launch Cursor after that bounded preflight.

When resolving the selected plan path from `impl-plans/PROGRESS.json`, check
exact candidate paths in this order before doing any directory listing:

1. `impl-plans/<plan-name>.md`
2. `impl-plans/active/<plan-name>.md`
3. `impl-plans/completed/<plan-name>.md`

Only if all exact candidates are missing may you do one narrow lookup scoped to
that exact plan name. Do not start with `impl-plans/active/` as the default
guess, because many repositories keep the authoritative plan file at the top
level.

If `impl-plans/PROGRESS.json` does not exist:

1. Do not keep searching for `impl-plan` files indefinitely.
2. Build one concrete implementation brief from the user's request plus the
   smallest amount of repository context needed.
3. Prefer one failing test, one named file, one named command surface, or one
   obvious diff-adjacent continuation slice.
4. Delegate that single synthesized slice to Cursor immediately.
5. If no concrete implementation slice can be justified, switch to review of
   the current diff instead of speculative implementation.

When step 5 applies, state clearly that the skill resolved to review mode and
that no implementation delegation was attempted.

When extracting active plan names from `impl-plans/PROGRESS.json`, use a query
that returns only plan names, for example:

```bash
jq -r '.plans | to_entries[] | select(.value.status == "In Progress") | .key' impl-plans/PROGRESS.json
```

Do not combine plan-name extraction with task-row flattening in one TSV stream,
because that can cause the parent agent to misparse task identifiers or
historical plan names as the selected plan.

Do not:

- run `rg --files impl-plans`, `find impl-plans`, or similar whole-tree listing before `impl-plans/PROGRESS.json`
- scan the entire `.agents/commands` or `.agents/agents` tree
- read multiple plan files speculatively
- spend the whole run on narrowing without ever delegating

## Impl-Plan Requests

If the user asks to implement from `impl-plan` or `impl-plans` but does not name a specific plan or task, do not send Cursor a vague "implement the impl-plans" prompt.

First narrow the work:

1. If `impl-plans/PROGRESS.json` exists, read it first.
2. Select one concrete non-completed plan. Prefer:
   - a plan already marked `In Progress`
   - otherwise the first plan with executable non-blocked tasks
   If `impl-plans/PROGRESS.json` does not exist, synthesize one concrete slice
   from the user request and local repository evidence instead of trying to
   infer a plan tree.
3. Do not enumerate the entire `impl-plans/` tree before reading `PROGRESS.json`.
4. Read only the selected plan file, not the entire `impl-plans/` tree.
5. Choose one concrete task or one bounded checklist slice from that plan.
6. If the selected task is still broad, reduce it to one file-scoped or failing-test-scoped first pass before delegating.
7. If the repo contains workflow-specific implementation commands such as `.agents/commands/impl-exec-auto.md` or `.agents/commands/impl-exec-specific.md`, mirror those repository rules in the Cursor-facing prompt instead of using a generic "read all plans and code" instruction.
8. If the most recent plan progress log names a concrete blocker or failing assertion, prefer that blocker as the delegated slice instead of a broader architectural continuation.
9. If there is no executable implementation slice, tell Cursor to review the current diff instead of attempting speculative implementation.

## Preferred Execution Path

Use direct local CLI execution with `cursor-agent`, and prefer streaming output:

```bash
cursor-agent --print --output-format stream-json --stream-partial-output \
  --trust --workspace /abs/workspace/path \
  --model composer-2 "First read /abs/impl-plan.md, then implement the task.
Run the requested verification commands. At the end, summarize files changed
and verification results."
```

If there is no `impl-plan`, put the concrete implementation instruction directly in the prompt.

Do not default to plain `--print` text output for long-running implementation tasks, because the parent session can look hung while Cursor is still working.

## Parent-Agent Monitoring

When Claude is calling Cursor from inside another agent run, do not rely on one
blocking foreground `cursor-agent` command if the parent shell/tool surface does
not stream child stdout incrementally.

Prefer the bundled monitor helper:

```bash
~/.claude/skills/code-with-cursor/scripts/cursor-agent-monitor.sh start \
  --state-dir "$state_dir" \
  --workspace /abs/workspace/path \
  --model composer-2 \
  --prompt-file "$prompt_file"
```

Then poll from the parent run:

```bash
~/.claude/skills/code-with-cursor/scripts/cursor-agent-monitor.sh poll --state-dir "$state_dir"
~/.claude/skills/code-with-cursor/scripts/cursor-agent-monitor.sh status --state-dir "$state_dir"
```

Use this monitored path when:

- the parent agent is Codex or Claude
- the user expects visible progress
- the delegated run may take longer than a few seconds

The monitor helper writes Cursor NDJSON to a state directory, starts Cursor in
the background, and lets the parent agent poll concise progress without
silently blocking on a single shell command.

For an implementation pass, this helper is not just a convenience. Its start
output and NDJSON stream are valid evidence that a real `cursor-agent` run was
launched.

## Prompt Contract

The delegated prompt should contain:

1. The implementation request in imperative form.
2. The workspace path and target scope.
3. The exact files or directories to edit when known.
4. The verification commands to run when known.
5. The path to any existing `impl-plan`, with an instruction to read it first.
6. A requirement to summarize files changed and verification results at the end.
7. A requirement to keep emitting streaming output while work is in progress.
8. For impl-plan work, the exact selected plan path and selected task/checklist slice.
9. A requirement to either make concrete file edits or return an explicit blocker that names the blocking plan/task/dependency. Do not allow a silent no-op.
10. When the parent agent synthesized a narrower brief, preserve the user's original request verbatim in a section labeled exactly `Original prompt:`.
11. If the parent agent already named target files, treat those files as the mandatory first edit scope. Do not branch into broader cross-surface reads before the first write unless a directly referenced type/test dependency forces it.
12. For implementation passes, require a real `cursor-agent` launch and forbid satisfying the task via local write/edit tools.

Keep the prompt concrete. Do not paste large repository overviews unless they are required.

## Execution Rules

- Default model: `composer-2`
- Default runner: direct `cursor-agent`
- Default mode: normal implementation mode, not `plan`
- Default output mode: `--print --output-format stream-json --stream-partial-output`
- For a single-pass delegation from another agent, keep using `composer-2` unless the user explicitly asked for another Cursor model.
- Use `--resume <chat-id>` only when continuing an existing Cursor session is clearly better than starting fresh.
- Keep the command simple unless there is a clear need for resume or wrapper behavior.
- Do not let Cursor stop after reading plan files, command docs, or help text. It should either produce a concrete patch, run the requested verification, or return a blocker with exact evidence.
- If this skill is active and the chosen branch is implementation, do not satisfy the task with Claude local write/edit tools. Launch `cursor-agent` or return a blocker.
- When the parent prompt already names exact target files and focused tests, Cursor should begin with those files and make the first concrete edit before expanding into unrelated surfaces such as CLI, GraphQL, or TUI unless compilation or failing tests show that expansion is necessary.
- Do not run package-manager install commands such as `bun install`, `npm install`, `pnpm install`, or `yarn install`, and do not modify lockfiles, unless the user explicitly asked for dependency updates or the task itself is about dependency management. If verification is blocked by missing local dependencies, return that as an explicit environment blocker instead of mutating the workspace.

## Expected Parent Workflow

1. Build or locate the concrete implementation instruction.
2. Prefer an existing `impl-plan` path when available.
3. For generic impl-plan requests, resolve them into one concrete plan/task slice before delegating.
4. When running inside another agent, prefer `~/.claude/skills/code-with-cursor/scripts/cursor-agent-monitor.sh` so the parent can poll progress instead of blocking silently.
5. Treat observed `cursor-agent` launch/output as a required success condition for implementation passes, not as optional telemetry.
6. Inspect Cursor output and surface visible progress back to the user if the delegated work is taking a while.
7. Review and verify any resulting code changes in the parent session before reporting back.

## Runner Selection

Read `references/execution-surfaces.md` when you need to decide between direct `cursor-agent`, the `cursor-cli-agent` wrapper, and non-options such as agents that cannot execute the local `cursor-agent` binary.
