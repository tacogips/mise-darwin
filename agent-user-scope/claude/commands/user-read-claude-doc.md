---
allowed-tools: WebFetch(*), Task(claude-code-guide:*)
description: Read and understand Claude Code documentation
argument-hint: [topic]
---

## Your task

Read and understand the Claude Code documentation from https://code.claude.com/docs/en/slash-commands

### Instructions

1. **Determine the topic**:
   - If $ARGUMENTS is provided, use it as the specific topic to focus on
   - If no arguments, read the general slash-commands documentation

2. **Fetch the documentation**:
   - Use the Task tool with subagent_type='claude-code-guide' to get accurate information
   - Or use WebFetch to retrieve content from https://code.claude.com/docs/en/slash-commands

3. **Analyze and summarize**:
   - Read and understand the documentation content
   - If a specific topic was requested, focus on that area
   - Provide a clear, concise summary of the key points

4. **Present the information**:
   - Show the main concepts and features
   - Include practical examples if available
   - Highlight any important notes or best practices

### Example Usage

```
/read-claude-doc
```
Reads the general slash-commands documentation.

```
/read-claude-doc custom commands
```
Focuses on information about custom commands in the documentation.
