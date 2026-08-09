---
allowed-tools: WebFetch(*), Task(claude-code-guide:*)
description: Read and understand Claude Code hooks documentation
argument-hint: [hook_type]
---

## Your task

Read and understand the Claude Code hooks documentation from https://code.claude.com/docs/en/hooks-guide

### Instructions

1. **Determine the scope**:
   - If $ARGUMENTS is provided, use it as the specific hook type to focus on
   - If no arguments, read the general hooks documentation overview

2. **Fetch the documentation**:
   - Use the Task tool with subagent_type='claude-code-guide' to get accurate information about hooks
   - Or use WebFetch to retrieve content from https://code.claude.com/docs/en/hooks-guide

3. **Analyze and summarize**:
   - Read and understand the hooks documentation content
   - If a specific hook type was requested, focus on that hook's details
   - Provide a clear, concise summary of the key concepts

4. **Present the information**:
   - Show what hooks are and how they work
   - Explain available hook types and their purposes
   - Include practical examples of how to implement and use hooks
   - Highlight best practices and important notes

### Example Usage

```
/read-claude-hooks
```
Reads the general hooks documentation overview.

```
/read-claude-hooks tool
```
Focuses on information about tool hooks.

```
/read-claude-hooks user-prompt-submit
```
Focuses on information about user-prompt-submit hooks.
