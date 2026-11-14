---
allowed-tools: WebFetch(*), Task(claude-code-guide:*)
description: Read and understand Claude Code slash commands documentation
argument-hint: [command_topic]
---

## Your task

Read and understand the Claude Code slash commands documentation from https://code.claude.com/docs/en/slash-commands

### Instructions

1. **Determine the scope**:
   - If $ARGUMENTS is provided, use it as the specific slash command topic to focus on
   - If no arguments, read the general slash commands documentation overview

2. **Fetch the documentation**:
   - Use the Task tool with subagent_type='claude-code-guide' to get accurate information about slash commands
   - Or use WebFetch to retrieve content from https://code.claude.com/docs/en/slash-commands

3. **Analyze and summarize**:
   - Read and understand the slash commands documentation content
   - If a specific command topic was requested, focus on that topic's details
   - Provide a clear, concise summary of the key concepts

4. **Present the information**:
   - Show what slash commands are and how they work
   - Explain how to create and use custom slash commands
   - Include practical examples if available
   - Highlight best practices and important notes

### Example Usage

```
/read-claude-slash-commands
```
Reads the general slash commands documentation overview.

```
/read-claude-slash-commands custom
```
Focuses on information about creating custom slash commands.

```
/read-claude-slash-commands frontmatter
```
Focuses on information about slash command frontmatter configuration.
