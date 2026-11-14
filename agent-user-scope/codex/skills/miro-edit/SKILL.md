---
name: miro-edit
description: Edit Miro boards through the Miro REST API and browser verification. Use when Codex needs to create, inspect, update, resize, move, or verify Miro topology diagrams, especially board items such as shapes, connectors, labels, network areas, and architecture diagrams whose board URL is supplied by environment variables or kinko-injected secrets.
---

# Miro Edit

## Overview

Use this skill to edit Miro boards with API-first changes and visual verification. Do not hard-code board URLs, board IDs, or tokens in skill files or generated scripts; read them from environment variables injected by the shell or kinko.

## Required Environment

Require:

- `MIRO_API_TOKEN`: Bearer token for Miro REST API.
- One board URL variable:
  - Prefer `MIRO_BOARD_URL` for generic tasks.
  - Use a project-specific variable such as `KESTRA_WORKGROUP_TOPOLOGY_MIRO_URL` when the user names an existing saved board.

If variables are missing, first check whether kinko can inject them:

```bash
kinko exec -- env | rg 'MIRO_API_TOKEN|MIRO_BOARD_URL|KESTRA_.*MIRO_URL'
```

Avoid printing token values. Board URLs are less sensitive, but still do not copy concrete URLs into this skill.

## Workflow

1. Resolve the target board URL from environment variables. If more than one board URL is available, choose the one matching the user request or ask a concise question.
2. Inspect existing board items before editing:

```bash
scripts/miro_api.sh items
scripts/miro_api.sh connectors
```

3. Make scoped edits with the Miro API. Prefer updating existing shapes and connectors over recreating a whole diagram.
4. Keep visual constraints explicit:
   - Area/zone boxes must contain their components.
   - Network labels must identify the boundary, such as `Network: GKE / GCP VPC` or `Network: On-prem / GCE subnet`.
   - Directional or forbidden traffic must be visible with labeled arrows.
5. Verify by API coordinates for containment and by browser screenshot when possible.

## Helper Script

Use `scripts/miro_api.sh` for common operations. It reads `MIRO_API_TOKEN` and board URL variables at runtime.

Supported commands:

```bash
scripts/miro_api.sh board
scripts/miro_api.sh items
scripts/miro_api.sh connectors
scripts/miro_api.sh patch-shape <shape-id> '<json-payload>'
scripts/miro_api.sh create-shape '<json-payload>'
scripts/miro_api.sh create-connector '<json-payload>'
```

Payloads are raw Miro API JSON. Generate them with `jq -nc` to avoid quoting mistakes.

## Browser Verification

When the user asks for Miro visual edits, open the resolved board URL in the browser and verify the result when a browser tool is available. If browser access is blocked or the page requires user login, verify through API item counts and coordinate checks, then tell the user what was and was not visually confirmed.
