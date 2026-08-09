---
name: peekaboo
description: Use Peekaboo through the configured Cursor MCP server to inspect screenshots, read macOS app/window accessibility trees, and operate macOS UI elements. Use only when the user explicitly asks to use Peekaboo, inspect the screen or a macOS app, or automate visible UI through Peekaboo from Cursor CLI.
metadata:
  surfaces:
    - cli
---

# Peekaboo

Use this skill only from Cursor CLI, with the configured `peekaboo` MCP server.
Do not use `npx`; the MCP server is launched from the local binary.

Keep this skill thin. Use the live Peekaboo surface instead of copying a command
reference into the skill:

- `peekaboo learn`
- `peekaboo tools`
- `peekaboo <command> --help`
- https://peekaboo.sh/MCP.html

## Workflow

1. Prefer Peekaboo MCP tools over shelling out to `peekaboo`.
2. Call `see` first for UI work, targeting the narrowest useful surface:
   `frontmost`, an app name, `App Name:Window Title`, `screen`, or `screen:N`.
3. Use element IDs returned by `see` for `click`, `set_value`, and
   `perform_action` whenever possible. Coordinate actions are a fallback.
4. Use `image` when the task requires visual pixels rather than accessibility
   structure.
5. Use `click`, `scroll`, `type`, and `hotkey` for common interaction. Use
   `set_value` or `perform_action` only when those tools are exposed by the MCP
   server and the target element supports them.
6. If the MCP tool surface is unclear, use `peekaboo tools` or
   `peekaboo learn` to inspect the installed version instead of relying on stale
   memory.

## Safety

- Prefer app/window captures over full-screen captures.
- Do not transcribe secrets, tokens, private messages, or other sensitive screen
  content unless the user explicitly asks.
- Ask before typing, submitting forms, changing settings, deleting data,
  purchasing, authenticating, or sending messages.
- If the intended action is ambiguous, inspect again with `see` instead of
  guessing.

## Troubleshooting

- If the `peekaboo` MCP tools are unavailable, check Cursor's MCP status with
  `cursor-agent mcp list` and enable it with `cursor-agent mcp enable peekaboo`.
- If the server cannot start, verify `~/.cursor/mcp.json` launches
  `peekaboo mcp serve --transport stdio`.
- If captures or actions fail, verify macOS Screen Recording and Accessibility
  permissions with `peekaboo permissions status`.
- If permissions are missing and the user approves setup, run
  `peekaboo permissions grant`.
