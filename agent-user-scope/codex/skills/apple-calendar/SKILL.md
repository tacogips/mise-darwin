---
name: apple-calendar
description: Inspect and manage Apple Calendar calendar containers through the installed apple-gateway CLI on macOS. Use when Codex needs to list event or reminder calendars, inspect calendar sources and editability, create a calendar, choose the calendar that should hold an event, or delete a calendar. Use apple-schedule for events, appointments, meetings, recurrences, and event alarms.
---

# Apple Calendar

Use `apple-gateway-reader` for calendar queries and `apple-gateway` only for
requested calendar creation or deletion. Treat `schema print` as authoritative.

## Workflow

1. Confirm `apple-gateway-reader` and `apple-gateway` are available.
2. Inspect the live `calendars` fields and calendar inputs with
   `apple-gateway-reader schema print` when the request needs unfamiliar fields.
3. Query `calendars(entityType:)`, requesting only fields needed for the answer,
   such as `id`, `title`, `entityType`, `sourceTitle`, `allowsModifications`,
   `isSubscribed`, and `isDefault`.
4. Before creating a calendar, preserve whether it is intended for events or
   reminders and any specified source or color.
5. Before deletion, query the exact calendar by listing candidates and verify
   title, source, entity type, and identifier. Calendar deletion is destructive
   and may remove all contained items.
6. Re-query after a mutation and report the resulting calendar list.

Prefer query and variables files in a task-specific temporary directory:

```bash
apple-gateway-reader --pretty graphql \
  --query-file "$task_dir/calendar.graphql" \
  --variables-file "$task_dir/variables.json"
```

Supported mutations are `createCalendar` and `deleteCalendar`. Use
`apple-schedule` for `createEvent`, `updateEvent`, `deleteEvent`, and
`setEventAlarms`. Never delete a calendar unless explicitly asked.

If access fails, inspect `apple-gateway permissions status --json`. Request the
`calendar` permission only when the approved task requires the macOS prompt.
