---
name: apple-reminders
description: Inspect and manage Apple Reminders lists, reminders, due schedules, completion state, priority, recurrence, and alarms through the installed apple-gateway CLI on macOS. Use when Codex needs to list or search reminders, create a scheduled task, update its due date or details, mark it complete, move it by recreating when supported, set alarms, or delete it.
---

# Apple Reminders

Use `apple-gateway-reader` for reads and `apple-gateway` only for user-requested
changes. Treat the live schema as authoritative.

## Workflow

1. Inspect `reminderLists`, `reminders`, and `reminder` for read requests.
2. Bound searches with the narrowest available list, completion, date, and text
   filters. Include identifiers in intermediate results but expose only useful
   user-facing details.
3. For a new reminder, resolve `listId` if the user named a list. Preserve the
   distinction between `startDate`, `dueDate`, `dueDateHasTime`, alarms, and
   recurrence rules; do not invent a time for a date-only reminder.
4. Before updating, completing, or deleting, query the exact reminder by ID and
   verify ambiguous title matches with the user.
5. Use `setReminderCompleted` for completion state and `setReminderAlarms` for
   alarm replacement. Re-query after each mutation.

Use GraphQL variables rather than interpolating titles or notes:

```bash
apple-gateway --pretty graphql \
  --query-file "$task_dir/reminder.graphql" \
  --variables-file "$task_dir/variables.json"
```

Supported mutations include `createReminderList`, `createReminder`,
`updateReminder`, `deleteReminder`, `setReminderCompleted`, and
`setReminderAlarms`. Treat list creation and deletion as separate scopes; the
live schema currently exposes list creation but not list deletion.

If access fails, inspect `apple-gateway permissions status --json`. Request the
`reminders` permission only when the approved task requires the macOS prompt.
