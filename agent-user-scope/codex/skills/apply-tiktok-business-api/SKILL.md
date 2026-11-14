---
name: apply-tiktok-business-api
description: Prepare, submit, and follow through a TikTok API for Business application, including official API research, Riela-assisted design, portal registration, use-case text, scopes, public redirect URLs, app logos, review follow-up, secure App ID/secret and token storage in kinko, OAuth authorization, sandbox verification, and a sanitized handover. Use when Codex needs to create or update a TikTok Business/Marketing API app, obtain credentials, configure callbacks or permissions, or verify an approved app end to end.
---

# Apply for TikTok Business API

Complete the application lifecycle without exposing credentials or overstating
approval or live-test status.

## Establish current state

1. Read the repository's `AGENTS.md` and any existing design, implementation,
   decision, or handover documents before acting.
2. Inspect the current TikTok portal in the existing signed-in browser session.
   Resume an existing registration, form, pending review, or approved app
   instead of creating duplicates.
3. Record separately:
   - developer identity and company registration state;
   - app submission and review state;
   - requested and granted scopes;
   - App ID/secret availability;
   - OAuth authorization and advertiser grants;
   - local credential presence;
   - offline tests and authenticated provider tests.
4. Never equate a browser login, Ads Manager advertiser ID, submitted app,
   granted scope, stored credential, or successful API call with any other item
   in that list without evidence.

## Research and design

Use the user-scoped `riela` skill for research, design, implementation, or
review work when Riela is requested or already part of the project workflow.
Prefer its narrowest applicable design/implementation workflow.

Verify time-sensitive behavior against current official TikTok documentation
before relying on it. Use only first-party TikTok sources for endpoint paths,
OAuth parameters, callback requirements, permissions, token lifecycle, rate
limits, and review rules. Preserve source links and the retrieval date in the
project's design evidence when implementation decisions depend on them.

Treat portal permission approval and implemented API surface as separate. A
portal app may request broad or all scopes while a local gateway implements a
small allowlisted surface. Do not add arbitrary URL or request-body passthrough
to make the code appear to support all APIs.

## Prepare the application

Collect or discover these non-secret inputs:

- app name and owner/business identity;
- accurate English use-case description;
- test-account identity and intended owned/authorized advertisers;
- API families required now and planned later;
- public HTTPS advertiser and TikTok-account-holder redirect URLs;
- compliant app logo;
- repository credential and deployment conventions.

Write the description truthfully. Include what will be advertised, expected
e-commerce or TikTok Shop use, data/API workflows, account ownership or
authorization boundaries, and security controls when relevant.

Do not use `localhost` as a registered callback when TikTok requires an
internet-reachable URL. Verify the current rule, require an exact URL match,
and confirm the deployed callback safely handles query parameters without
logging authorization codes. Prefer a dedicated callback path over a generic
homepage when one can be deployed safely.

Generate or reuse a logo that meets the portal's current size, format, and byte
limits. Inspect the final file before upload. Keep a reusable copy in the
project only when it belongs there.

Default to least-privilege scopes. If the user explicitly requests all scopes,
select all available categories, state that broad review may require additional
justification, and record the exact requested categories. After approval,
record the scopes actually granted.

## Operate the portal safely

Use the in-app browser or Computer Use skill because the existing browser may
contain the signed-in TikTok session. Re-query the latest page state before
actions, especially after user interaction or navigation. Prefer accessible
element operations; use coordinate clicks only after inspecting a current
screenshot.

Fill and validate all fields, then summarize the final app name, description,
callbacks, scopes, and logo state. Pause immediately before the final Submit
action and obtain action-time confirmation because submission creates or
materially expands persistent API access. A user's explicit instruction to
submit after seeing that summary is sufficient confirmation.

Never enter payment, tax, legal attestation, identity-verification, or business
ownership information for the user. If required, stop and let the user enter
it. Re-query the portal afterward and continue.

After submission, verify the success state. If review is pending and App ID or
Secret displays as unavailable, report the genuine blocker; do not create
placeholder secrets or claim authenticated verification.

## Handle approval and credentials

When the app becomes approved:

1. Inspect the granted scopes and any review conditions.
2. Obtain App ID and Secret without printing or summarizing their values.
3. Store secrets in kinko using interactive entry. Do not pass values with
   `--value`, command arguments, environment-dumping commands, or shell history.
4. Use stable environment-style key names, separated by environment and
   capability, for example:
   - `TIKTOK_SANDBOX_APP_ID`
   - `TIKTOK_SANDBOX_APP_SECRET`
   - `TIKTOK_SANDBOX_READER_ACCESS_TOKEN`
   - `TIKTOK_SANDBOX_WRITER_ACCESS_TOKEN`
5. Verify only key presence and injection success. Never echo the values.
6. Keep non-secret profiles limited to kinko-injected environment-variable
   names, confirmed advertiser allowlists, capability, API version, and fixed
   operation allowlists.

Re-check official OAuth documentation before constructing the authorization
URL. Immediately before the final TikTok account authorization action, obtain
action-time user confirmation because it grants persistent account access.
Validate OAuth state, exact callback matching, code confidentiality, exchange
behavior, expiry, refresh, and revocation. Store returned tokens directly in
kinko without exposing them.

## Verify behavior

Run verification in increasing-risk order:

1. Local lint, formatting, unit tests, builds, and artifact-boundary checks.
2. Unauthenticated HTTPS reachability to fixed official API origins.
3. Local credential-presence/configuration checks without rendering secrets.
4. Authenticated authorized-advertiser discovery.
5. Read-only advertiser details and one bounded list/report request.
6. Writer verification only against an explicitly confirmed non-serving
   sandbox resource with a reviewed current state and desired reversible or
   no-op outcome.

Do not claim end-to-end verification until an authenticated official API call
succeeds. Do not mutate a live-serving campaign merely to prove connectivity.
Record sanitized command names, timestamps, result categories, advertiser
identity confirmation, and failures; omit sensitive response bodies and all
credentials.

## Preserve handover state

Create or update a project handover whenever work pauses for review, user input,
credentials, OAuth approval, or a safe sandbox resource. Read
`references/application-record-template.md` when writing that record.

The handover must distinguish completed, pending, blocked, and unattempted
work; include exact next actions; and never contain secrets. Link it from the
project README when appropriate.
