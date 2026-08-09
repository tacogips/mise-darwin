---
name: "brave-browser-computer-use"
description: "Use when Codex needs to operate a browser UI, open or inspect web pages interactively, navigate localhost or external sites, click links/buttons, type into forms, scroll pages, take browser screenshots, or verify a web UI through a visible browser. This skill requires using the Computer Use MCP tools to operate Brave Browser specifically."
---

# Brave Browser Computer Use

## Overview

Operate browser tasks through Computer Use MCP with `Brave Browser` as the target app.
Use this for visible browser interaction, including local web app checks, website navigation, form entry, clicking, scrolling, and UI verification.

## Required Tooling

- Use `mcp__computer_use` tools for browser operation.
- Set the Computer Use `app` parameter to `Brave Browser` whenever possible.
- Start each interaction turn by calling `mcp__computer_use.get_app_state` for `Brave Browser`.
- Use Computer Use actions such as `click`, `type_text`, `press_key`, `scroll`, `select_text`, and `set_value` against Brave's visible UI.

## Workflow

1. Open or focus Brave Browser through `mcp__computer_use.get_app_state`.
2. Navigate by using Brave's address bar when a URL is provided.
3. Perform requested browser actions with Computer Use MCP tools.
4. Inspect the returned screenshot and accessibility tree after meaningful actions.
5. Report what was verified or any visible blocker.

## Constraints

- Do not satisfy browser-operation requests with the Browser plugin, generic web browser automation tools, or `open` shell commands unless the user explicitly asks for a different browser tool.
- Do not substitute another browser when Brave Browser is available.
- Use internet/search tools only for factual lookup. Use Brave through Computer Use for interactive browser UI operation.
