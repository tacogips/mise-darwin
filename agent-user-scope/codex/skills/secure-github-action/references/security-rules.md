# GitHub Actions Security Rules - Complete Reference

## 1. Supply chain attack prevention

### 1.1 Pin all actions to full-length commit SHAs

Never use mutable tag references such as `@v3`, `@v4`, or `@main`. Tags can be force-pushed to point to malicious commits.

```yaml
# Bad
uses: actions/checkout@v4
uses: some-action@main

# Good
uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
```

### 1.2 Resolve SHAs correctly

Some tags are annotated and point to a tag object rather than a commit. Always dereference when needed.

```bash
SHA=$(gh api repos/{owner}/{repo}/git/ref/tags/{tag} --jq '.object.sha')
TYPE=$(gh api repos/{owner}/{repo}/git/ref/tags/{tag} --jq '.object.type')

if [ "$TYPE" = "tag" ]; then
  SHA=$(gh api repos/{owner}/{repo}/git/tags/$SHA --jq '.object.sha')
fi
```

### 1.3 Check for the latest stable release

```bash
gh api repos/{owner}/{repo}/releases/latest --jq '.tag_name'
```

### 1.4 Vet third-party actions before adoption

- Audit the action source for secret exfiltration or unexpected network calls.
- Check the action's OpenSSF Scorecard score.
- Prefer actions from trusted or verified publishers.
- Audit `action.yml` for transitive unpinned dependencies.

### 1.5 Enable Dependabot for actions

```yaml
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

### 1.6 Pin reusable workflows to SHAs too

```yaml
uses: org/shared-workflows/.github/workflows/deploy.yml@abc123def456...
```

## 2. Permission hardening

### 2.1 Default to minimal permissions

```yaml
permissions:
  contents: read
```

### 2.2 Use job-level permissions for granularity

```yaml
jobs:
  build:
    permissions:
      contents: read
  deploy:
    permissions:
      contents: write
      deployments: write
```

### 2.3 Use empty permissions for isolated jobs

```yaml
jobs:
  lint:
    permissions: {}
```

### 2.4 Never grant `permissions: write-all`

### 2.5 Prefer OIDC over long-lived secrets

```yaml
permissions:
  id-token: write
  contents: read
```

### 2.6 Disable Actions PR creation and approval where possible

Use repository settings to prevent GitHub Actions from creating or approving pull requests unless explicitly required.

## 3. Script injection prevention

### 3.1 Dangerous contexts

Never place attacker-controlled GitHub context directly inside `run:` blocks:

- `github.event.issue.title`
- `github.event.issue.body`
- `github.event.pull_request.title`
- `github.event.pull_request.body`
- `github.event.pull_request.head.ref`
- `github.event.comment.body`
- `github.event.review.body`
- `github.event.pages.*.page_name`
- `github.event.commits.*.message`
- `github.event.commits.*.author.email`
- `github.head_ref`

### 3.2 Safe pattern: use env intermediaries

```yaml
- name: Process PR
  env:
    TITLE: ${{ github.event.pull_request.title }}
    BODY: ${{ github.event.pull_request.body }}
  run: |
    echo "Title: $TITLE"
    echo "Body: $BODY"
```

### 3.3 Be cautious with `GITHUB_OUTPUT` and `GITHUB_ENV`

Sanitize attacker-controlled values before writing them.

### 3.4 Prefer small JS actions for complex untrusted input handling

Passing values as action inputs avoids shell interpretation hazards.

## 4. Secrets handling

### 4.1 Never hardcode secrets in workflow files

### 4.2 Avoid packing multiple values into one secret

Substring redaction can fail when structured data is stored in a single secret.

### 4.3 Mask dynamically generated sensitive values

```yaml
- run: echo "::add-mask::$DYNAMIC_SECRET"
```

### 4.4 Never upload artifacts that contain secrets or tokens

### 4.5 Do not use `secrets: inherit` in reusable workflows

Pass only required secrets explicitly.

```yaml
uses: org/shared/.github/workflows/deploy.yml@{SHA}
secrets:
  DEPLOY_KEY: ${{ secrets.DEPLOY_KEY }}
```

### 4.6 Use environment-scoped secrets for deployments

Bind sensitive credentials to protected environments with reviewer gates.

## 5. `pull_request_target` rules

### 5.1 Prefer `pull_request`

`pull_request` runs in the fork context with safer defaults.

### 5.2 Never check out PR head with `pull_request_target`

```yaml
on: pull_request_target
steps:
  - uses: actions/checkout@{SHA}
    with:
      ref: ${{ github.event.pull_request.head.sha }}
```

This is dangerous because it executes attacker-controlled code with elevated permissions.

### 5.3 Use the two-workflow pattern for privileged PR operations

1. Unprivileged `pull_request` workflow builds artifacts.
2. Privileged `workflow_run` consumes trusted artifacts.
3. Never execute untrusted PR code in the privileged workflow.

### 5.4 Require approval for fork PR workflows

Use repository settings to require maintainer approval before running workflows on forks.

## 6. Environment and deployment protections

### 6.1 Use GitHub Environments with required reviewers

```yaml
jobs:
  deploy:
    environment:
      name: production
      url: https://example.com
```

### 6.2 Restrict environments to specific branches

### 6.3 Set wait timers on sensitive environments

## 7. Concurrency controls

### 7.1 Deployments: prevent parallel runs

```yaml
concurrency:
  group: deploy-production
  cancel-in-progress: false
```

### 7.2 CI: cancel outdated runs

```yaml
concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true
```

## 8. Additional hardening

### 8.1 Always set `timeout-minutes`

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 30
```

### 8.2 Add `CODEOWNERS` coverage for `.github/`

### 8.3 Self-hosted runner rules

- Do not use self-hosted runners for public repositories.
- Treat runner filesystem persistence as a secrets and isolation risk.
