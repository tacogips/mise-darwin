---
allowed-tools: Bash(git log:*)
description: Show recent commit logs with changed files
---

## Context

You need to analyze recent git commits to understand what changes were made and why.

## Your task

Show the last {n=3} git commits with:
- Commit hash and message
- Changed file names
- Author and date

Use this command format:
```bash
git log --stat --oneline -n {n} --pretty=format:"%h - %an, %ar : %s"
```

Or for more detailed view:
```bash
git log -n {n} --pretty=format:"%h - %an, %ar : %s" --stat
```

**Important**: Do NOT show diffs (git diff output) as they are too large. Only show:
- Commit messages
- File names that were changed
- Basic statistics (lines added/removed)

Provide a summary of what you learned from these commits.
