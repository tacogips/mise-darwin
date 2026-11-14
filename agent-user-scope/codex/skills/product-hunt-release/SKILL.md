---
name: product-hunt-release
description: Prepare, create, review, and schedule Product Hunt launches from a product repository. Use when Codex needs to submit a product to Product Hunt, build or update a Product Hunt draft, choose launch copy and media, configure Built With or Shoutouts, associate makers, select pricing or tags, assess Product Hunt API support, recommend an audience-aware launch date, schedule a launch, or verify Product Hunt launch status.
---

# Product Hunt Release

Prepare accurate launch material from the product source, operate Product Hunt
through its visible UI, and verify the resulting draft or schedule.

## Required tooling

- Use the `brave-browser-computer-use` skill for all Product Hunt UI work.
- Follow its Computer Use confirmation policy. Product details, comments, drafts,
  and schedules are representational actions.
- Use internet search only for factual research. Prefer current official Product
  Hunt help and launch-guide pages for platform rules and timing guidance.

## Workflow

### 1. Establish the requested outcome

Distinguish among:

- preparing launch copy or assets without changing Product Hunt;
- creating or updating an unpublished draft;
- scheduling an existing draft;
- verifying a draft, scheduled launch, or live launch.

Resolve the product, repository, Product Hunt account, target audience, target
geography, and timing constraints from the request and available context. Do not
invent an account identity, launch date, customer segment, pricing model, maker,
or company claim.

If the user requests registration without a launch date, default to a completed
draft. Do not silently choose a public launch date.

### 2. Inspect the product source

Read repository instructions before acting. Inspect the narrowest useful set of
sources, including:

- README and product documentation;
- package or application metadata;
- license and pricing evidence;
- current release and installation instructions;
- dependency manifests, build configuration, and runtime integrations;
- logo, app icon, screenshots, and demo links;
- website, repository, store, and social links.

Prefer product facts already published by the project. Preserve unrelated local
changes. Never expose secrets, private URLs, credentials, telemetry, or
machine-local data in launch copy or uploaded media.

### 3. Verify current Product Hunt requirements

Browse current official Product Hunt documentation before relying on field
limits, media requirements, scheduling behavior, or launch-cycle timing.
Platform details change; do not rely only on remembered limits.

Confirm in the live form which fields and final actions are available. Treat
the visible UI as authoritative when it differs from older documentation.

### 4. Prepare the launch package

Draft concise, factual content:

- product name without promotional text;
- a clear tagline within the current limit;
- direct product URL, using the repository only when no better product page
  exists;
- description focused on users, differentiation, and concrete features;
- up to the current maximum number of strongly relevant launch tags;
- correct pricing and open-source status;
- maker attribution;
- a first comment covering motivation, audience, main capabilities, and the
  feedback requested.

Avoid unsupported superlatives, fabricated adoption, and security or privacy
claims not supported by the product.

Prepare Built With/Shoutouts from repository evidence:

- include only products that materially power the shipped product and have a
  genuine Product Hunt product entry;
- prioritize a required runtime or data source, the primary implementation
  platform, and a substantial user-facing framework;
- do not use incidental developer tools, optional install channels, or popular
  products merely for exposure;
- search Product Hunt for each candidate and verify the exact product identity
  before selecting it;
- omit a candidate when its Product Hunt identity is ambiguous or unavailable.

Select media in this order:

1. a square logo or app icon for the thumbnail;
2. the clearest product screenshot as the first gallery and social-preview
   image;
3. additional screenshots that demonstrate distinct workflows.

Prefer existing repository or README media. Verify dimensions, file size,
readability, and absence of sensitive data before upload. Use three or more
useful gallery images when available, but do not pad the gallery with duplicate
or low-value images. Generate new promotional artwork only when the user asks.

### 5. Operate Product Hunt

1. Open or focus Brave and inspect its current state.
2. Let the user handle login when credentials, MFA, or account selection require
   them.
3. Navigate to the new-product flow or the existing product draft.
4. Before entering content that Product Hunt may auto-save, present the proposed
   launch package and request action-time confirmation.
5. Enter the approved details and upload only approved assets.
6. Search and add the approved Built With/Shoutout products. Treat selecting a
   result as an immediate representational change unless the UI clearly defers
   it to a later save action.
7. Verify tags, open-source state, pricing, maker attribution, Built
   With/Shoutouts, gallery order, and first comment.
8. Create a draft or open the scheduler according to the requested outcome.
9. Inspect the completion page or status banner after the action.

Do not schedule or publish while the user asked only for preparation or a
draft. Do not call a draft or scheduled launch "published."

### 6. Choose a launch date

Base timing on current official guidance plus the stated audience:

- prefer a weekday for enterprise, professional, or workplace audiences;
- consider Product Hunt's current newsletter and category cadence when it
  directly matches the audience;
- prefer the beginning of Product Hunt's full daily cycle when the user has no
  conflicting constraint;
- avoid a partially elapsed launch day;
- leave enough lead time for the maker to monitor comments and promote the
  launch authentically.

State the selected weekday, calendar date, Pacific time, and the user's local
time. Label audience-based timing as a reasoned recommendation, not a guarantee.

Select the date in the scheduler, then stop immediately before the final
confirmation button. Explain that confirmation will publicly schedule the
launch, name the exact date and time, and request action-time approval. After
approval, confirm the schedule and verify the resulting banner.

## Product Hunt API decision

Check the current official Product Hunt API documentation before choosing an
automation path. The existence of GraphQL write scope does not by itself mean
that product launch creation or scheduling is supported.

Use the API only when all of the following are true:

- the current official schema documents the exact required mutation;
- the user's application has Product Hunt-approved write access;
- the mutation covers every required field and the desired draft, schedule, or
  publish state;
- using the API complies with Product Hunt's current terms and the user's
  authorization.

Do not create an OAuth application, request credentials, or solicit expanded API
access without explicit user authorization. When the public documented API lacks
the launch mutation or approved scope, use Product Hunt's visible submission UI.
Never infer an undocumented mutation or automate a private endpoint.

## Completion checks

Verify and report:

- Product Hunt product URL;
- draft, scheduled, or live status;
- exact launch date and timezone when scheduled;
- product name and tagline;
- thumbnail and gallery image count;
- pricing, open-source state, tags, and maker attribution;
- Built With/Shoutouts, including intentionally omitted candidates;
- any intentionally omitted optional fields.

Report only state visibly confirmed by Product Hunt.
