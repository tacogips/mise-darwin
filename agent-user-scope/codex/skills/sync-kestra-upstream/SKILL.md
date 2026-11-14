---
name: sync-kestra-upstream
description: Safely refresh a Kestra fork's local upsteam branch from kestra-io/kestra develop and merge it into the fork's main branch. Use for this repository's upstream synchronization; do not use for pushing or rebasing.
---

# Sync Kestra Upstream

Use this skill for the Kestra fork whose `origin` is `tacogips/kestra`.

## Outcome

- Configure `upstream` as `https://github.com/kestra-io/kestra.git` when it is absent.
- Make local `upsteam` track the latest `upstream/develop` without rewriting divergent history.
- Merge `upsteam` into local `main`.
- Do not push any branch.

## Procedure

1. State the assumptions and confirm that success means the three outcomes above.
2. Inspect `git status --short --branch`, remotes, and relevant branch tips.
3. Require explicit user authorization for the checkout and merge mutation. A direct request to perform the synchronization is sufficient.
4. Run `scripts/sync_kestra_upstream.sh <repository-path>`.
5. If the script reports a merge conflict, inspect and report it. Do not auto-resolve or abort unless the user requested that follow-up action.
6. Verify the resulting branch, merge ancestry, and worktree status. Run build and tests appropriate to the merged changes before reporting completion.

## Safety invariants

- Stop when the worktree or index is not clean.
- Stop if `origin` or an existing `upstream` has an unexpected URL.
- Update an existing `upsteam` only by fast-forward; never reset it.
- Never force, rebase, delete branches, or push.
- Preserve existing comments and user changes.

The unusual spelling `upsteam` is intentional and is the local mirror branch name requested by the user. The Git remote remains correctly spelled `upstream`.
