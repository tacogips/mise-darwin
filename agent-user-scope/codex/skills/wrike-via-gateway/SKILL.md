---
name: wrike-via-gateway
description: Use when reading or changing Wrike data (tasks, folders, projects, spaces, comments, attachments, timelogs, custom fields, workflows, webhooks, contacts, groups) with the wrike-gateway CLI. Covers choosing between wrike-gateway-reader, wrike-gateway-writer, and wrike-gateway-admin, credential injection through kinko, schema inspection, GraphQL query and mutation patterns, pagination, attachment transfer, and stable error handling.
allowed-tools: Read, Grep, Glob, Bash
---

# Wrike Via Gateway

Use this skill when the task is to read or change data in a Wrike account
through the `wrike-gateway` CLI. The CLI speaks a project-owned GraphQL-shaped
contract; there is no raw REST, arbitrary URL, or upstream passthrough.

## Choose the Binary by Least Privilege

| Binary | Can do | Cannot do |
| --- | --- | --- |
| `wrike-gateway-reader` | Query only | any mutation |
| `wrike-gateway-writer` | Query plus create/update/upload | any delete |
| `wrike-gateway-admin` | everything, including reviewed deletes | - |

Always pick the lowest tier that covers the task. The boundaries are enforced
at link time and at runtime: a delete through the writer fails locally with
`CAPABILITY_DENIED` before any network call. Do not "upgrade" to admin to make
an error go away unless the task genuinely requires a delete.

Deletes move Wrike tasks/folders to the Recycle Bin rather than erasing them.
Delete only objects the current task created or that the user explicitly named.

## Credentials

Never place a token or secret on a command line or in output. Never use
`kinko show --reveal`, `kinko get --reveal`, or `kinko exec --all` for Wrike.
Inject only the required allowlisted keys through kinko.

Expected kinko keys:

| Key | Purpose | Handling |
| --- | --- | --- |
| `WRIKE_GATEWAY_ACCESS_TOKEN` | permanent Wrike bearer token | secret; preferred when present |
| `WRIKE_GATEWAY_API_BASE_URL` | Wrike data-center API base URL | required with the permanent token |
| `WRIKE_GATEWAY_API_CLIENT_ID` | OAuth2 application client id | use only for OAuth mode |
| `WRIKE_GATEWAY_API_CLIENT_SECRET` | OAuth2 application client secret | secret; use only for OAuth mode |

Check key presence without revealing values. `kinko get` redacts the value
unless `--reveal` is explicitly supplied:

```bash
kinko get WRIKE_GATEWAY_ACCESS_TOKEN
kinko get WRIKE_GATEWAY_API_BASE_URL
```

Kinko resolves secrets by profile and path scope. If a known key is not found,
use `kinko show --all-scopes` without `--reveal` to locate its scope, then pass
the corresponding `--profile` or `--path` to `kinko exec`. Do not copy a value
between scopes merely to make a command work.

Choose credentials in this order:

1. If both `WRIKE_GATEWAY_ACCESS_TOKEN` and `WRIKE_GATEWAY_API_BASE_URL` are
   present, use permanent-token mode for reads and writes. The gateway itself
   gives a non-empty permanent token precedence over OAuth state.
2. Use OAuth mode only when the permanent-token pair is unavailable.
3. Do not run `auth oauth2` or replace stored credentials in response to an
   authorization error while a permanent token is available. First retry the
   original operation once with the permanent-token pair.

Permanent-token mode:

```bash
kinko exec --force --env WRIKE_GATEWAY_ACCESS_TOKEN,WRIKE_GATEWAY_API_BASE_URL -- \
  wrike-gateway-reader graphql query '{ account { id name } }'
```

OAuth fallback:

```bash
kinko exec --force --env WRIKE_GATEWAY_API_CLIENT_ID,WRIKE_GATEWAY_API_CLIENT_SECRET -- \
  wrike-gateway-reader graphql query '{ account { id name } }'
```

For an OAuth preflight:

```bash
kinko exec --force --env WRIKE_GATEWAY_API_CLIENT_ID,WRIKE_GATEWAY_API_CLIENT_SECRET -- \
  wrike-gateway-reader auth status
```

`auth status` prints mode, host, expiry, and whether refresh state exists; it
never prints a token. An expired OAuth access token with
`refreshStateAvailable: true` refreshes automatically on the next call. If no
usable credential exists, `auth oauth2` opens a browser consent flow (needs a
human or a browser agent to click Allow).

Run OAuth operations sequentially when refresh may occur. Concurrent commands
can race while Wrike rotates a refresh token, causing one command to report
`invalid_grant` even though another command refreshed successfully.

Once an OAuth login has completed, stored token state is read from the
kinko-backed credential store without any environment injection, so a bare
`wrike-gateway-reader graphql query ...` may already work. Still prefer the
explicit `kinko exec --env ...` form so credential selection is deterministic
and automatic refresh has the OAuth client keys it needs.

## Discover the Contract

The schema is rendered locally per binary and never fetched from Wrike:

```bash
wrike-gateway-reader graphql schema   # Query fields only
wrike-gateway-admin graphql schema    # full contract including deletes
```

Grep it rather than guessing field or argument names:

```bash
wrike-gateway-admin graphql schema | grep -A 8 '^input CreateTaskInput'
wrike-gateway-reader graphql schema | grep -E '^\s+(task|tasks|folder|folders)\('
```

## Command Grammar

```bash
<binary> [--pretty] graphql query '<document>' [--variables '<json-object>']
<binary> [--pretty] graphql query-file <path> [--variables-file <path>]
<binary> graphql schema
<binary> auth oauth2 | auth status | auth logout
```

Exactly one operation per document. Use `--variables` with `query C($id: ID!)`
style documents instead of string-interpolating ids. Use `query-file` when the
document is long or quoting gets hard. JSON output goes to stdout; diagnostics
go to stderr.

## Read Patterns (reader)

Account and people:

```bash
wrike-gateway-reader graphql query '{ account { id name rootFolderId } }'
wrike-gateway-reader graphql query '{ contacts { id firstName lastName type } }'
wrike-gateway-reader graphql query '{ contacts(me: true) { id firstName } }'
wrike-gateway-reader graphql query 'query C($id: ID!) { contact(id: $id) { id firstName } }' \
  --variables '{"id": "KUAAAAAA"}'
```

There is no `users` collection; account people come from `contacts` with a
type filter. `user(id:)` and `userTypes` exist but `userTypes` may be
plan-blocked (`AUTHORIZATION_FAILED`), which is a valid outcome, not a defect.

Work hierarchy:

```bash
wrike-gateway-reader graphql query '{ spaces { id title } }'
wrike-gateway-reader graphql query '{ folders { id title scope } }'
wrike-gateway-reader graphql query '{ projects { id title project { customStatusId } } }'
wrike-gateway-reader graphql query 'query F($id: ID!) { folder(id: $id) { id title parentIds childIds } }' \
  --variables '{"id": "<folder-id>"}'
```

The folders list includes the Root and Recycle Bin pseudo-folders (`scope` is
`WsRoot` / `RbRoot`). Their ids are refused by `folder(id:)` with HTTP 400.
When picking a folder id from a list, select one whose `scope` is `WsFolder`.

Tasks, with pagination:

```bash
wrike-gateway-reader graphql query \
  '{ tasks(page: { pageSize: 25 }) { nodes { id title status parentIds } pageInfo { resultCount nextPageToken } } }'
# next page: pass the token back with the SAME filters
wrike-gateway-reader graphql query \
  'query T($t: String) { tasks(page: { pageSize: 25, nextPageToken: $t }) { nodes { id title } pageInfo { nextPageToken } } }' \
  --variables '{"t": "<token-from-previous-page>"}'
wrike-gateway-reader graphql query 'query T($id: ID!) { task(id: $id) { id title status description } }' \
  --variables '{"id": "<task-id>"}'
```

`nextPageToken` is opaque: never construct one, never reuse it with changed
filters. Scoped reads use a typed `scope` input, never a path:

```bash
wrike-gateway-reader graphql query \
  'query S($fid: ID!) { tasks(scope: { folderId: $fid }, page: { pageSize: 50 }) { nodes { id title } pageInfo { nextPageToken } } }' \
  --variables '{"fid": "<folder-id>"}'
wrike-gateway-reader graphql query \
  'query C($tid: ID!) { comments(scope: { taskId: $tid }) { id text authorId } }' \
  --variables '{"tid": "<task-id>"}'
```

Collaboration and administration views:

```bash
wrike-gateway-reader graphql query '{ attachments { id name contentType size taskId } }'
wrike-gateway-reader graphql query '{ timelogs(page: { pageSize: 25 }) { nodes { id hours trackedDate } pageInfo { nextPageToken } } }'
wrike-gateway-reader graphql query '{ customFields { id title type } }'
wrike-gateway-reader graphql query '{ workflows { id name } }'
wrike-gateway-reader graphql query '{ webhooks { id status } }'
wrike-gateway-reader graphql query '{ groups { id title } }'
```

Account-wide `comments` may be plan-blocked; scope to a task or folder instead.

Attachment content writes a local file; it never appears in the JSON:

```bash
wrike-gateway-reader graphql query \
  'query D($id: ID!, $dest: String!) { attachmentDownload(id: $id, destination: $dest) { path byteCount contentType } }' \
  --variables '{"id": "<attachment-id>", "dest": "/tmp/brief.pdf"}'
```

The destination must not exist; a failed transfer writes nothing. Use
`attachmentPreview` (optional `size`: `w44 w100 w200 w300 w400 h400`) for
thumbnails and `attachmentDownloadUrl` for a time-limited URL instead.

## Write Patterns (writer)

```bash
# Create a folder (parentFolderId is required; account.rootFolderId works as a parent):
wrike-gateway-writer graphql query \
  'mutation F($p: ID!) { createFolder(input: { parentFolderId: $p, title: "Q3 launch" }) { folder { id title } } }' \
  --variables '{"p": "<parent-folder-id>"}'

# Create and update a task:
wrike-gateway-writer graphql query \
  'mutation T($f: ID!) { createTask(input: { folderId: $f, title: "Prepare launch" }) { task { id title } } }' \
  --variables '{"f": "<folder-id>"}'
wrike-gateway-writer graphql query \
  'mutation U($id: ID!) { updateTask(input: { taskId: $id, description: "updated" }) { task { id } } }' \
  --variables '{"id": "<task-id>"}'

# Comment on a task (comment target is a scope, not an input field):
wrike-gateway-writer graphql query \
  'mutation C($tid: ID!) { createComment(scope: { taskId: $tid }, input: { text: "done" }) { comment { id } } }' \
  --variables '{"tid": "<task-id>"}'

# Timelog: hours, taskId, trackedDate, and comment are all required live:
wrike-gateway-writer graphql query \
  'mutation L($tid: ID!) { createTimelog(input: { taskId: $tid, hours: 0.5, trackedDate: "2026-08-06", comment: "review" }) { timelog { id } } }' \
  --variables '{"tid": "<task-id>"}'

# Upload a local file as a task attachment (filePath must be a readable regular file):
wrike-gateway-writer graphql query \
  'mutation A($tid: ID!, $f: String!) { uploadTaskAttachment(input: { taskId: $tid, filePath: $f }) { attachment { id name } } }' \
  --variables '{"tid": "<task-id>", "f": "/tmp/brief.pdf"}'
```

Update inputs treat omitted fields as "leave unchanged". Mutations never retry
automatically; a transport failure on a mutation is reported outcome-unknown,
so re-check state before re-sending one.

## Delete Patterns (admin only)

```bash
wrike-gateway-admin graphql query \
  'mutation D($id: ID!) { deleteTask(input: { taskId: $id }) { deletedId } }' \
  --variables '{"id": "<task-id>"}'
```

Available deletes: `deleteTask`, `deleteFolder`, `deleteProject`,
`deleteComment`, `deleteAttachment`, `deleteTimelog`, `deleteGroup`,
`deleteSpace`, `deleteWebhook`. Each takes exactly one explicit id; there is no
wildcard, recursive, or bulk form. Before deleting, confirm the id with a fresh
read (for example that the task's `parentIds` names the container you created).
Delete children before their container.

## Errors and Exit Codes

Failures use a stable envelope; branch on `errors[].extensions.code`, never on
message text:

| Code | Meaning | Typical handling |
| --- | --- | --- |
| `VALIDATION_ERROR` | bad document/arguments, or Wrike rejected parameters | fix the request |
| `CAPABILITY_DENIED` | field not in this binary's tier | use the named higher tier only if the task requires it |
| `AUTHENTICATION_FAILED` | no usable credential | run auth preflight; check kinko keys |
| `AUTHORIZATION_FAILED` | plan/scope forbids it | valid outcome; record as blocked, do not retry |
| `NOT_FOUND` | id does not exist (or was deleted) | verify the id |
| `RATE_LIMITED` / `UPSTREAM_UNAVAILABLE` | transient | GETs already retried; back off before retrying manually |
| `TRANSPORT_FAILED` | local connectivity | outcome unknown for mutations |
| `UPSTREAM_RESPONSE_INVALID` | live envelope did not decode | report it; likely a gateway defect worth filing |

Exit codes: `0` success, `2` usage/validation, `3` credential, `4` rejected or
not found, `5` rate limit/transient, `6` local file or credential store, `70`
internal.

## Rules

- Never print, log, or commit a token, client secret, or authorization header.
- Prefer `--variables` over interpolating values into documents.
- Treat Wrike ids as opaque strings; never parse or construct them.
- A plan-blocked operation (`AUTHORIZATION_FAILED`) is a result to report, not
  an error to work around with a broader operation.
- For repository development tasks (building, testing, releasing this CLI),
  use the repository's own AGENTS.md and skills instead of this one.
