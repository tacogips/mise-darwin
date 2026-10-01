---
name: google-service-gateway-oauth-setup
description: Set up Google gateway OAuth using Service gateway for GCP projects and API enablement, Google Auth Platform Console for Desktop/Web client registration, and Service gateway for local client import and native-login verification. Use for Google gateway credential bootstrap or client reconfiguration.
---

# Google gateway OAuth setup

Use Service gateway for Cloud operations and local configuration. Use the
Google Auth Platform Console only for steps that lack a supported public API.
Keep those two kinds of registration distinct: `clients register` imports an
already registered client locally; it does not create a client at Google.

## Establish the requested setup

Inspect installed command versions, `--help`, existing project records, client
files, and selected credentials before creating resources. Preserve the user's
chosen project ownership, number of clients, browser, and existing external
credential inputs. Reuse an existing project only when that matches the request.
Do not recreate projects merely because client registration is unfinished.

For the initial Cloud grant, use:

```sh
google-service-gateway-auth auth login --provider gcloud
```

A successful provider login selects private isolated ADC for Service roles.
Workspace gcloud grants additionally require a registered custom Desktop
client and the cloud-platform scope; gcloud does not create that client.

## Create projects and enable APIs through Service gateway

Use the writer's actual installed help and bounded operation polling:

```sh
google-service-gateway-writer projects create \
  --project-id "$PROJECT_ID" --display-name "$PROJECT_NAME" \
  --service "$API_ID" --timeout 180

google-service-gateway-reader services list \
  --project "$PROJECT_ID" --state enabled --all-pages
```

Repeat `--service` for additional APIs. If the project already exists, use
`services enable` or `services batch-enable`. Match required APIs against the
returned ENABLED list; exit 0 alone is insufficient. A polling timeout does
not establish failure: inspect the existing operation before retrying creation.
Do not attach billing unless that is part of the user's request.

| Product selector | APIs commonly required |
| --- | --- |
| service | cloudresourcemanager.googleapis.com, serviceusage.googleapis.com; add cloudbilling.googleapis.com and apikeys.googleapis.com for those features |
| calendar | calendar-json.googleapis.com |
| gmail | gmail.googleapis.com |
| docs | docs.googleapis.com, drive.googleapis.com |
| sheets | sheets.googleapis.com, drive.googleapis.com |
| drive | drive.googleapis.com |
| analytics | analyticsadmin.googleapis.com, analyticsdata.googleapis.com, tagmanager.googleapis.com |
| marketing | googleads.googleapis.com, adsense.googleapis.com, admob.googleapis.com, searchconsole.googleapis.com; add analyticsdata.googleapis.com for its analytics-data product |
| ocr | documentai.googleapis.com |

Select the API set from the products the user actually wants.

## Register the client in Google Auth Platform

Read current official documentation before assuming an API or CLI can replace
this step. General Google Auth Platform Desktop/Web clients differ from IAM
Workforce Identity Federation OAuth clients and former IAP-only clients.

If Console use is authorized, operate the user's selected browser through
Computer Use. In this user's environment use Brave and the Brave browser skill.
Use the exact project-specific URLs returned by `projects create` where possible.
Confirm the selected project in the UI before saving changes.

1. Configure branding, support/contact email, and the appropriate audience.
   Avoid Google-branded app names: `google-service-gateway` was rejected;
   `Service Gateway` succeeded. Do not infer an organization or choose Internal
   solely because the signed-in account belongs to Workspace.
2. Obtain applicable action-time approval before accepting Google's User Data
   Policy or creating persistent credentials. Batch equivalent project approvals
   when allowed by the active Computer Use policy; record the actual scope.
3. Create a Desktop client for a local CLI. Use a registered Web client for a
   deployed HTTPS callback. Choose the AI-agent designation according to the
   actual client use and Google's displayed instructions.
4. Download JSON before dismissing the creation dialog: Google may expose the
   new client secret only once. Keep the download outside Git, in a private
   directory, with mode 600; validate its `project_id` without printing secrets.
5. For an External app in Testing, add the authorized Google account as a test
   user and verify its saved row. Do not publish the app merely to finish a test.

Inspect fresh UI state after actions. A click is not evidence of a saved change.
In the Desktop type dropdown, End then Return selected the final Desktop option
when accessibility clicks only focused it; use this only after observing the
current menu order. Sanitize authentication URLs, client secrets, and clipboard
values before returning UI text. Avoid screenshots while a secret is displayed.

If browser use is prohibited, explain the missing supported registration API
and request local paths to already registered client JSON files. Do not silently
substitute a shared client when the user requested a client per project.

## Import through Service gateway and verify native login

Back up an existing private client before authorized replacement. Import:

```sh
google-service-gateway-auth clients register \
  --product "$PRODUCT" --file "$CLIENT_JSON" --replace
```

`PRODUCT` is one of the nine selectors above, and `CLIENT_JSON` is absolute.
Use `--replace` only for intended replacement. For a Web client, supply its exact
registered `--redirect-uri` and the required `--listen-host` / `--listen-port`.
Public HTTPS callbacks require TLS termination outside the local HTTP listener.
Desktop clients use loopback callbacks; configurable ephemeral ports are valid.

Run each requested gateway role's `auth login` without `--provider`, complete
its actual consent, then verify `auth status`, refresh where supported, and a
real read API request. Confirm successful native login cleared any earlier
selected gcloud binding. Keep credentials in the gateway's private file store;
do not opt into Keychain storage unless requested.

External JSON/path inputs override native files. Preserve them and scope any
verification overrides to the individual process. A stored READY status, fixture
OAuth server, or common client file does not prove a live grant for every role.
Verify the returned scopes and client/project association. Cloud grants can
require reauthentication under Workspace session controls; do not treat an
`invalid_rapt` refresh rejection as successful authentication.

Record project IDs, enabled APIs, client registration/import state, and actual
API checks without credential values. Report incomplete roles explicitly.

## Official references

- https://support.google.com/cloud/answer/15549257
- https://docs.cloud.google.com/mcp/set-up-authentication-mcp-servers
- https://docs.cloud.google.com/sdk/gcloud/reference/auth/application-default/login
- https://docs.cloud.google.com/iam/docs/workforce-manage-oauth-app
