---
name: apple-notes
description: Search, read, create, append to, replace, move, and delete Apple Notes notes and download note bodies or attachments through the installed apple-gateway CLI on macOS. Use when Codex needs to find notes, summarize note content, create a note, edit its body, move it to a folder, retrieve an attachment, or remove a note.
---

# Apple Notes

Use `apple-gateway-reader` for reads and `apple-gateway` only for requested
mutations. Treat the live schema as authoritative.

## Workflow

1. Resolve accounts and folders with `noteAccounts` and `noteFolders` only when
   needed, then use `notes` or `note` with narrow fields and filters.
2. Do not expose unrelated note content. Treat password-protected notes as
   unavailable rather than attempting to bypass protection.
3. For creation, prefer `bodyText` unless the user supplied or requires HTML.
   Resolve `accountId` or `folderId` when a destination was specified.
4. Before `updateNoteBody`, `moveNote`, or `deleteNote`, query the exact note by
   ID and disambiguate title matches. Explicitly choose append versus replace.
5. Re-query the note after a mutation.

When a result returns `downloadKey`, materialize it explicitly:

```bash
apple-gateway file download --key "$download_key" --output-dir "$output_dir"
```

Use a user-selected output directory when provided. Otherwise use a
task-specific directory and report the written path. Never open or summarize
attachments beyond the user's requested scope.

If access fails, inspect `apple-gateway permissions status --json`. Request the
`notes` permission only when the approved task requires the macOS prompt.
