---
name: apple-mail
description: Search and read Apple Mail accounts, mailboxes, messages, bodies, raw sources, and attachments through the read-only apple-gateway CLI on macOS. Use when Codex needs to find recent, unread, flagged, sender-specific, recipient-specific, subject-specific, or date-bounded mail; summarize selected messages; or download a selected body or attachment.
---

# Apple Mail

Use `apple-gateway-reader` for all Mail work. The apple-gateway schema exposes
Mail reads but no mail mutation, send, draft, delete, or state-change fields.

## Workflow

1. Resolve `mailAccounts` or `mailboxes` only when the request needs a specific
   account or mailbox.
2. Search with `mailMessages`, using the narrowest available filters:
   `accountId`, `mailboxId`, `query`, `from`, `to`, `subject`, received date
   bounds, `unreadOnly`, or `flaggedOnly`.
3. Request envelope fields first. Retrieve body or attachment `downloadKey`
   fields only for messages the user asked to inspect.
4. Use `mailMessage(messageId:)` after identifying the exact message. Avoid
   exposing unrelated recipients, content, or attachment names.
5. Materialize selected files with `apple-gateway file download --key ...` and
   an explicit output directory when the user supplied one.

Use query and variables files for user-provided search text:

```bash
apple-gateway-reader --pretty graphql \
  --query-file "$task_dir/mail.graphql" \
  --variables-file "$task_dir/variables.json"
```

If the user asks to send, draft, delete, flag, or mark mail read, explain that
this skill and the current live schema are read-only; use another explicitly
available mail tool only if the user authorizes that broader workflow.

If access fails, inspect `apple-gateway permissions status --json`. Full Disk
Access for Mail is a manual macOS setting and must not be represented as a CLI
permission request.
