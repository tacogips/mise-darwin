---
name: apple-clock-alarms
description: Inspect and manage alarms in the macOS Clock app through the installed apple-gateway CLI. Use when Codex needs to list alarms, create an alarm, enable or disable one, change its time, label, or repeat days, or delete an alarm.
---

# Apple Clock Alarms

Use `apple-gateway-reader` to list alarms and `apple-gateway` only for requested
mutations. Clock operations use UI automation, so verify results carefully.

## Workflow

1. Query `clockAlarms { id label time isEnabled repeatDays }` before changing
   anything.
2. Disambiguate alarms with duplicate labels or times. Prefer a stable `id`
   when the live schema and result provide one.
3. For creation or updates, preserve the user's local time, label, and repeat
   days. Do not infer weekdays, sound, snooze, or other unsupported settings.
4. Use `toggleClockAlarm`, `updateClockAlarm`, or `deleteClockAlarm` only after
   identifying the exact target. Treat deletion as destructive.
5. Inspect the returned `success`, `alarm`, and `warning`, then re-query the
   alarm list to verify UI automation took effect.

Supported mutations are `createClockAlarm`, `toggleClockAlarm`,
`updateClockAlarm`, and `deleteClockAlarm`. Inspect
`apple-gateway schema print --role full` for their current input shapes rather
than guessing identifiers or enum values.

If access fails, inspect `apple-gateway permissions status --json`. Request the
`clock-alarms` permission only when the approved task requires Accessibility or
Automation prompts.
