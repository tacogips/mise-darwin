---
name: disk-cleanup
description: Investigate low disk space on macOS and reclaim regenerable development caches, Rust targets, Swift builds, and container build storage while preserving source and persistent data.
---

# Disk Cleanup

Measure before deleting and report the final host free space. A request to free
space authorizes routine cleanup of identified, regenerable caches; carry it
through without asking again for each directory. Inspect data-bearing storage
and preserve it unless the user has authorized its deletion.

For this desktop's known storage hotspots, previous cleanup results, and Riela
history details, read [references/observed-storage.md](references/observed-storage.md).
Treat the measurements as historical evidence, not current sizes or permanent
authorization to delete data.

## Find the actual consumers

- Start with `df -h /System/Volumes/Data` on macOS. The root system volume alone
  does not show the writable data usage.
- Measure the home directory, repositories, Library, application storage, tool
  caches, and container storage. Include hidden directories and nested worktrees.
- Use bounded, pruned scans: skip `.git`, dependency trees, and known build
  directories during discovery, then measure each candidate once. Avoid several
  concurrent full-home scans or a pipeline that hides all progress until sorting.
- `du` totals may double-count shared/cloned data across separate invocations.
  Report actual host free-space change separately from nominal sizes removed.

## Rust and Swift build outputs

Always consider **both Rust and Swift**, including temporary and sibling
worktrees. Source repositories can be small while each worktree has gigabytes
of duplicate build outputs.

- Rust: find `target` directories; confirm Cargo output through `.rustc_info.json`,
  `CACHEDIR.TAG`, or `debug/.fingerprint` / `release/.fingerprint`. A source
  directory merely named `target` is not a cleanup candidate.
- SwiftPM: inspect `.build/*-apple-*` compilation directories. Preserve
  `checkouts`, `repositories`, `artifacts`, workspace metadata, and any locally
  modified dependency sources. Removing only compilation output avoids losing
  dependency edits or required downloaded binary artifacts.
- Xcode: inspect generated object/product and DerivedData directories, including
  `~/Library/Developer/Xcode/DerivedData` and per-project `.build/xcode-*`.
  Preserve `.xcarchive`, dSYM archives, signing material, and exported releases
  unless their deletion is authorized. Do not delete every `xcode-*` directory
  based on its name alone.
- Tauri/iOS: inspect `src-tauri/gen/apple/build` and temporary `.app` bundles.
  Preserve generated project files, custom native code, app data, and archives;
  `gen` and `tmp` are not blanket deletion targets.
- Before deleting, ensure the exact output contains no tracked source, is not a
  symlink escaping scope, and is not used by a compiler, test runner, running
  executable, or active build. Use process paths and working directories; skip
  an active project. Do not stop the user's processes to make deletion possible.
- Delete complete confirmed build-output units, then report that the next build
  will regenerate them. Do not run builds or tests just to verify cleanup.

## Other development and container storage

- Inspect `dist`, packaging `build`/`work` staging trees, and duplicate release
  artifacts. Distinguish reproducible staging files from signed releases and
  historical archives. Keep the latter unless deletion is authorized.
  When the user explicitly requests removal of old releases, include old signed
  archives and checksums as well as their staging/build trees. Group by product,
  compare numeric semantic versions, retain the newest version's platform
  variants, and exclude open files. Search sibling/temporary worktrees too;
  modification time alone does not identify the newest release.
- Package-manager caches can be cleared with their own cleanup commands when
  available. Avoid partial package deletion that leaves a cache entry appearing
  complete. Preserve active installs and tool runtimes in use.
- On macOS, inspect `/private/var/folders/*/*/X/*code_sign_clone` for accumulated
  browser application copies. Verify the copied `.app.bundle` identity through
  `Contents/Info.plist`. Remove only old copies with no open files or running
  process references, using a complete inventory for the owning user. Preserve
  the active copy and browser profiles; never clear `/private/var/folders` broadly.
- Inspect Docker, Podman, and Apple `container` separately using their local CLI
  disk-usage commands. Prefer unused build-cache cleanup. Do not equate an
  unreferenced volume with disposable data: it may contain a database.
- Preserve running containers, persistent volumes, VM disks, and backups unless
  the user authorized their removal. Do not use broad system/volume prune flags
  as a substitute for inspecting these resources.
- VM-internal deletion may not release host space immediately. For Colima,
  `colima ssh -- sudo fstrim -av` can return unused blocks without stopping the
  VM; verify host `df` afterward. If a cleanup command stalls, bound retries,
  cancel only the command you started, and report that cleanup as unconfirmed.

## Histories and source documents

- Apply history retention only when requested. Use the authorized age cutoff
  for conversation/log/cache files; preserve configuration, credentials, skills,
  memories, and active SQLite databases. Age alone never makes these disposable.
- Delete source PDFs only when authorized and matching completed OCR is verified
  through the manifest, page counts, nonempty text, and hashes. Preserve OCR
  text/PDF, provenance, source URLs, and retrieval metadata. Record removed local
  source files so stale manifest paths are not mistaken for available originals.

Finish with actual space reclaimed, the main deleted categories, retained large
data, and any cleanup that could not be confirmed.
