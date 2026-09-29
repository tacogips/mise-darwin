---
name: invoice-update-download
description: Use when Codex needs to update invoice, estimate, quotation, receipt, purchase-order, or other billing-document fields in an accounting or invoicing system, then download corrected PDF files and verify their rendered contents. Trigger for requests involving document corrections, recipient or issuer changes, dates, subjects, line items, amounts, PDF downloads, browser-based billing tools, API-backed billing tools, or repeated regeneration of corrected billing PDFs.
---

# Invoice Update Download

## Overview

Update billing documents, download the corrected PDFs, and verify the final files before handoff. Keep the workflow generic: never persist client names, addresses, email addresses, project titles, authorization codes, tokens, or document identifiers in git-managed content.

## Related Skills

- Use `computer-use:computer-use` for operating local app UI.
- Use `brave-browser-computer-use` for browser-based accounting or invoicing systems.
- Use `pdf:pdf` for rendering and visually verifying downloaded PDFs.

## Workflow

1. Capture the requested changes.
   - Extract the exact fields to change: document type, document number, subject, date, recipient, issuer, address, contacts, line items, tax, totals, notes, and target file names.
   - Treat screenshots and user-provided source URLs as task-local evidence, not reusable skill content.
   - If current public facts are needed, verify against a primary source before editing.

2. Identify the safest update path.
   - Prefer the service API for bulk or repeated field changes when credentials are already available for the task.
   - Prefer the browser UI when the API cannot express the required change, when authentication is already only in the browser, or when PDF download is UI-only.
   - When both are used, update through the API and verify through the UI before downloading.

3. Preserve existing document data.
   - Fetch or inspect the current document before updating.
   - Send only intended changes plus required unchanged fields.
   - Omit empty optional string fields when an API rejects empty strings or enforces minimum lengths.
   - Do not print, store, or commit secrets. Use environment injection, secret managers, or temporary shell scope only.

4. Apply corrections.
   - Update all requested documents consistently.
   - Confirm the service accepted the changes by reading back the record or visible UI.
   - Check any numeric or enumerated API fields against official schema or live documentation instead of guessing.

5. Download PDFs.
   - Use the user's requested naming convention exactly.
   - If no naming convention is given, use a deterministic generic pattern such as `billing_document_<document-number>.pdf`.
   - Save to the requested folder, or to `~/Downloads` by default.
   - If replacing existing files, move old copies to a timestamped folder under `/tmp` unless the user explicitly asks for overwrite-only behavior.

6. Verify rendered output.
   - Render each downloaded PDF to an image using the PDF skill workflow.
   - If Poppler is unavailable on macOS, use `qlmanage -t` as a fallback.
   - Visually verify the corrected fields, document title/month, document number, date, issuer, recipient, address, amounts, page count, and filename.
   - Do not rely only on API responses or PDF text extraction for final approval.

7. Report completion.
   - List the final local file paths.
   - Summarize the corrected fields without exposing secrets.
   - State explicitly whether any email draft, upload, or send action was not performed.

## Communication Boundary

Downloading a corrected PDF is allowed when requested. Sending email, editing a message draft, uploading corrected documents to a third-party recipient, or otherwise representing the user to another party requires explicit user confirmation immediately before that action.

## Privacy Guardrails

- Do not add task-specific customer names, vendor names, addresses, email addresses, project titles, document numbers, or account IDs to tracked repository files.
- Keep task-local notes in `/tmp` or transient command input, and delete them when they are no longer useful.
- Before creating or modifying a skill, script, or repository file, scan it for accidental task-specific values.
