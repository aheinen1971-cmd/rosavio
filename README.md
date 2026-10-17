# Rose Browser

Eigenstaendiges Windows-Browserprojekt auf Firefox-Basis. Dieses Verzeichnis
enthaelt die Rose-Anpassungen und den Update-Dienst; es ist noch kein fertiges
installierbares Browserpaket. Den aktuellen Stand dokumentiert STATUS.json.

Rose und Wolkivo bleiben getrennte Projekte. Wolkivo verwendet Chromium und
bereits eigene GitHub-Releases. Rose darf dessen Update-Dateien, Schluessel
und Latest-Release-Ziel nicht verwenden.

## Technische Basis

Firefox 158.0 wird aus dem offiziellen Quellarchiv gebaut. SHA-512 und
Download-Adresse stehen in upstream.json. Der Overlay setzt den Produktnamen
und die Menue-Bezeichnungen auf Rose, erzeugt eigene Windows-Icons und baut
rose.exe. Profilverzeichnis, Prozesskennung und Update-Kanal sind eigenstaendig.
Die Firefox-Anwendungs-ID bleibt fuer WebExtension-Kompatibilitaet erhalten.
Mozilla- und Drittlizenzhinweise im Quellcode bleiben erhalten.

Die erste Zielplattform ist Windows x64, Sprache en-US. Deutschsprachige
Releasepakete sind noch nicht vorbereitet.

## Updates

Rose verwendet den nativen Firefox-Updater mit eigenem Kanal `rose-release`
und eingebettetem Rose-Zertifikat. MAR-Pakete werden mit RSA-4096 / SHA-384
signiert; die Pruefung wird nicht abgeschaltet. Fertige Firefox-Updates von
Mozilla sind kein Ersatz fuer Rose-Pakete. Neue Firefox-Staende muessen in
Rose uebernommen, neu gebaut und getestet werden.

Eine eigene Domain ist optional: Ein separates GitHub-Repository kann
`rose-win64-update.xml` und die signierten MARs ueber GitHub Releases anbieten.
Der lokale Node-Dienst dient alternativ als Entwicklungs-Update-Server.
Das separate oeffentliche Repository liegt unter
https://github.com/aheinen1971-cmd/rose. Der Browser ist auf dessen kuenftige
Release-Update-Datei eingestellt. Dort wurde noch kein Browser-Release
veroeffentlicht; der oeffentliche Update-Kanal ist noch nicht betriebsbereit.

Kostenrahmen: ausschliesslich kostenlose GitHub-Funktionen, oeffentliches
Rose-Repository und GitHub Releases. Keine kostenpflichtigen Runner, kein
Git LFS und kein kostenpflichtiger Hosting-Vertrag. Die Builds werden
zunaechst lokal durchgefuehrt.

Der private Update-Schluessel gehoert nicht in dieses Repository oder in ein
Downloadpaket. Auf dem Entwicklungsrechner liegt er verschluesselt ausserhalb
dieses Ordners. `certificates/rose-update.der` ist nur das oeffentliche
Pruefzertifikat. Die eigene Update-Signatur ist keine Windows-Code-Signatur.

## Lokaler Build

Voraussetzungen: MozillaBuild, dessen von `mach bootstrap` verwaltete
Werkzeuge, Python mit requirements.txt und Node ab Version 22. Fuer die
Vorbereitung koennen die Python-Bibliotheken in einer getrennten Umgebung
installiert werden.

1. Offizielles Quellarchiv anhand upstream.json herunterladen, SHA-512 pruefen
   und ausserhalb dieses Projekts entpacken.
2. `python scripts/prepare-source.py QUELLORDNER --local-test` fuer den
   lokalen Update-Test ausfuehren. Fuer eine spaetere GitHub-Veroeffentlichung
   stattdessen `--github-repo BENUTZER/ROSE-REPOSITORY` verwenden.
3. In der MozillaBuild-Shell im Quellordner
   `./mach --no-interactive bootstrap --application-choice browser --no-system-changes`
   ausfuehren. Antivirus-Ausnahmen sind nicht Bestandteil dieser Anleitung.
4. `bash scripts/build-windows.sh QUELLORDNER` vom Rose-Projekt aus starten.
   Ein voller Build ist erforderlich; Artifact-Builds genuegen hier nicht.
5. Das fertige Verzeichnis `obj-rose/dist/rose` mit Install-Rose.ps1 fuer das
   Benutzerkonto installieren. Dieses Installationsskript verarbeitet nur
   einen kompilierten Rose-Build, nicht den frueheren Firefox-Prototyp.

## Release-Pakete

`scripts/package-update.sh` erzeugt ein komplettes MAR, signiert es mit dem
verschluesselten privaten Schluessel und prueft es zusaetzlich mit Mozillas
nativem signmar-Werkzeug. Erst danach schreibt es release.json. Das Passwort
wird interaktiv abgefragt oder aus ROSE_SIGNING_PASSWORD gelesen.

`node scripts/write-github-feed.mjs BENUTZER/REPO RELEASE_TAG RELEASEORDNER`
erzeugt die XML-Datei fuer GitHub Releases. MAR und XML zusammen als Release
veroeffentlichen; niemals eine Wolkivo-Veroeffentlichung dafuer ersetzen.
Vor dem ersten Release muessen zwei echte Rose-Versionen und ein Update
zwischen ihren getrennten Testinstallationen erfolgreich geprueft werden.

## Tests

`npm test` prueft den Update-Dienst. `python tests/test_signing.py` prueft
Signieren, Nutzdaten-Erhalt, Manipulationserkennung und Produkt-/Kanalgrenzen.
Die Signaturtests verwenden synthetische MAR-Dateien. Sie bestaetigen noch
keine erfolgreiche Aktualisierung eines kompilierten Browsers.

Lokaler Dienst: ROSE_LOCAL_TEST=1 setzen, dann `node updates/server.mjs`.
Ohne release.json antwortet der Dienst mit einer leeren Update-Liste.
Oeffentlich benoetigt der Dienst eine vorgeschaltete HTTPS-Verbindung.

## Quellen

- https://firefox-source-docs.mozilla.org/setup/windows_build.html
- https://firefox-source-docs.mozilla.org/toolkit/mozapps/update/docs/MarFiles.html
- https://github.com/mozilla-releng/build-mar
- https://github.com/aheinen1971-cmd/wolkivo
