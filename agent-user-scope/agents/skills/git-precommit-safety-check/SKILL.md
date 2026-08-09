---
name: git-precommit-safety-check
description: Use before committing or pushing when the commit target should be checked for credential material, private URLs, and machine-local absolute paths without using gitleaks.
allowed-tools: Bash, Read, Grep, Glob
argument-hint: [optional repository path]
user-invocable: true
---

# Git Precommit Safety Check

Use this skill before creating a Git commit, amending a commit, or pushing a
not-yet-reviewed commit when the user asks for a non-gitleaks check of the
commit target.

## Scope

Check only the content that is actually intended for commit:

1. Resolve the repository path. Default to the current working directory.
2. Run `git status --short` and identify staged, unstaged, and untracked files.
3. If staged changes exist, inspect `git diff --cached --stat` and
   `git diff --cached --name-only`.
4. If no staged changes exist but the user is asking before staging, inspect the
   tracked dirty files and relevant untracked files before advising what can be
   staged.
5. If a commit already exists but has not been pushed, inspect
   `git show --stat --name-only HEAD` and the patch for `HEAD`.

## Checks

Use `references/security.md` as the rule source. The important checks are:

- No real credential values, private key material, tokens, API keys, or
  credential-bearing URLs.
- No private repository URLs unless the user explicitly requested them.
- No machine-local absolute paths, especially paths that reveal a username,
  workstation layout, local checkout root, or private filesystem structure.
- No generated outputs that embed environment variable values. References such
  as `$GITHUB_TOKEN` or `${GITHUB_TOKEN}` are acceptable when they are examples
  of secure configuration.

Prefer direct patch inspection over broad repository scans. Use targeted
commands such as:

```bash
git diff --cached
git diff --cached --name-only
git show --format=fuller --stat --name-only HEAD
git show --format=fuller --patch HEAD
```

Do not use gitleaks for this skill. If a repository also requires gitleaks,
that is an additional gate, not a substitute for this manual staged-content
review.

## Output

Report either `Pass` or `Issues`.

For issues, include the file path, the suspicious category, and the minimal fix.
Do not quote real secret values. Redact any sensitive value before reporting it.
