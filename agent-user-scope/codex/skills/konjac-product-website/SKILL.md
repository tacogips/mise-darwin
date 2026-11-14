---
name: konjac-product-website
description: Build, edit, review, or verify the Konjac public product website in `pubpage/`, including the English and Japanese landing pages, product messaging, App Store links, QR code download surfaces, screenshots, privacy links, Vite assets, and Cloudflare-ready build output. Use for requests to change the Konjac website, landing page, localized marketing copy, site download CTA, website screenshots, or website validation.
---

# Konjac Product Website

Maintain the public Vite site in `pubpage/`. Keep both landing pages accurate, accessible, localized, and aligned with the current ad-free product build.

## Inspect Before Editing

1. Preserve unrelated worktree changes. In particular, do not add generated Fastlane reports or `pubpage/dist/` output unless the user explicitly requests them.
2. Read `AGENTS.md`, `pubpage/package.json`, `pubpage/src/main.js`, `pubpage/src/styles.css`, `pubpage/index.html`, and `pubpage/ja/index.html`.
3. Inspect relevant assets under `pubpage/public/` before changing screenshot or image references.
4. Use `rg` to find every related copy string or link so English and Japanese do not drift.

## Product and Public-Site Rules

- Describe Konjac as an instant, continuous OCR-note workspace: users capture consecutive notes without leaving the camera workflow.
- Present Apple on-device processing and user-selected AI providers as optional processing choices; users supply any external-provider credentials.
- Keep language-learning examples grounded in books and video subtitles, preserving source text alongside translations.
- Do not position Konjac as a travel or sightseeing app unless a specific example truly requires it.
- The first viewport must keep a real localized app capture and explain the capture-to-OCR-note workflow immediately.
- Never describe the private repository as open source or link public pages to private GitHub repositories or issue trackers.
- Keep `/privacy/` and `/ja/privacy/` links correct. Do not imply advertising is active in the current ad-free build.

## Landing-Page Changes

- Update equivalent English and Japanese content in `index.html` and `ja/index.html` together unless the user explicitly requests one locale.
- Keep page metadata, canonical links, `hreflang`, image `alt` text, navigation labels, and CTA labels localized.
- Reuse the existing CSS design system in `src/styles.css`; verify the change at desktop and narrow mobile widths.
- Use semantic links and buttons, visible focus states, and concise accessible names.

## App Store CTA and QR Code

- Use the canonical App Store URL `https://apps.apple.com/app/id6787576273` for Konjac.
- Keep the URL centralized as `appStoreURL` in `src/main.js`; all visible App Store buttons and QR-code targets must use the same URL.
- Generate QR codes client-side using the `qrcode` dependency and a `<canvas data-app-store-qr>` element. Do not use third-party QR image services or send visitor data to a QR service.
- Make the QR panel itself a link to the App Store, provide localized text, and hide the canvas gracefully if rendering fails.

## Verify

Run from `pubpage/` after website changes:

```bash
npm run check
npm audit --omit=dev --audit-level=high
```

Also check for malformed whitespace and inspect the scoped diff:

```bash
git diff --check
git diff -- pubpage
```

For visual requests, start the Vite server with `npm run dev -- --port 4173` and open `http://127.0.0.1:4173/` and `/ja/` in Brave Browser using the browser-computer-use skill. Stop the server when it is no longer needed.

Do not deploy or publish the site unless the user explicitly asks.
