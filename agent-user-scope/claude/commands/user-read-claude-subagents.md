---
allowed-tools: WebFetch(*), Task(claude-code-guide:*)
description: Read and understand Claude Code sub-agents documentation
argument-hint: [subagent_type]
---

## Your task

Read and understand the Claude Code sub-agents documentation from https://code.claude.com/docs/en/sub-agents

### Instructions

1. **Determine the scope**:
   - If $ARGUMENTS is provided, use it as the specific sub-agent type to focus on
   - If no arguments, read the general sub-agents documentation overview

2. **Fetch the documentation**:
   - Use the Task tool with subagent_type='claude-code-guide' to get accurate information about sub-agents
   - Or use WebFetch to retrieve content from https://code.claude.com/docs/en/sub-agents

3. **Analyze and summarize**:
   - Read and understand the sub-agents documentation content
   - If a specific sub-agent type was requested, focus on that type's details
   - Provide a clear, concise summary of the key concepts

4. **Present the information**:
   - Show what sub-agents are and how they work
   - Explain available sub-agent types and their purposes
   - Include practical examples of when to use each sub-agent type
   - Highlight best practices and important notes

### Example Usage

```
/read-claude-subagents
```
Reads the general sub-agents documentation overview.

```
/read-claude-subagents Explore
```
Focuses on information about the Explore sub-agent type.

```
/read-claude-subagents general-purpose
```
Focuses on information about the general-purpose sub-agent.
