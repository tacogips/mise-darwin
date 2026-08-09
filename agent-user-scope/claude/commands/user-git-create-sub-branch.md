---
allowed-tools: Bash(git branch:*), Bash(git checkout:*)
description: Create a new sub-branch from the current branch
argument-hint: <sub_name>
---

## Context

- Current branch: !`git branch --show-current`
- All local branches: !`git branch --list`

## Your task

Create a new branch based on the current branch with the format: `{current_branch_name}_{sub_name}`

### Instructions

1. **Extract sub_name from arguments**:
   - The sub_name is provided via: $ARGUMENTS
   - If $ARGUMENTS is empty or not provided, return an error message: "Error: sub_name is required. Usage: /create-sub-branch <sub_name>"
   - If sub_name contains obvious typos, fix them appropriately (e.g., "faeture" -> "feature", "bugfxi" -> "bugfix")

2. **Create the new branch**:
   - Get the current branch name
   - Create a new branch with format: `{current_branch_name}_{sub_name}`
   - Use `git checkout -b` to create and switch to the new branch

3. **Confirm the operation**:
   - Display a success message showing:
     - Previous branch name
     - New branch name
     - Confirmation that the branch was created and checked out

### Example

If the current branch is `main` and the user provides `feature-auth`:
- Create and checkout branch: `main_feature-auth`

If the current branch is `develop_api` and the user provides `bugfix`:
- Create and checkout branch: `develop_api_bugfix`
