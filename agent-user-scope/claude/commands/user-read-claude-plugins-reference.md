---
allowed-tools: WebFetch(*), Task(claude-code-guide:*)
description: Read and understand Claude Code plugins reference documentation
argument-hint: [plugin_name]
---

## Your task

Read and understand the Claude Code plugins reference documentation from https://code.claude.com/docs/en/plugins-reference

### Instructions

1. **Determine the scope**:
   - If $ARGUMENTS is provided, use it as the specific plugin name to focus on
   - If no arguments, read the general plugins reference documentation

2. **Fetch the documentation**:
   - Use the Task tool with subagent_type='claude-code-guide' to get accurate information about the plugins reference
   - Or use WebFetch to retrieve content from https://code.claude.com/docs/en/plugins-reference

3. **Analyze and summarize**:
   - Read and understand the plugins reference documentation content
   - If a specific plugin was requested, focus on that plugin's API reference details
   - Provide a clear, concise summary of the key concepts and API details

4. **Present the information**:
   - Show the complete API reference for plugins
   - Explain plugin configuration options and their purposes
   - Include practical examples of plugin configuration
   - Highlight best practices and important notes
   - Show the structure and schema for plugin definitions

### Example Usage

```
/read-claude-plugins-reference
```
Reads the complete plugins reference documentation.

```
/read-claude-plugins-reference mcp
```
Focuses on MCP plugin reference details.

```
/read-claude-plugins-reference config
```
Focuses on plugin configuration reference.
