# Rosenpfad backup qualification

The existing reader already persists font size, line spacing and background.
The existing native split view already reverses the two tabs and exposes a
draggable divider. `check-workspace.cjs` now exercises those capabilities.
No redundant reader or split implementation was added.

The new backup buttons live in the Rosenpfad section of `about:rosavio-notes`:

- Export contains the explicitly saved trail only: name, ordered passages,
  source links, step notes and current position. General notes, other reading
  places, home shortcuts, bookmarks, preferences and browsing history are excluded.
- Restore accepts version 1 JSON, at most 512 KiB and 30 passages. Only bounded
  text and HTTP(S) text-fragment URLs without credentials are accepted. Unknown
  fields, future versions, duplicate steps and malformed files are rejected.
- Confirmation replaces the draft trail only. The existing Save button commits
  it using the existing revision-conflict protection. Cancelling or invalid data
  does not alter the saved state. Unrelated unsaved notes remain in the editor.
- The file is unencrypted personal data; the translated notice asks users to
  keep it private. No cloud service or new network connection is used.

All six new strings are present in all twenty interface languages, including RTL.
The native backup test exercises a real downloaded file and an isolated file-picker
selection fixture, the confirmation dialog, cancellation, explicit save and invalid
JSON. It does not relax the content sandbox or signature settings.

The branch-only feature workflow creates Windows and Linux candidates using the
existing signed-update checks. Flatpak reuses the qualified Linux candidates in a
temporary signed repository. It cannot publish through that test-only path. Public
release/feed verification remains a separate release gate; test artifacts are not
advertised as published releases.
