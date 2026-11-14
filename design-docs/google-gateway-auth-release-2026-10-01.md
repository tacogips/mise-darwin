# Shared Google gateway authentication release

The shared macOS profile declares `tacogips/tap/google-calendar-gateway` as
`latest`. The desktop Brewfile declares the Gmail roles, Docs/Sheets/Drive,
Analytics roles, Marketing, Document OCR and Service packages as unversioned
Homebrew dependencies, so the updated tap supplies the current releases.

## Published versions

| Package | Version |
| --- | --- |
| Google Calendar gateway | 0.1.9 |
| Gmail gateway roles | 0.1.17 |
| Google Docs/Sheets/Drive gateways | 0.3.6 |
| Google Analytics gateway roles | 0.1.5 |
| Google Marketing gateway | 0.1.4 |
| Google Document OCR gateway | 0.1.4 |
| Google Service gateway | 0.1.6 |

## Authentication convention

Set up one shared registered OAuth client through Service gateway. Native
`auth login` in every gateway uses that client unless an explicit product
client is selected. Google-side registration uses Google Auth Platform Console;
Service gateway imports and configures the downloaded client locally.

External credential use remains available without `auth login`. Canonical
product prefixes use `ACCESS_TOKEN` for a token string, `TOKEN_STORE_JSON` for
JSON contents and `TOKEN_STORE_PATH` for a private file path. Profile-specific
inputs add `CREDENTIAL_<NORMALIZED_ID>_` before the suffix. Gmail retains its
`GMAIL_GATEWAY_` prefix; the other products use `GOOGLE_<PRODUCT>_GATEWAY_`.

`auth logout` removes managed local credentials and the isolated gcloud binding,
preserves externally selected credential files/JSON and OAuth client setup, and
does not revoke the Google grant. Native login stores credentials in private
files by default.

## Verification scope

All 28 executable roots completed native browser login, external JSON credential
handling, local logout and login again. Supported Marketing product/role
profiles were covered separately. A real native login with an environment-selected
callback host, port and path passed and its listener closed afterward.

Live read requests passed for Calendar, Gmail, Docs/Sheets/Drive, Analytics,
Service reader, OCR, Search Console, AdSense, AdMob reader and Analytics Data.
Google Ads still requires an independently configured developer token for API
requests. AdMob writer exposes request preview only. Configured Web/public HTTPS
callbacks have fixture coverage; deployed HTTPS callbacks and a live registered
Web-client grant are not claimed.

The tap metadata workflow succeeded and all 13 formula entries plus the Calendar
Cask metadata matched release versions and committed Ruby checksums. Both Calendar
DMGs were signed, notarized, stapled and accepted by Gatekeeper.

## Local update verification

All 13 declared Homebrew packages passed audit, fetch, upgrade and formula tests.
All 28 installed executable roots passed 112 help, version, auth-help and external
credential status checks. Calendar Cask fetch and audit passed. Desktop mise
configuration validation passed, and bootstrap status reports Calendar 0.1.9
installed. One unrelated host resource differs; no unrelated setting was applied.

The old Calendar package directories and old command links are absent. Homebrew
resolves its old formula name as a rename alias to the current Google package.
No package pin changes are required because these declarations already select
the latest tap releases.
