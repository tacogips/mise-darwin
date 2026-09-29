---
name: apple-gateway
description: Diagnose and administer the installed apple-gateway macOS CLI, including permission status and requests, live GraphQL schema inspection, materialized file downloads, configuration validation, and cache pruning. Use for apple-gateway setup, troubleshooting, permissions, or cross-domain CLI administration on Darwin; use the dedicated Apple app skill for Calendar, Reminders, Notes, Mail, notifications, or Clock alarm tasks.
---

# Apple Gateway

Use the installed `apple-gateway` commands for cross-domain administration and
diagnostics. Delegate app data work to `apple-calendar`, `apple-reminders`,
`apple-schedule`, `apple-notes`, `apple-mail`, `apple-notifications`, or
`apple-clock-alarms`.
Treat the live CLI schema and help as authoritative because the source project
can evolve independently of this skill.

## Workflow

1. Confirm the CLI is available with `command -v apple-gateway`.
2. For a read-only request, prefer `apple-gateway-reader`. Fall back to
   `apple-gateway` only if the reader binary is unavailable.
3. Inspect only the relevant live interface:
   - Run `<binary> --help` for command routing.
   - Run `<binary> schema print` to inspect GraphQL fields and input types.
   - Run `apple-gateway permissions status --json` when access may be blocked.
4. Form the narrowest query that satisfies the request. Prefer GraphQL
   variables over interpolating user content into a query string.
5. Parse JSON output with `jq` when useful, preserving the command's error
   envelope and exit status when reporting failures.
6. Summarize the result without exposing unrelated personal data.

Use this general query pattern:

```bash
apple-gateway-reader --pretty graphql \
  --query-file /path/to/query.graphql \
  --variables-file /path/to/variables.json
```

Temporary query and variables files should be created in a task-specific
temporary directory and removed after use.

## Writes and prompts

- Use `apple-gateway`, not `apple-gateway-reader`, for GraphQL mutations.
- Perform a mutation only when the user requested the corresponding change.
- Before a destructive or broad mutation, identify the exact target and state
  the intended effect. Re-query afterward when practical to verify it.
- Do not request permissions merely to inspect their state. Run
  `permissions request --domain ...` only when the user requested access or the
  approved task requires the macOS prompt.
- Treat notification posting and Clock alarm changes as writes.

Supported permission request domains are `calendar`, `reminders`, `notes`,
`notifications`, and `clock-alarms`. Full Disk Access remains a manual macOS
setting.

## Files and cache

Use `apple-gateway file download --key <key>` for `downloadKey` values returned
by GraphQL. Use an explicit `--output-dir` when the user specified a destination.
Do not run `cache prune`, especially `cache prune --all`, unless the user asked
to remove cached data.

## Source checkout

For implementation details or CLI troubleshooting, use
`$HOME/gits/tacogips/apple-gateway`. Read its `AGENTS.md` before working in that
repository, then consult `README.md`, `design-docs/specs/command.md`, and the
relevant schema module. Do not edit the source checkout unless the user asks
for a source change.
