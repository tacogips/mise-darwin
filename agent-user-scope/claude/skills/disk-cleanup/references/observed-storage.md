# Desktop storage observations (2026-10-19)

These are results from one authorized cleanup, not a deletion schedule. Measure
again on the current host and apply the user's current scope and retention.
Paths below are home-relative or generic; preserve backups and actual data.

## Where storage accumulated

- Worktrees each carried their own Rust targets, Swift compilation results,
  dependencies, and copied test applications. Small source trees did not imply
  small checkouts. A shallow scan of `~/gits` also missed builds in `/private/tmp`.
- Riela and its worktrees together occupied roughly 102 decimal GB during the
  investigation. The main `dist` alone was about 50 GiB. Versioned
  `dist/homebrew/{build,work}` and `dist/homebrew-cask/{build,work}` contained
  repeated Swift build stores and staged releases, alongside compressed archives.
- Temporary Swift scratch stores did not always use the name `.build`: examples
  included `baseline-build`, `process-test-build`, `p1-dispatch`, and
  `notion-integration-build`. Confirm a Swift store through `workspace-state.json`
  or `build.db` and architecture/triple output directories. Preserve the scratch
  source and dependency checkouts; do not delete a whole `tmp` tree.
- The desktop had separate Apple `container`, Colima/Docker, and Podman storage.
  Apple container storage was about 45 GiB; Colima about 28 GiB. Docker persistent
  volumes were only about 276 MB, all referenced. Volumes were not the main cause.
- Simulator device data occupied about 66 GiB; iOS DeviceSupport about 17 GiB.
  Device data includes installed applications and their persistent state. Neither
  an old OS version nor a shut-down device makes all of that state disposable.
- Other retained data included an Android backup (about 36 GiB), audio/sample
  libraries under `/Users/Shared` (about 30 GiB), mise tools (about 25 GiB), and
  separate rustup toolchains (about 10 GiB). These are not generic caches.
- Browser code-sign copies under `/private/var/folders/*/*/X` appeared as
  `Google Chrome.app.bundle` / `Brave Browser.app.bundle`, rather than `*.app`.
  Their apparent aggregate size was about 137 GiB. Verify bundle identifiers and
  open-file/process references; these are separate from browser user profiles.

## Verified cleanup results before release/history cleanup

- Removed 43 confirmed Cargo targets, roughly 177 GiB in aggregate. Checked for
  Rust build markers, tracked files, and process references. Sources merely
  named `target` inside dependency crates were excluded.
- Removed 89 Swift/Xcode compilation directories, roughly 43 GiB, while retaining
  SwiftPM checkouts, binary dependencies, and release archives at that stage.
- Removed 25 Monja test-app/simulator output directories, roughly 3.2 GiB.
  Monja shrank from about 6.5 to 2.8 GiB; Apple Gateway from 2.9 to 1.2 GiB;
  Konjac from 7.6 GiB to about 824 MiB.
- Removed 13.61 decimal GB of Docker build cache. Ran Colima filesystem trim and
  checked host free space; deleting guest files alone is not sufficient proof.
- Removed 85 old unused browser application copies; apparent removed size was
  about 108 GiB. Host free space did not grow by that amount because cloned/shared
  blocks cannot be added as independent physical usage.
- With explicit authorization, removed Codex/Claude histories older than a week,
  about 4.5 and 2.5 GiB respectively. Preserved settings, credentials, skills,
  memories, current runtimes, and active databases.
- For AI-native research, removed 185 original PDFs (about 304 MiB) after matching
  completed OCR, page counts, and SHA-256 values for original/OCR PDF/OCR text.
  Preserved all OCR PDFs and text, manifests, source URLs, and a deletion report.
  The research tree remained about 5.7 GiB: deleting original PDFs does not remove
  larger OCR derivatives, disclosures, or other research data.

## Additional release and scratch cleanup

After the user explicitly authorized deletion of old release artifacts:

- Removed 1,768 old-version release files/directories, about 58.1 GiB nominal,
  across gateway products, Riela, and related projects/worktrees. This included
  old archives, checksums, staged apps, and versioned build stores.
- Grouped candidates by product and compared numeric semantic-version components
  across packaging roots. Retained the newest version's entries, including its
  platform variants; excluded tracked files, escaping symlinks, and open files.
  No Git release/tag or remote asset was deleted.
- A second scan found arbitrary-named Swift scratch stores and Rust targets in
  `/private/tmp/nodetto-release-*`, outside the initial repository scan. Removed
  20 confirmed build-output directories, about 40.1 GiB nominal. One recently
  modified/active candidate was retained. Scratch sources were preserved.

## Riela history is database-backed

`~/.riela/sessions/runtime-records/runtime-message-log.sqlite` held most of the
roughly 8 GiB of user-scope Riela history. Another store existed under
`~/.riela/sessions-telescreen/runtime-records`. Root directory/file ages did not
represent individual session ages.

- Inspect the installed schema before pruning. This observed schema used SQLite
  JSONB BLOBs, not UTF-8 JSON: `json.loads(blob)` failed. Use a JSONB-capable SQLite
  version and `json(...)` / `json_extract(...)` when decoding is needed.
- Prefer stored/generated summary columns (`session_status`, `root_session_id`,
  `parent_session_id`, `updated_at`) over repeatedly decoding multi-gigabyte JSON
  histories. Inspect `PRAGMA table_xinfo`, which includes generated columns.
- Apply the authorized cutoff to ended sessions. Preserve running, paused,
  waiting, recent, and otherwise resumable sessions and their connected session
  trees. Do not infer completion from old modification times or stale locks.
- Inspect related message, payload-index, CLI-session, and nested-invocation
  records. Prune a consistent set in a transaction; do not unlink a live SQLite
  file or delete only its WAL/SHM files. Avoid application/schema migrations.
- Physical space is not necessarily returned by `DELETE`. Check integrity and
  use supported compaction or SQLite `VACUUM` when the database is idle and there
  is enough free space. Report retained old sessions and why they were retained.

## Completed Riela history cleanup

The user explicitly included old Riela history/logs in this pass. A seven-day
cutoff was applied, consistent with the session's earlier history-retention
request; it is not a permanent default for future users or runs.

- Removed 547 completed/failed sessions across the main and Telescreen stores.
  Preserved 552 sessions, including all 12 marked running and recent sessions.
  Parent/root/nested-invocation connections were considered together so an old
  terminal member did not remove a retained tree's dependencies.
- Removed matching messages, payload-index entries, CLI records, and nested
  invocation rows in transactions. Compared retained session summaries before
  commit, compacted with `VACUUM`, and obtained `PRAGMA quick_check = ok` for both
  databases. Their combined file sizes fell from 7.26 to 3.33 GiB.
- Removed 46 old unopened log files, about
  314 MiB. Current workflows, registries,
  settings, running sessions, and current logs were retained.
- After the release, scratch-build, and history pass, the host reported about
  310 GiB free (333 decimal GB), versus about 223 GiB at the start
  of that pass. Ongoing builds and shared blocks mean nominal deleted sizes
  should not be substituted for the actual free-space measurement.

## Measurement and execution lessons

- Marketing GB and `df` GiB differ. This nominal 1 TB drive's main APFS container
  was about 995 decimal GB. Use consistent units in before/after reports.
- The writable Data volume and APFS container provide different scopes; include
  system/preboot/recovery/VM consumption when explaining total disk occupancy.
- Do not sum parent and child paths, separately measured hard links/clones, or
  mounted simulator images as independent physical usage.
- Avoid simultaneous recursive scans of home, Data, and repositories. They
  repeated millions of file visits and delayed useful results. Discover bounded
  candidates, measure once, and report progress while large deletions finish.
- Long-running builds continued during cleanup and regenerated some outputs.
  Recheck open files/working directories, preserve active output, and report
  final `df` rather than subtracting nominal directory sizes from a past value.
