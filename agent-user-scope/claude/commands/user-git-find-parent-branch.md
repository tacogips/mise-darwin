---
allowed-tools: Bash(git branch:*), Bash(git rev-parse:*), Bash(git symbolic-ref:*)
description: Find the parent branch of the current branch
---

## Context

- Current branch: !`git branch --show-current`
- All local branches: !`git branch --list`
- Default branch: !`git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@'`

## Your task

Find the parent branch of the current branch based on branch naming convention.

### Instructions

1. **Get current branch information**:
   - Get the current branch name
   - Get all local branch names
   - Get the default branch (main/master)

2. **Parse branch name to find parent**:
   - Assume branch naming format: `{parent_branch_name}_{sub_name}`
   - Extract the parent branch name by removing the last underscore segment
   - Example: `main_feature-auth` -> parent is `main`
   - Example: `develop_api_bugfix` -> parent is `develop_api`

3. **Verify parent branch exists**:
   - Check if the extracted parent branch exists in local branches
   - If found, display the parent branch name
   - If not found, fall back to the default branch (main/master)

4. **Display results**:
   - Show the current branch name
   - Show the identified parent branch
   - If using fallback, indicate that the parent was determined by default branch

### Example Output

For branch `main_feature-auth`:
```
Current branch: main_feature-auth
Parent branch: main
```

For branch `develop_api_bugfix`:
```
Current branch: develop_api_bugfix
Parent branch: develop_api
```

For branch `standalone-feature` (no underscore pattern):
```
Current branch: standalone-feature
Parent branch: main (default - no parent pattern found)
```
