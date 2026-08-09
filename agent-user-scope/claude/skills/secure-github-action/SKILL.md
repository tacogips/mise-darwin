---
name: secure-github-action
description: Use this skill when creating or modifying GitHub Actions workflow files (.github/workflows/*.yml or .yaml). Ensures all actions are pinned by commit SHA, permissions are minimized, script injection is prevented, and other supply chain security best practices are applied.
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
argument-hint: [workflow description or file path]
user-invocable: true
---

# Secure GitHub Action Workflow

When creating or modifying GitHub Actions workflow files, follow all steps below. Read `references/security-rules.md` for the full rule set.

## Mandatory Workflow

### Step 1: Pin ALL action references to full commit SHAs

For every `uses:` line, resolve the tag or branch to its full 40-character commit SHA.

How to resolve SHAs:

```bash
# For a tagged release (e.g. actions/checkout@v4.2.2)
gh api repos/{owner}/{repo}/git/ref/tags/{tag} --jq '.object.sha'

# If the above returns a tag object (not a commit), dereference it
gh api repos/{owner}/{repo}/git/tags/{tag_sha} --jq '.object.sha'

# For a branch reference (e.g. @main)
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

- Use `permissions: {}` for jobs needing no GitHub API access.
- Never use `permissions: write-all`.
- Prefer job-level permissions over workflow-level permissions.

### Step 3: Harden checkout

```yaml
- uses: actions/checkout@{SHA} # vX.Y.Z
  with:
    persist-credentials: false
```

Set `persist-credentials: false` for all jobs that do not need to `git push`.

### Step 4: Prevent script injection

Never interpolate `${{ github.event.* }}` directly in `run:` blocks. Use `env:` intermediaries instead.

```yaml
# BAD
- run: echo "${{ github.event.pull_request.title }}"

# GOOD
- env:
    PR_TITLE: ${{ github.event.pull_request.title }}
  run: echo "$PR_TITLE"
```

Dangerous contexts: `github.event.issue.title`, `github.event.issue.body`, `github.event.pull_request.title`, `github.event.pull_request.body`, `github.event.pull_request.head.ref`, `github.event.comment.body`, `github.event.commits.*.message`, and `github.head_ref`.

### Step 5: Avoid `pull_request_target` pitfalls

- Prefer `pull_request` over `pull_request_target`.
- If `pull_request_target` is used, never check out `${{ github.event.pull_request.head.sha }}`.
- For privileged operations on PR code, use the two-workflow pattern: unprivileged `pull_request` plus privileged `workflow_run`.

### Step 6: Apply additional hardening

- Always set `timeout-minutes` on jobs.
- Add concurrency groups for deployments and CI.
- Never use `secrets: inherit` in reusable workflows. Pass secrets explicitly.
- Never upload artifacts containing secrets or tokens.
- Prefer OIDC over long-lived secrets for cloud provider auth.

### Step 7: Validate before finalizing

After generating or editing the workflow, verify:

1. Every `uses:` line has a full 40-character SHA.
2. A minimal `permissions:` block exists at workflow or job level.
3. No dangerous `${{ github.event.* }}` appears directly in any `run:` block.
4. `persist-credentials: false` is set where push is not needed.
5. `timeout-minutes` is set on all jobs.

## Arguments

If `$ARGUMENTS` is a file path, read it and apply hardening. If it is a description, create a new workflow that follows all rules above.
