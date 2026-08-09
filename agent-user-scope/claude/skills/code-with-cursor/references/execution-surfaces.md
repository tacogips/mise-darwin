# Execution Surfaces

## Preferred Engine: Direct `cursor-agent`

Use direct local `cursor-agent` when the goal is to have Cursor implement code
from the current parent session.

If `code-with-cursor` is already active and the parent run has resolved to an
implementation pass, direct local `cursor-agent` execution is not optional. It
is the required execution surface for the implementation itself. Local
write/edit tools may prepare prompt/state files, but they must not substitute
for the delegated implementation.

Why this is the default:

- it is installed in this environment
- it supports `--print`, `--workspace`, `--model composer-2`, and streaming JSON output
- it is the shortest path from Codex to Cursor execution
- it can emit early partial output so the parent agent does not look stalled

Typical command shape:

```bash
cursor-agent --print --trust --output-format stream-json \
  --stream-partial-output --workspace /repo --model composer-2 "..."
```

Avoid plain `--print` text output for long-running implementation runs unless a
user specifically wants final text only. The streaming JSON form is preferred
because the first event appears immediately and later deltas make progress
visible.

## Preferred Parent-Agent Surface: `scripts/cursor-agent-monitor.sh`

When Codex or Claude is delegating to Cursor from inside its own tool loop, the
parent often cannot rely on child stdout appearing incrementally in the UI even
if Cursor emits NDJSON immediately.

In that case, wrap direct `cursor-agent` with the bundled monitor helper:

```bash
# Codex parent
~/.agents/skills/code-with-cursor/scripts/cursor-agent-monitor.sh start \
  --state-dir "$state_dir" \
  --workspace /repo \
  --model composer-2 \
  --prompt-file "$prompt_file"
~/.agents/skills/code-with-cursor/scripts/cursor-agent-monitor.sh poll --state-dir "$state_dir"
~/.agents/skills/code-with-cursor/scripts/cursor-agent-monitor.sh status --state-dir "$state_dir"

# Claude parent
~/.claude/skills/code-with-cursor/scripts/cursor-agent-monitor.sh start \
  --state-dir "$state_dir" \
  --workspace /repo \
  --model composer-2 \
  --prompt-file "$prompt_file"
~/.claude/skills/code-with-cursor/scripts/cursor-agent-monitor.sh poll --state-dir "$state_dir"
~/.claude/skills/code-with-cursor/scripts/cursor-agent-monitor.sh status --state-dir "$state_dir"
```

For implementation passes under `code-with-cursor`, monitor-helper start output
and Cursor NDJSON events are acceptable evidence that real delegation occurred.

Why this is preferred for parent agents:

- the parent can start Cursor once and then poll progress with short commands
- progress stays visible even if the parent shell surface buffers child stdout
- the raw Cursor NDJSON stream is preserved for later inspection
- the parent can summarize recent tool activity instead of waiting silently

## Optional: `cursor-cli-agent`

Use the wrapper only when session indexing, transcript inspection, or explicit
resume/watch behavior is valuable. It is not the default path for this skill.

Current local status:

- repository exists at `/g/gits/tacogips/cursor-cli-agent`
- direct PATH install is not present in this environment
- wrapper execution is currently via `bun run src/main.ts ...`

That means it is viable as an advanced path, but not the default.

## Not An Execution Surface: Codex `web`

Codex `web` can fetch documentation, web pages, and current references. It
cannot execute the local `cursor-agent` binary.

Use `web` only to gather external context that should then be passed into the
Cursor prompt, for example:

- a current API document
- a linked issue or PR page
- hosted implementation notes

Do not describe `web` as the mechanism that runs Cursor Agent. It is only a
supporting context source.

## Parent Session Handoff Guidance

When delegating from the parent session, pass only the information Cursor needs
to act:

- exact task
- target workspace
- allowed or preferred files
- verification expectations
- existing `impl-plan` path when available

If an `impl-plan` already captures the work, tell Cursor to read that file
first and then implement it. Keep the prompt short and concrete.

If the delegated run is expected to take a while, the parent session should
surface Cursor progress back to the user instead of waiting silently for the
final summary.

For generic impl-plan requests in repositories that maintain
`impl-plans/PROGRESS.json`, do not delegate the entire plan set blindly. The
parent session should first resolve the request into one concrete plan/task
slice, then pass that bounded slice to Cursor together with the repository's
native implementation workflow when one exists.
