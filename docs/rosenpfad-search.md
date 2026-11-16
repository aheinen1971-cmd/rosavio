# Rosenpfad search

The notes page filters the existing trail by saved quote, full URL and step note.
The model stores passages rather than page titles; no browsing history or title
collection was introduced. All search terms must match; matching is case-insensitive
using the selected locale. The counter displays visible matches out of all steps.

Search is transient UI state: it never saves, changes the active passage, reorders
steps or changes backup contents. Row actions retain original indices when filtered.
The existing explicit Save and revision-conflict protection remain unchanged.

Both new strings are included in all twenty locales. Unit checks exercise all
thirty allowed steps, URL/note/quote matches, Unicode, literal markup, no results
and clearing, with unchanged data. Native release checks assert search behavior
and translated labels. The Windows, Linux and Flatpak candidates passed workflow
43911774147, including twenty interfaces and isolated signed update/profile checks.
The retained candidates are promoted without recompiling the browser. Public
release checks independently verify the real update channels before availability
is announced. Tests use isolated profiles, never personal browsing data.
