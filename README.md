## Aktuelle Version

Rosavio 158.0.1 steht mit 20 integrierten Oberflaechensprachen bereit; Deutsch bleibt die Voreinstellung. Der vollstaendige Cloudlauf [39833487343](https://github.com/aheinen1971-cmd/rosavio/actions/runs/39833487343) und die zusaetzlichen isolierten Tests vom 23.10.2026 haben bestanden: Sprachauswahl, aktive Sprache nach Neustart, signiertes oeffentliches Autoupdate, Start ueber eine echte Windows-Testverknuepfung und Erhalt der sichtbaren Lesezeichenleiste mit Unterordnern und Reihenfolge.

[Webseite und Sprachwahl](https://aheinen1971-cmd.github.io/rosavio/) · [Aktueller Download](https://github.com/aheinen1971-cmd/rosavio/releases/latest)

GitHub prueft taeglich gegen 18:00 Uhr Europe/Berlin neue stabile Firefox-Versionen. Bau und Veroeffentlichung laufen auf kostenlosen Standard-Runnern unabhaengig vom eigenen PC. Details und Testgrenzen stehen am Anfang von MAINTENANCE.md; die aelteren Angaben darunter dokumentieren die Entwicklung.

# Rosavio Browser
## Automatischer GitHub-Bau

Der vollstaendige kostenlose Windows-Cloud-Bau hat am 18.10.2026 bestanden:
https://github.com/aheinen1971-cmd/rosavio/actions/runs/39081253629.
Die deutsche Version wurde signiert, lokal und anschliessend ueber das
veroeffentlichte native Autoupdate installiert und neu gestartet. Die
Signaturpruefung blieb aktiv und die Videoeinstellung blieb erhalten.
Der aktuelle gepruefte Cloud-Release ist v158.0-rosavio.39081253629,
Build-ID 20261018000553. Die folgenden lokalen Build-IDs dokumentieren
zusaetzlich die vorherigen Tests.

GitHub prueft alle sechs Stunden neue stabile Firefox-Versionen und baut
neue Versionen auf kostenlosen Standard-Runnern. Das funktioniert auch,
wenn der eigene PC ausgeschaltet ist. Die Installation auf dem eigenen PC
kann erst erfolgen, sobald er wieder eingeschaltet ist und Rosavio Updates
pruefen kann. Bei Fehlern wird keine ungepruefte Version freigegeben;
nach fehlgeschlagenem oeffentlichem Update-Test wird das vorherige Latest
wiederhergestellt. Details: MAINTENANCE.md und .github/workflows/rosavio-build.yml.

Eigenstaendiger Windows-Browser auf Firefox-Basis mit deutscher Oberflaeche.
Dieses Verzeichnis enthaelt die Quellcode-Anpassungen und den Update-Dienst.
Fertige Windows-Pakete gibt es unter
https://github.com/aheinen1971-cmd/rosavio/releases/latest.
Den geprueften Stand dokumentiert STATUS.json.

Rosavio und Wolkivo bleiben getrennte Projekte. Wolkivo verwendet Chromium und
bereits eigene GitHub-Releases. Rosavio darf dessen Update-Dateien, Schluessel
und Latest-Release-Ziel nicht verwenden.

## Technische Basis

Firefox 158.0 wird aus dem offiziellen Quellarchiv gebaut. SHA-512 und
Download-Adresse stehen in upstream.json. Der Overlay setzt den Produktnamen
und die Menue-Bezeichnungen auf Rosavio, erzeugt eigene Windows-Icons und baut
rosavio.exe. Profilverzeichnis, Prozesskennung und Update-Kanal sind eigenstaendig.
Die Firefox-Anwendungs-ID bleibt fuer WebExtension-Kompatibilitaet erhalten.
Mozilla- und Drittlizenzhinweise im Quellcode bleiben erhalten.

Zielplattform ist Windows x64. Fuer Deutsch wird die zum Firefox-Quellarchiv
passende Uebersetzung verwendet; Repository und Revision stehen in
localization.json. Das deutsche Paket wird direkt lokalisiert und benoetigt
kein nachtraeglich installiertes Sprachpaket.

## Updates

Rosavio verwendet den nativen Firefox-Updater mit eigenem Kanal `rosavio-release`
und eingebettetem Rosavio-Zertifikat. MAR-Pakete werden mit RSA-4096 / SHA-384
signiert; die Pruefung wird nicht abgeschaltet. Fertige Firefox-Updates von
Mozilla sind kein Ersatz fuer Rosavio-Pakete. Neue Firefox-Staende muessen in
Rosavio uebernommen, neu gebaut und getestet werden.

Seit dieser Firefox-Basis liest der Updater die native `AppUpdate`-URL aus den
kompilierten Anwendungsdaten. prepare-source.py setzt deshalb auch die URL in
`build/application.ini.in`; eine alleinige app.update.url-Voreinstellung reicht
nicht. `node scripts/check-native.cjs PFAD_ZUR_EXE PRUEFORDNER` prueft die vom
nativen Update-Checker verwendete Adresse, Produktnamen, Menues und HTTPS.
Mit `ROSAVIO_EXPECT_LOCALE=de` werden zusaetzlich die deutschen Menues geprueft.

Eine eigene Domain ist optional: Ein separates GitHub-Repository kann
`rosavio-win64-update.xml` und die signierten MARs ueber GitHub Releases anbieten.
Der lokale Node-Dienst dient alternativ als Entwicklungs-Update-Server.
Das separate oeffentliche Repository liegt unter
https://github.com/aheinen1971-cmd/rosavio. Der Browser verwendet die dortige
Release-Update-Datei `releases/latest/download/rosavio-win64-update.xml`.
Ein nativer Integrationstest hat den Wechsel von der englischen Build-ID
20261017161130 zur deutschen Build-ID 20261017175200 mit aktivierter
MAR-Signaturpruefung erfolgreich durchgefuehrt.
Auch der oeffentliche Update-Test ohne lokale URL-Richtlinie hat bestanden:
Der native Updater hat Build 20261017184503 ueber GitHub heruntergeladen,
mit aktivierter Signaturpruefung angewendet und nach dem Neustart Deutsch
und die eigene native GitHub-Update-Adresse bestaetigt. Die Veroeffentlichung
traegt den Tag `v158.0-rosavio.3`.

Kostenrahmen: ausschliesslich kostenlose GitHub-Funktionen, oeffentliches
Rosavio-Repository und GitHub Releases. Keine kostenpflichtigen Runner, kein
Git LFS und kein kostenpflichtiger Hosting-Vertrag. Die Builds werden
zunaechst lokal durchgefuehrt.

Der private Update-Schluessel gehoert nicht in dieses Repository oder in ein
Downloadpaket. Auf dem Entwicklungsrechner liegt er verschluesselt ausserhalb
dieses Ordners. `certificates/rosavio-update.der` ist nur das oeffentliche
Pruefzertifikat. Die eigene Update-Signatur ist keine Windows-Code-Signatur.

## Lokaler Build

Voraussetzungen: MozillaBuild, dessen von `mach bootstrap` verwaltete
Werkzeuge, Python mit requirements.txt und Node ab Version 22. Fuer die
Vorbereitung koennen die Python-Bibliotheken in einer getrennten Umgebung
installiert werden.

1. Offizielles Quellarchiv anhand upstream.json herunterladen, SHA-512 pruefen
   und ausserhalb dieses Projekts entpacken. Unter Windows darf der volle
   Quellcode-Pfad hoechstens 62 Zeichen lang sein.
2. `python scripts/prepare-source.py QUELLORDNER --local-test` fuer den
   lokalen Update-Test ausfuehren. Fuer eine spaetere GitHub-Veroeffentlichung
   stattdessen `--github-repo BENUTZER/ROSAVIO-REPOSITORY` verwenden.
3. In der MozillaBuild-Shell im Quellordner
   `./mach --no-interactive bootstrap --application-choice browser --no-system-changes`
   ausfuehren. Bei dieser Variante muss Rust separat eingerichtet und fuer
   den Build erreichbar sein. Antivirus-Ausnahmen sind nicht Bestandteil
   dieser Anleitung.
4. `bash scripts/build-windows.sh QUELLORDNER` vom Rosavio-Projekt aus starten.
   Ein voller Build ist erforderlich; Artifact-Builds genuegen hier nicht.
5. Das fertige Verzeichnis `obj-rose/dist/rosavio` mit Install-Rosavio.ps1 fuer das
   Benutzerkonto installieren. Dieses Installationsskript verarbeitet nur
   einen kompilierten Rosavio-Build, nicht den frueheren Firefox-Prototyp.

## Release-Pakete

Fuer ein deutsches Paket das Repository aus localization.json mit Git klonen,
die dort genannte Revision auschecken und
`python scripts/prepare-german.py QUELLORDNER UEBERSETZUNGSORDNER` ausfuehren.
Anschliessend `bash scripts/build-windows.sh QUELLORDNER --german` ausfuehren.
Die deutsche Anwendung liegt unter `obj-rose/dist/l10n-stage/rosavio`.
Fuer deren Update-Paket `ROSAVIO_LOCALE=de` und `ROSAVIO_PACKAGE_DIR` auf diesen
absoluten Anwendungspfad setzen. Beide Variablen werden von package-update.sh
verarbeitet. `ROSAVIO_PYTHON` und `ROSAVIO_NODE` koennen explizite Werkzeugpfade
festlegen. Bei einem Quellarchiv ohne Versionsverwaltung benoetigt der
Mozilla-Repacker lokale Git-Metadaten: Nach dem nativen Build `git init`,
einen leeren lokalen Commit und `./mach configure` ausfuehren, bevor
`./mach build installers-de` gestartet wird. Das Quellarchiv bleibt dabei
weiterhin die in upstream.json dokumentierte und gepruefte Basis.

`scripts/package-update.sh` erzeugt ein komplettes MAR, signiert es mit dem
verschluesselten privaten Schluessel und prueft es zusaetzlich mit Mozillas
nativem signmar-Werkzeug. Erst danach schreibt es release.json. Das Passwort
wird interaktiv abgefragt oder aus ROSAVIO_SIGNING_PASSWORD gelesen.

`node scripts/write-github-feed.mjs BENUTZER/REPO RELEASE_TAG RELEASEORDNER`
erzeugt die XML-Datei fuer GitHub Releases. MAR und XML zusammen als Release
veroeffentlichen; niemals eine Wolkivo-Veroeffentlichung dafuer ersetzen.
Das Release muss fuer GitHubs `releases/latest`-Adresse veroeffentlicht sein;
Drafts und reine Prereleases werden dort nicht automatisch angeboten.
Vor dem ersten Release muessen zwei echte Rosavio-Versionen und ein Update
zwischen ihren getrennten Testinstallationen erfolgreich geprueft werden.

## Tests

`npm test` prueft den Update-Dienst. `python tests/test_signing.py` prueft
Signieren, Nutzdaten-Erhalt, Manipulationserkennung und Produkt-/Kanalgrenzen.
Die Signaturtests verwenden synthetische MAR-Dateien. Sie bestaetigen noch
keine erfolgreiche Aktualisierung eines kompilierten Browsers.

Lokaler Dienst: ROSAVIO_LOCAL_TEST=1 setzen, dann `node updates/server.mjs`.
Ohne release.json antwortet der Dienst mit einer leeren Update-Liste.
Oeffentlich benoetigt der Dienst eine vorgeschaltete HTTPS-Verbindung.

## Quellen

- https://firefox-source-docs.mozilla.org/setup/windows_build.html
- https://firefox-source-docs.mozilla.org/toolkit/mozapps/update/docs/MarFiles.html
- https://github.com/mozilla-releng/build-mar
- https://github.com/aheinen1971-cmd/wolkivo
