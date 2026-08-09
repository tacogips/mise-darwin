---
name: secure-github-action
description: Use when creating or modifying GitHub Actions workflow files (.github/workflows/*.yml or .yaml). Pin actions to full commit SHAs, minimize permissions, prevent script injection, and apply supply chain hardening.
metadata:
  short-description: Harden GitHub Actions workflows
---

# Secure GitHub Action Workflow

Use this skill when creating or modifying GitHub Actions workflows. Read `references/security-rules.md` for the complete rule set before making non-trivial changes.

## Mandatory workflow

### Step 1: Pin all action references to full commit SHAs

For every `uses:` line, resolve the tag or branch to its full 40-character commit SHA.

How to resolve SHAs:

```bash
# For a tagged release, such as actions/checkout@v4.2.2
gh api repos/{owner}/{repo}/git/ref/tags/{tag} --jq '.object.sha'

# If that returns a tag object instead of a commit, dereference it
gh api repos/{owner}/{repo}/git/tags/{tag_sha} --jq '.object.sha'

# For a branch reference, such as @main
gh api repos/{owner}/{repo}/git/ref/heads/{branch} --jq '.object.sha'
```

Always check the latest stable release first:

```bash
gh api repos/{owner}/{repo}/releases/latest --jq '.tag_name'
```

Output format:

```yaml
- uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
```

### Step 2: Set minimal permissions

```yaml
permissions:
  contents: read

jobs:
  deploy:
    permissions:
      contents: write
      deployments: write
```

- Use `permissions: {}` for jobs that need no GitHub API access.
- Never use `permissions: write-all`.
- Prefer job-level permissions over broad workflow-level write scopes.

### Step 3: Harden checkout

```yaml
- uses: actions/checkout@{SHA} # vX.Y.Z
  with:
    persist-credentials: false
```

Set `persist-credentials: false` unless the job must push with Git.

### Step 4: Prevent script injection

Never interpolate attacker-controlled GitHub context directly inside `run:` blocks. Use `env:` intermediaries instead.

```yaml
# Bad
- run: echo "${{ github.event.pull_request.title }}"

# Good
- env:
    PR_TITLE: ${{ github.event.pull_request.title }}
  run: echo "$PR_TITLE"
```

Dangerous contexts include `github.event.issue.title`, `github.event.issue.body`, `github.event.pull_request.title`, `github.event.pull_request.body`, `github.event.pull_request.head.ref`, `github.event.comment.body`, `github.event.commits.*.message`, and `github.head_ref`.

### Step 5: Avoid `pull_request_target` pitfalls

- Prefer `pull_request` over `pull_request_target`.
- If `pull_request_target` is used, never check out `${{ github.event.pull_request.head.sha }}`.
- For privileged PR operations, use the two-workflow pattern: unprivileged `pull_request` plus privileged `workflow_run`.

### Step 6: Apply additional hardening

- Set `timeout-minutes` on every job.
- Add concurrency groups for CI and deployments.
- Never use `secrets: inherit` in reusable workflows.
- Never upload artifacts that contain secrets or tokens.
- Prefer OIDC over long-lived cloud credentials.

### Step 7: Validate before finalizing

Before you finish:

1. Confirm every `uses:` line is pinned to a full 40-character SHA.
2. Confirm workflow or job `permissions:` exist and are minimal.
3. Confirm no dangerous `${{ github.event.* }}` interpolation appears directly in `run:` blocks.
4. Confirm `persist-credentials: false` is set anywhere push access is unnecessary.
5. Confirm every job defines `timeout-minutes`.

## Arguments

If the request points at an existing workflow file, read it and harden it. If the request is a new workflow description, generate a workflow that follows every rule above.
