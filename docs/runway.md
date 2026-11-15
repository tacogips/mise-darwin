# Runway from any directory

## Managed Runway CLI

Bootstrap installs `runwayml-cli` through the managed Homebrew tap. To install
only this CLI and authenticate its creative MCP connection:

```sh
mise -E macos-arm64 -E desktop bootstrap packages apply brew:tacogips/tap/runwayml-cli --yes
runwayml-cli auth login
runwayml-cli auth status
runwayml-cli mcp tools
```

An existing valid OAuth login can be reused. Tool discovery checks live access
without generating media. Developer REST calls require a separate API key.

## Choose the connection

| Route | Authentication | Purpose |
| --- | --- | --- |
| Creative MCP: `https://mcp.runwayml.com/mcp` | Runway app OAuth | Generate media in an assistant, using the app account's credits |
| Developer API: `https://api.dev.runwayml.com/v1` | `RUNWAYML_API_SECRET` | Direct HTTP requests and official Python/Node SDKs |
| Developer MCP: `https://dev.runwayml.com/mcp` | Developer Portal OAuth | Developer account tools, task lookup, model routers, and documentation |
| Runway website | Browser sign-in | Interactive Runway Agent and media tools |

The creative MCP and Developer MCP are different services. This repository
provisions the **creative MCP** under the Codex server name `runway`.
The Developer API requires a developer project, API key, and funded developer
credits. Do not assume a creative-app subscription or its OAuth grant supplies
API credentials or API credits. No purchase or generation is part of setup.

## Tools

Desktop bootstrap already provides Codex, Python, Node, cURL, jq, and kinko.
mise manages `uv` for isolated Python SDK runs, including a user-scope default
so its shim works outside this checkout. Homebrew provides `ffmpeg` (including
`ffprobe`) for inspecting and finishing media. A local
Runway MCP server, npm proxy, or Python server is unnecessary for the remote
HTTP MCP connection. Do not install an unrelated package named `runway`:
several other products use that name.

On an existing machine, install just the added tools without applying the
rest of bootstrap:

```sh
brew install ffmpeg
```

## Creative MCP setup

From any directory:

```sh
mise -C ~/gits/tacogips/mise-darwin -E macos-arm64 -E desktop run runway:setup
codex mcp login runway
codex mcp get runway
```

Complete sign-in and review the authorization in your browser. Setup merges
only these two Runway keys into `~/.codex/config.toml`, preserving other servers,
settings, custom Runway headers, and client-managed OAuth credentials:

```toml
[mcp_servers.runway]
url = "https://mcp.runwayml.com/mcp"
enabled = true
```

The configuration is user-scoped, rather than stored in a project's `.codex`
directory. A custom `CODEX_HOME`, project configuration, or selected profile
can change the effective configuration; inspect those if another directory
behaves differently. Never copy tokens between projects or commit OAuth data.

To configure another Mac without this repository, Codex also supports:

```sh
codex mcp add runway --url https://mcp.runwayml.com/mcp
codex mcp login runway
```

## Verify configuration and live access separately

```sh
cd /tmp
codex mcp get runway
codex mcp list
```

These commands verify saved configuration. An `OAuth` auth column identifies
the authentication mechanism; it does not prove that the current conversation
has initialized the server or loaded its generation tools.

After setup or login, start a fresh Codex conversation and inspect `/mcp` in
the CLI, or the MCP tool status in the app. Verify that Runway tools are listed
and make a read-only discovery/account request if the server provides one.
Do not spend credits just to test connectivity.

If a running conversation reports `unknown MCP server 'runway'` or exposes no
Runway tools, first compare `codex mcp get runway` from that directory and
`/tmp`. If both show the correct URL, investigate the client session rather
than adding duplicate project entries. Reload the MCP connection if the client
offers that action, or start a fresh session. Reauthenticate only when the
client reports an authentication failure. Changing directories alone does not
refresh a running conversation's tool catalog.

## Use the API without MCP

Create a project and API key in the [Runway Developer Portal](https://dev.runway.com/).
Store the key interactively in kinko's shared scope so the same profile can
resolve it from different directories:

```sh
kinko set-key RUNWAYML_API_SECRET --shared
```

Do not put the key in mise TOML, Git, command-line `--value` arguments, or shell
startup files. Inject only the required variable into a request process.

The official Python SDK is `runwayml`. `uv` can resolve it without installing
it into the system Python or requiring a project virtual environment:

```sh
uv run --no-project --with runwayml python -c 'from runwayml import RunwayML; print("Runway SDK import OK")'
```

That import check uses neither credentials nor credits. For a real integration,
pin a reviewed SDK version in the project's dependency lockfile or script
metadata. The following example retrieves an existing task; replace `TASK_ID`
with a task from the developer project:

```sh
kinko exec --env RUNWAYML_API_SECRET -- \
  uv run --no-project --with runwayml python -c \
  'import sys; from runwayml import RunwayML; print(RunwayML().tasks.retrieve(sys.argv[1]).model_dump_json())' \
  TASK_ID
```

For Node integrations, install `@runwayml/sdk` in the consuming project. Both
SDKs read `RUNWAYML_API_SECRET`. cURL can call the REST API directly as well;
use the documented endpoint, authorization header, and API version. Generating
images, video, speech, or music is a separate API call that consumes developer
credits. Media returned by a generation must be downloaded and verified before
publishing; Runway generation does not upload to Instagram automatically.

## Official references

- [Creative MCP connection and app credits](https://help.runwayml.com/hc/en-us/articles/51931843164691-Connecting-to-Runway-MCP)
- [API credentials and billing setup](https://docs.dev.runwayml.com/guides/setup/)
- [API quickstart, including cURL](https://docs.dev.runwayml.com/guides/using-the-api/)
- [Official Python and Node SDKs](https://docs.dev.runwayml.com/api-details/sdks/)
- [Developer MCP and its distinction from creative MCP](https://docs.dev.runwayml.com/guides/mcp/)
- [Codex MCP configuration](https://developers.openai.com/codex/mcp/)
