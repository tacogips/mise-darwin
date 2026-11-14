---
allowed-tools: Bash(git branch:*), Bash(git rev-parse:*), Bash(git symbolic-ref:*), Bash(gh pr:*), Bash(git log:*), Bash(git diff:*)
description: Create a pull request using gh command
---

## Context

- Current branch: !`git branch --show-current`
- All local branches: !`git branch --list`
- Default branch: !`git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@'`
- Recent commits on current branch: !`git log --oneline -10`
- Remote tracking status: !`git status -sb`

## Your task

Create a pull request using the `gh` command. Determine the base branch based on the following logic:

### Instructions

1. **Determine base branch**:
   - If `$ARGUMENTS` contains a base branch name, use that as the base branch
   - If `$ARGUMENTS` is empty or doesn't specify a base branch, find the parent branch using the following method:
     - Assume branch naming format: `{parent_branch_name}_{sub_name}`
     - Extract the parent branch name by removing the last underscore segment
     - Example: `main_feature-auth` -> parent is `main`
     - Example: `develop_api_bugfix` -> parent is `develop_api`
     - Verify the extracted parent branch exists in local branches
     - If not found, fall back to the default branch (main/master)

2. **Analyze changes for PR description**:
   - Get the list of commits that will be included in the PR
   - Use `git log <base_branch>..HEAD` to see all commits since diverging from base
   - Use `git diff <base_branch>...HEAD` to see the full diff
   - Analyze the changes to create a comprehensive PR description

3. **Create PR title and body**:
   - Title: Concise summary of the changes (50-72 characters)
   - Body should include:
     - **Summary**: Brief overview of what this PR does (2-3 sentences)
     - **Changes**: Bulleted list of key changes
     - **Testing**: How the changes were tested (if applicable)
     - **Related Issues**: Reference any related issues (if applicable)

4. **Execute PR creation**:
   - Push the current branch to remote if not already pushed
   - Use `gh pr create --base <base_branch> --title "<title>" --body "<body>"`
   - If the branch is not pushed, push it first with `git push -u origin <current_branch>`

5. **Display results**:
   - Show the PR URL after creation
   - Show the base branch used
   - Show the current branch

### Example Output

```
Base branch: main
Current branch: main_feature-auth

Creating pull request...

✓ Pull request created successfully!
URL: https://github.com/user/repo/pull/123

Title: Add JWT authentication system
Base: main <- Head: main_feature-auth
```

### Notes

- If `gh` is not authenticated, the command will prompt for authentication
- If the branch has no commits ahead of the base branch, the PR creation will fail
- Ensure all commits are pushed to remote before creating the PR
