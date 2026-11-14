---
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*)
description: Create a git commit
---

## Context

- Current git status: !`git status`
- Current git diff (staged and unstaged changes): !`git diff HEAD`
- Current branch: !`git branch --show-current`
- Recent commits: !`git log --oneline -10`

## Your task

Based on the above changes, create a single git commit. Follow the git commit policy and format below.

## Git Commit Policy

- Follow commit message format from this document
- Auto-proceed without user confirmation
- **NO Claude Code attribution** - commits appear as user-made only

### Git Commit Message Format

**Structure** (8 sections):

1. **Objective**: Purpose, goals, challenges addressed
2. **Primary Changes**: Main changes and intent
3. **Key Technical Concepts**: Technologies, frameworks involved
4. **Files and Code Sections**: Modified files with summaries
5. **Problem Solving**: Issues addressed (include bug reproduction for fixes)
6. **Impact**: Effect on overall project
7. **Related Commits**: `Related: abc123d, def456a`
8. **Unresolved TODOs**: `- [ ]` format
