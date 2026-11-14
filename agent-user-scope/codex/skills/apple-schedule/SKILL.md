---
name: apple-schedule
description: Inspect and manage scheduled Apple Calendar events, appointments, meetings, availability, recurrences, attendees, and event alarms through the installed apple-gateway CLI on macOS. Use when Codex needs to find or summarize a schedule, check events in a date range, create or update an event, change recurrence or alarms, or delete one occurrence or an event series. Use apple-calendar for calendar container creation or deletion.
---

# Apple Schedule

Use `apple-gateway-reader` for event queries and `apple-gateway` only for
requested mutations. Treat the live GraphQL schema as authoritative.

## Workflow

1. Query `events` with explicit `startDate` and `endDate` bounds whenever the
   request implies a period. Include the user's timezone in ISO 8601 values and
   request only fields needed for the answer.
2. Use `event(eventId:, occurrenceDate:)` after identifying the exact event.
   Preserve all-day status, timezone, location, URL, attendees, availability,
   recurrence, and alarms unless the user asks to change them.
3. Before creation, use `apple-calendar` or a narrow `calendars` query to
   resolve `calendarId` when the target calendar is unclear.
4. Before updating or deleting, distinguish a single occurrence from the whole
   recurrence series. Pass `occurrenceDate` and the intended `RecurrenceSpan`
   where required; never infer destructive recurrence scope.
5. Re-query after a mutation and report the resulting event details.

Prefer query and variables files in a task-specific temporary directory:

```bash
apple-gateway --pretty graphql \
  --query-file "$task_dir/schedule.graphql" \
  --variables-file "$task_dir/variables.json"
```

Supported mutations are `createEvent`, `updateEvent`, `deleteEvent`, and
`setEventAlarms`. Use `apple-calendar` for calendar container mutations.

If access fails, inspect `apple-gateway permissions status --json`. Request the
`calendar` permission only when the approved task requires the macOS prompt.
