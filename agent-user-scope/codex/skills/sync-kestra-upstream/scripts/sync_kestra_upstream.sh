#!/usr/bin/env bash

set -euo pipefail

REPOSITORY_PATH="${1:-.}"
EXPECTED_ORIGIN="https://github.com/tacogips/kestra.git"
EXPECTED_UPSTREAM="https://github.com/kestra-io/kestra.git"
UPSTREAM_REMOTE="upstream"
UPSTREAM_BRANCH="develop"
MIRROR_BRANCH="upsteam"
TARGET_BRANCH="main"

cd "${REPOSITORY_PATH}"

git rev-parse --is-inside-work-tree >/dev/null

if [[ -n "$(git status --porcelain)" ]]; then
    echo "Refusing to synchronize: the worktree or index is not clean." >&2
    exit 1
fi

origin_url="$(git remote get-url origin)"
if [[ "${origin_url%.git}" != "${EXPECTED_ORIGIN%.git}" ]]; then
    echo "Refusing to synchronize: unexpected origin URL: ${origin_url}" >&2
    exit 1
fi

if git remote get-url "${UPSTREAM_REMOTE}" >/dev/null 2>&1; then
    upstream_url="$(git remote get-url "${UPSTREAM_REMOTE}")"
    if [[ "${upstream_url%.git}" != "${EXPECTED_UPSTREAM%.git}" ]]; then
        echo "Refusing to synchronize: unexpected upstream URL: ${upstream_url}" >&2
        exit 1
    fi
else
    git remote add "${UPSTREAM_REMOTE}" "${EXPECTED_UPSTREAM}"
fi

git fetch --prune "${UPSTREAM_REMOTE}" "${UPSTREAM_BRANCH}"

if git show-ref --verify --quiet "refs/heads/${MIRROR_BRANCH}"; then
    git checkout "${MIRROR_BRANCH}"
    git merge --ff-only "refs/remotes/${UPSTREAM_REMOTE}/${UPSTREAM_BRANCH}"
else
    git checkout --track -b "${MIRROR_BRANCH}" "${UPSTREAM_REMOTE}/${UPSTREAM_BRANCH}"
fi

git checkout "${TARGET_BRANCH}"
git merge --no-edit "${MIRROR_BRANCH}"

echo "Merged ${MIRROR_BRANCH} into ${TARGET_BRANCH}. No branches were pushed."
