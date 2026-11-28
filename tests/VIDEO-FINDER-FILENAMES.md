# Editable video filename — 28 November 2026

Prepared on feature/video-finder-names-20261128 from f8415b3. Not published or installed.

Rosavio's built-in Video Finder now offers the detected title in an editable field for YouTube, direct media and HLS downloads. The native helper accepts a title, never an output path. Sanitization, actual container extensions and collision numbering protect existing files. The staging worker continues using its safe internal video ID. Final downloads no longer expose its ID plus random UUID.

All 20 supported locales include the new label; RTL and narrow widths were checked. Web pages without individual video metadata may still suggest a page title, which can be edited. Existing downloads are not renamed.

Validation:
- 60 JavaScript regression tests passed (media, localization, background, native bridge).
- 9 existing native tests and 3 new groups passed, including real neutral video bytes, concurrent name collisions, invalid names, no-hardlink destinations and disk-full cleanup.
- All 20 localized UIs exercised in isolated Rosavio 161.0 against local neutral fixtures. Extension APIs simulated; this is not a final compiled package test.
- Secondary 320px UI tests covered 20 locales, direct/HLS save names, edited input preservation and RTL. Screenshots inspected for German and Arabic.
- Real YouTube extraction/download via the changed source host and unchanged installed Rosavio worker: Blender's Big Buck Bunny, original title and custom title. Both output files contain audio/video and pass full strict audio/video decoding.
- No personal browser profile or installed application changed. No GitHub build or publication started. Final Windows/Linux/Flatpak package qualification is still required before release.

Evidence: evidence/filename-rosavio/report.json, evidence/filename-ui/report.json and evidence/filename-youtube/report.json. Large local videos and isolated profiles are intentionally excluded from Git.
