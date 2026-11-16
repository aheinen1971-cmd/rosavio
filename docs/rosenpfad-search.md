# Rosenpfad search (prepared)

The notes page filters the existing trail by saved quote, full URL and step note.
The model stores passages rather than page titles; no browsing history or title
collection was introduced. All search terms must match; matching is case-insensitive
using the selected locale. The counter displays visible matches out of all steps.

Search is transient UI state: it never saves, changes the active passage, reorders
steps or changes backup contents. Row actions retain original indices when filtered.
The existing explicit Save and revision-conflict protection remain unchanged.

Both new strings are included in all twenty locales. Unit checks exercise all
thirty allowed steps, URL/note/quote matches, Unicode, literal markup, no results
and clearing, with unchanged data. Native Windows renderer fixtures cover the
twenty translated interfaces without personal profiles. These fixtures are not
new signed Windows/Linux/Flatpak package qualification. The native release checks
now also assert search behavior and translated labels when qualifying candidates.

Not published; no product build or release was triggered for this preparation.
