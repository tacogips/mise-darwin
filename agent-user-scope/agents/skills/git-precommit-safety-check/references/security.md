# Commit Target Security Reference

This reference is for manual review of Git commit targets before commit or push.
It complements automated scanners and intentionally does not depend on gitleaks.

## Prohibited Content

- Real credential values, access tokens, API keys, session cookies, OAuth
  secrets, JWT signing secrets, private key contents, seed phrases, passphrases,
  database passwords, and cloud provider credentials.
- Credential-bearing URLs, including URLs with embedded usernames, passwords,
  tokens, or signed query parameters.
- Private repository URLs unless the user explicitly asked to include them.
- Machine-local absolute paths that reveal a user name, host layout, checkout
  location, local cache, private config directory, or workstation-specific state.
- Generated outputs that embed environment variable values, credential file
  contents, local machine metadata, or private service endpoints.

## Allowed Content

- Environment variable references such as `$GITHUB_TOKEN`,
  `${GITHUB_TOKEN}`, or `process.env.GITHUB_TOKEN`.
- Placeholder values such as `<token>`, `<home>`, `<workspace>`,
  `<private-repo-url>`, and `<redacted>`.
- Relative paths from the repository root.
- Generic instructions to configure credentials through a secret manager,
  environment variable, or user-local file, as long as no real value is present.

## Review Procedure

1. Determine the actual commit target:
   - staged patch for a new commit
   - `HEAD` patch for an already-created local commit
   - amended patch when preparing `git commit --amend`
2. Inspect file names and patch content. Treat generated lockfiles, snapshots,
   fixtures, logs, and documentation examples as in scope.
3. Search only the commit target when possible. Avoid broad scans that report
   unrelated historical or user-local files.
4. For any suspicious value, verify whether it is a placeholder or a real value.
   If uncertain, stop and ask before committing.
5. Replace sensitive or machine-local content with a placeholder, a relative
   path, or a documented environment variable reference.

## Useful Patterns

These patterns are intentionally written as review hints, not as an exhaustive
scanner:

```text
credential keywords: token, secret, password, passwd, api_key, apikey, private_key, auth
private key headers: PEM/OpenSSH private key block boundaries
token-looking prefixes: ghp_, github_pat_, npm_, xoxb-, xoxp-, sk-
local path hints: /[Uu]sers/, /[Hh]ome/, C:\\[Uu]sers\\
credential URL hints: ://[^/[:space:]]+:[^/[:space:]]+@
```

## Reporting

Report `Pass` only when the reviewed commit target has no issues. For problems,
report the category and file path, but redact values.
