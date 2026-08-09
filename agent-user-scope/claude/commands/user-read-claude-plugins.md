---
allowed-tools: WebFetch(*), Task(claude-code-guide:*)
description: Read and understand Claude Code plugins documentation
argument-hint: [plugin_name]
---

## Your task

Read and understand the Claude Code plugins documentation from https://code.claude.com/docs/en/plugins

### Instructions

1. **Determine the scope**:
   - If $ARGUMENTS is provided, use it as the specific plugin name to focus on
   - If no arguments, read the general plugins documentation overview

2. **Fetch the documentation**:
   - Use the Task tool with subagent_type='claude-code-guide' to get accurate information about plugins
   - Or use WebFetch to retrieve content from https://code.claude.com/docs/en/plugins

3. **Analyze and summarize**:
   - Read and understand the plugins documentation content
   - If a specific plugin was requested, focus on that plugin's details
   - Provide a clear, concise summary of the key concepts

4. **Present the information**:
   - Show what plugins are and how they work
   - Explain available plugins and their purposes
   - Include practical examples of how to install and use plugins
   - Highlight best practices and important notes

### Example Usage

```
/read-claude-plugins
```
Reads the general plugins documentation overview.

```
/read-claude-plugins mcp
```
Focuses on information about MCP (Model Context Protocol) plugins.

```
/read-claude-plugins installation
```
Focuses on information about installing plugins.
