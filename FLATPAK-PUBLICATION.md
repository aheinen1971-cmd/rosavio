# Public Flatpak distribution gate

The local signed Flatpak update trial passed in run 40188454325. It used a
disposable CI identity. That identity is deliberately not a production trust root.

The intended free public installation URL is:
https://aheinen1971-cmd.github.io/rosavio/flatpak/Rosavio.flatpakref

The package ID is `io.github.aheinen1971_cmd.Rosavio`, architecture `x86_64`,
branch `stable`, with all twenty existing interface languages. The existing
TAR.XZ/MAR installations remain separate. Flatpak owns updates in this variant.

## Required identity approval

Approval received directly from the user on 25 October 2026. Both named
encrypted GitHub Actions secrets are now stored in the authorized repository.
The protected local recovery copy is outside the source tree. Public fingerprint:
`2E0679F4ADFCA8549DAF597810F7B311F9B1C264`.

Before production publication, obtain the user's specific approval to store a
new private OpenPGP signing key and its password as encrypted repository Actions
secrets `ROSAVIO_FLATPAK_SIGNING_KEY` and `ROSAVIO_FLATPAK_SIGNING_PASSWORD` in
`aheinen1971-cmd/rosavio`. Existing MAR-key approval does not cover this new key.
Pin the public fingerprint in tracked configuration. Never print or publish the
private key, use the test key as production, or disable GPG verification.

## Remaining publication work

1. Generate the approved persistent identity, keep a secure local recovery copy,
   and transfer only through GitHub's encrypted secret mechanism after approval.
2. Build and sign the repository from tested native Linux releases. Check signed
   commits and summary; generate installation descriptors with
   `scripts/prepare-flatpak-distribution.py`.
3. Host the signed OSTree repository with the existing website. Retain repository
   payloads in release assets and assemble the Pages deployment artifact, rather
   than accumulating binary history in the source branch. Keep below the Pages
   deployment size limit; preserve all twenty HTML pages and existing downloads.
4. Test installation from the real public `.flatpakref` in a clean user
   installation with GPG verification, then publish a second genuine revision and
   prove `flatpak update`, browser restart, all twenty languages, profile,
   bookmarks, active protection, extension compatibility, desktop start and icons.
   Verify downloads/file portals and the browser sandbox without disabling it.
5. On failure restore the last working signed public repository/deployment.
   No completion claim until the public chain passes. Set up ongoing builds from
   tested Linux releases and verify a complete scheduled pipeline trial.
6. Only then advertise Flatpak on all twenty website pages and in Google Sites.

No paid service, new account, Flathub submission or acceptance of legal terms is
authorized by this implementation note. A Flathub listing remains a separate
review process. Do not interrupt the ongoing macOS builds.
