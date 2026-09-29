---
name: apple-notifications
description: List, filter, post, await responses to, and dismiss macOS notifications through the installed apple-gateway CLI. Use when Codex needs to review delivered notifications, filter them by app or time, post a notification with optional actions or reply support, wait for user interaction, dismiss selected notifications, or dismiss notifications created by apple-gateway.
---

# Apple Notifications

Use `apple-gateway-reader` to list delivered notifications and `apple-gateway`
only for requested posting or dismissal.

## Workflow

1. Query `notifications` with the narrowest `source`, `appBundleId`, delivered
   date bounds, and page size. Avoid returning unrelated notification bodies.
2. For posting, preserve the requested title, subtitle, body, sound, actions,
   reply support, and wait duration. Do not enable reply collection unless the
   task needs it.
3. Treat `postNotification` as a write even when it only informs the user.
   Report whether delivery used a fallback and any returned activation.
4. Before `dismissNotifications`, query and identify the exact notification
   IDs. Use `dismissAllGatewayNotifications` only when the user explicitly asks
   to clear all notifications created through the gateway.
5. Re-query after dismissal when practical.

Use GraphQL variables for notification text and IDs. Do not place private
content into shell-interpolated query strings.

If access fails, inspect `apple-gateway permissions status --json`. Request the
`notifications` permission only when the approved task requires the macOS
prompt. Notification database Full Disk Access remains a manual macOS setting.
