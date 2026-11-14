---
allowed-tools: WebFetch(*), Task(claude-code-guide:*)
description: Read and understand Claude Code skills documentation
argument-hint: [skill_name]
---

## Your task

Read and understand the Claude Code skills documentation from https://code.claude.com/docs/en/skills

### Instructions

1. **Determine the scope**:
   - If $ARGUMENTS is provided, use it as the specific skill name to focus on
   - If no arguments, read the general skills documentation overview

2. **Fetch the documentation**:
   - Use the Task tool with subagent_type='claude-code-guide' to get accurate information about skills
   - Or use WebFetch to retrieve content from https://code.claude.com/docs/en/skills

3. **Analyze and summarize**:
   - Read and understand the skills documentation content
   - If a specific skill was requested, focus on that skill's details
   - Provide a clear, concise summary of the key concepts

4. **Present the information**:
   - Show what skills are and how they work
   - Explain how to use or install skills if applicable
   - Include practical examples if available
   - Highlight best practices and important notes

### Example Usage

```
/read-claude-skills
```
Reads the general skills documentation overview.

```
/read-claude-skills pdf
```
Focuses on information about the PDF skill.

```
/read-claude-skills excel
```
Focuses on information about the Excel/spreadsheet skills.
