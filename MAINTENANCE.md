## Aktueller gepruefter Stand: 20 Sprachen, 23.10.2026

Latest v158.0.1-rosavio.39833487343, BuildID 20261022184458.
Cloudlauf https://github.com/aheinen1971-cmd/rosavio/actions/runs/39833487343 vollstaendig erfolgreich: nativer Bau, alle 20 Sprachen mit Neustart, aktive MAR-Signaturpruefung einschliesslich Manipulations-Negativtest, lokaler und oeffentlicher nativer Update-Test.

Am 23.10. lokal mit separaten Profilen wiederholt: alle 20 aktiven Browseroberflaechen nach Neustart samt lokalisiertem About-Namen; alle 20 Auswahloptionen in about:preferences#languages sichtbar. Deutsch bleibt Standard. Spracheinstellungen verwenden inzwischen diese eigene Kategorie, nicht zwingend Allgemein.

Echte eigene Windows-Testverknuepfung vor und nach oeffentlichem Update gestartet: gleicher Rosavio-Prozesspfad, Rosavio-Identitaet, de, eigene Update-Adresse, Videoeinstellung false erhalten. Direkte Lesezeichen, Unterordner, Titel, URLs, GUIDs und Reihenfolge identisch; Leiste weiterhin always, collapsed=false, hidden=false. Dies belegt den .lnk-Start, nicht die separate Verknuepfungserzeugung durch den Installer. Persoenliches Profil und Wolkivo unveraendert.

Belege im uebergeordneten outputs-Verzeichnis: Rosavio-20-Sprachen-Sprachtest.json, Rosavio-20-Sprachen-Einstellungen-Test.json, Rosavio-20-Sprachen-Desktop-Lesezeichen-Test.json und PNG, Rosavio-20-Sprachen-public-update-test.json, Rosavio-20-Sprachen-Webseiten-Test.json und Rosavio-20-Sprachen-Webseite.png.

Alle 20 oeffentlichen Webseiten HTTP200, je 20 korrekte Sprachlinks und Downloadziel geprueft, RTL fuer ar/he. Verfuegbarkeitstexte aktualisiert; Pages-Lauf 39955250535 success, Commit 3b50a31e0919e3d5383c27a7eebf73c3346ed69a. Generator work/rosavio-extra-website-languages.py erzeugt historische In-Arbeit-Texte; danach work/finalize-twenty-language-website.py anwenden. Alten Fuenfsprachgenerator nicht verwenden.

Gesamtauftrag 20 Sprachen abgeschlossen. Kuenftige Releases weiter mit diesen Sprach-, Signatur-, Update-, Desktop- und Toolbar-Tests pruefen. GitHub taeglich 18:00 Europe/Berlin, Begleitpruefung alle sechs Stunden. Die folgenden Abschnitte sind historische Arbeitsstaende und keine offenen Aufgaben, soweit oben abgeschlossen.

## Zusatztests 158.0.1 bestanden am 21.10.2026

Bericht: ../Rosavio-158.0.1-Desktop-Lesezeichen-Test.json, Screenshot daneben.
Separater Installationsordner und neues Profil unter work/rosavio-desktop-update-check.
Tatsaechliche Windows-.lnk ueber Shell Start-Process gestartet (Testverknuepfung,
nicht Installer-generiert); Ziel vor/nach Update dieselbe rosavio.exe. Oeffentlicher
nativer Update-Pfad vom lokalen 158.0 Build 20261017184503 auf veroeffentlichten
158.0.1 Build 20261020162722, Signaturpruefung aktiv. Identitaet Rosavio, de,
Ueber Rosavio und eigene /rosavio-Update-Adresse nach Neustart bestanden.
Zwei direkte Testlesezeichen, Ordner und Kind identisch erhalten (GUID, Titel,
URL, Eltern, Reihenfolge); visibility always und Toolbar collapsed=false,
hidden=false. Persoenliches Profil nicht verwendet oder veraendert.
Teststeuerung muss remote.prefs.recommended=false setzen; sonst versteckt sie
selbst die Leiste. Erste zwei Versuche wegen dieser Testbeeinflussung verworfen.
Aktueller Teststart ueber .lnk bestanden; automatische Installer-Erzeugung der
Desktop-Verknuepfung wurde damit nicht separat getestet. Nutzer entsprechend
nur Start ueber Desktop-Verknuepfung und Toolbar-Erhalt bestaetigen.
## 158.0.1 Cloud-Erfolg bestaetigt am 21.10.2026

Reparaturlauf 39456937708 vollstaendig success. Veroeffentlichtes Latest:
v158.0.1-rosavio.39456937708, BuildID 20261020162722, 20.10.2026 19:08 UTC.
Lokaler und oeffentlicher nativer Update-Bericht heruntergeladen nach
outputs/Rosavio-158.0.1-local-update-test.json und public-update-test.json
(im uebergeordneten Arbeitsverzeichnis). Beide passed=true, de, Signatur-
Pruefung aktiv, Neustart auf 158.0.1 und Videoeinstellung false erhalten.
Nachfolgender Lauf 39457339727 ebenfalls success. Release-Tag-Reparatur
somit im Cloud-Lauf bestanden. Taeglicher 18-Uhr-Europe/Berlin-Zeitplan aktiv.
WICHTIG: Desktop-Verknuepfungsstart und Lesezeichenleisten-Erhalt nach Update
sind in diesen Berichten NICHT abgedeckt und weiterhin ausstehend. Diese
in separater Testinstallation mit eigenem Profil nachholen, kein persoenliches
Profil verwenden. Noch keine vollstaendige Erfolgsmeldung fuer diese beiden
Zusatzpruefungen geben.
## Reparaturversuch Release-Veröffentlichung am 20.10.2026

Lauf 39429431662: nativer 158.0.1-Bau, Signierung und lokaler Update-Test
bestanden, Release-Anlage mit HTTP403 Resource not accessible by integration
fehlgeschlagen. Vorheriges Latest 158.0 blieb aktiv. Waehrend des Baus wurde
der main-Workflow fuer 18 Uhr geaendert; GITHUB_SHA war bei Release-Anlage
nicht mehr der Branch-HEAD. Korrektur: Release-Tag vor dem langen Bau auf
exakten GITHUB_SHA reservieren, vorhandenen Tag auf identische SHA pruefen;
cloud-publish verwendet --verify-tag statt spaeter neuer Tag-Anlage.
Korrektur erst nach neuem Cloud-Probelauf bestaetigen. Acht Node-Tests lokal
bestanden, PowerShell-Publish-Syntax ohne Fehler. Desktop-Start und Bookmark-
Erhalt-Test bleiben zusaetzliche Pflicht und noch nicht bestaetigt.
## Aktueller GitHub-Zeitplan ab 20.10.2026

Auf Nutzerwunsch prueft rosavio-build.yml jetzt taeglich gegen 18:00 Uhr
Europe/Berlin (cron 0 18 * * *, timezone Europe/Berlin). Sommer-/Winterzeit
wird von GitHub beruecksichtigt; Starts koennen sich verzoegern. Nur wenn eine
neue stabile Firefox-Version vorliegt, beginnt der Bau. Fertigstellung und
Installation sind nicht auf 18 Uhr festgelegt. Bereits laufenden Bau nicht
abbrechen. Begleitpruefung weiterhin alle sechs Stunden. Dieser Abschnitt
ersetzt die historischen Hinweise auf den sechs-stuendlichen GitHub-Bauplan.
## Desktop-Start bei kuenftigen Updates pruefen (18.10.2026)

Nutzer meldete Firefox beim Start ueber Desktop. Gefunden wurde eine Datei
Desktop/Rosavio.exe mit OriginalFilename desktop-launcher.exe und internen
Mozilla-Download-/FirefoxDesktopLauncher-Verweisen. Herkunft nicht bewiesen;
nicht als nachgewiesenen Fehler des Rosavio-Updaters darstellen. Datei wurde
unter work/rosavio-desktop-launcher-backup gesichert. Rosavio.lnk zeigt direkt
auf C:/Program Files/Rosavio/rosavio.exe. Installierte native Identitaet, de,
Menues und Update-Adresse getestet; Nutzer bestaetigte danach korrekten Start.

Bei naechsten Updates zusaetzlich in isolierter Windows-Testinstallation die
Desktop-Verknuepfung vor und nach Update und Neustart tatsaechlich starten.
Prozesspfad und native Identitaet Rosavio, deutsche Menues, eigene Update-URL
nachweisen. Keine als Rosavio benannte Firefox-Launcher-Datei darf entstehen,
kein Firefox-Prozess durch den Rosavio-Desktop-Start. Ergebnis dokumentieren;
fehlenden Desktop-Test ausdruecklich als ausstehend markieren und nachholen.
Persoenliches Profil und dessen Videoeinstellung unveraendert lassen.
# Automatische Firefox-Uebernahme

## Vollstaendiger Cloud-Erfolg am 18.10.2026

Massgeblicher erfolgreicher Lauf: https://github.com/aheinen1971-cmd/rosavio/actions/runs/39081253629
Abgeschlossen um 04:34 Uhr Europe/Berlin. Vollstaendiger nativer Windows-Bau,
deutscher Starttest, Signierung mit aktiver MAR-Pruefung, Manipulations-Negativtest,
lokaler und oeffentlicher nativer Update-Test einschliesslich Neustart bestanden.
Oeffentlicher Test von Build 20261017184503 zu 20261018000553, Sprache de,
media.hardware-video-decoding.enabled=false erhalten. Alter /rose-Client hat
ueber Weiterleitung auf GitHub aktualisiert; neuer Browser verwendet /rosavio.

Release: https://github.com/aheinen1971-cmd/rosavio/releases/tag/v158.0-rosavio.39081253629
Lokale Belege: outputs/Rosavio-Cloud-local-update-test.json und
outputs/Rosavio-Cloud-public-update-test.json im uebergeordneten Arbeitsverzeichnis.
Die Begleit-Automation wurde auf sechs Stunden umgestellt. Der GitHub-Workflow
bleibt ebenfalls alle sechs Stunden aktiv. Erfolg einmalig gemeldet; kuenftig
nur neue fertige Updates, Fehler oder erforderliche Nutzerhilfe melden.
Die folgenden Abschnitte dokumentieren den bisherigen Aufbau und Fehlersuche.

## GitHub-Umstellung

GitHub Actions hat am 17.10.2026 den kostenlosen Windows-Runner erfolgreich
geprueft: 4 CPUs, 16 GB RAM, C: 82,9 GB und D: 147 GB frei. Die verschluesselten
Repository-Secrets ROSAVIO_UPDATE_KEY und ROSAVIO_SIGNING_PASSWORD wurden mit
ausdruecklicher Nutzerzustimmung eingerichtet. Werte niemals ausgeben.

Der Workflow `.github/workflows/rosavio-build.yml` auf dem oeffentlichen
Repository aheinen1971-cmd/rosavio prueft alle sechs Stunden und baut lokal
auf einem GitHub-Standard-Runner. Der erste volle Integrationslauf ist
https://github.com/aheinen1971-cmd/rosavio/actions/runs/39064202133.
Er ist noch NICHT als erfolgreich bestaetigt. Erst bei erfolgreichem Build,
Signierung und nativem oeffentlichem Update-Test Vollautomatik bestaetigen.

Ab jetzt zuerst die GitHub-Workflows pruefen und reparieren; KEINEN parallelen
lokalen Build starten. Fuer kleine Reparaturen Browser-Upload auf GitHub
verwenden, keine Zugangsdaten auslesen. Kostenlosen Standard-Runner beibehalten.
Die folgenden lokalen Schritte bleiben als dokumentierter Rueckfallweg.

Eine geplante Codex-Aufgabe in diesem Chat prueft alle sechs Stunden die stabile
Firefox-Version mit `node scripts/check-firefox-release.mjs`. PC und Codex muessen
laufen. Die Ausfuehrungen nutzen die verfuegbaren Codex-Kontingente. Es werden
keine kostenpflichtigen GitHub-Dienste oder API-Schluessel eingerichtet.

Bei unveraendertem Stand keine Meldung. Bei einem neuen stabilen Release diesen
Ablauf ausfuehren und bei langen Builds in folgenden Ausfuehrungen fortsetzen:

1. Verifizierten letzten Rosavio-Release und lokale Projektdateien sichern.
   Nicht das persoenliche Browserprofil oder laufende Rosavio-Prozesse veraendern.
   Pro Version nur ein Build; Fortschritt unter work/rosavio-maintenance speichern.
2. Offizielles Mozilla-Quellarchiv und veroeffentlichte Pruefsummen herunterladen.
   SHA-512 pruefen; bei fehlender oder falscher Pruefsumme abbrechen. Keine Beta,
   ESR-Umstellung oder fremden Binaerpakete als Ersatz verwenden. Neuen Quellbaum
   unter einem kurzen eigenen Pfad C:/Users/armin/Documents/Codex/work anlegen.
3. Neue AGENTS.md beachten, Overlay gegen die neue Firefox-Version pruefen und
   noetige Anpassungen vornehmen. Erst dann upstreamVersion/upstream.json erhoehen.
   prepare-source.py --github-repo aheinen1971-cmd/rosavio verwenden. Deutsche
   Uebersetzung exakt nach browser/locales/l10n-changesets.json pinnen und
   prepare-german.py ausfuehren. Eigene Namen, Icons, Zertifikate und Kanaele behalten.
4. Vollstaendig lokal mit MozillaBuild bauen. work/run-rose-build.ps1 ist das
   funktionierende Umgebungsbeispiel; neuen Quellpfad und eindeutige UTC-Build-ID
   verwenden. Kein paralleler zweiter Build im selben Objektordner. Sprache de,
   Windows x64, Rosavio-Menues und native Update-Adresse kontrollieren. Die neue
   Adresse ist https://github.com/aheinen1971-cmd/rosavio/releases/latest/download/rosavio-win64-update.xml.
5. Native Startpruefung, HTTPS und Menues mit scripts/check-native.cjs pruefen;
   dessen festes altes Repository-Ziel zuerst passend auf rosavio aktualisieren.
   Anwendung und application.ini muessen dieselbe Version und Build-ID haben.
   Node- und Signaturtests ausfuehren. Dann deutsche EXE, ZIP und signiertes MAR
   erstellen. work/sign-rosavio.ps1 zeigt die sichere DPAPI-Schluesselnutzung.
   Private Schluessel bleiben lokal und werden nie ausgegeben oder hochgeladen.
6. Nativen Update-Test von einer Kopie des letzten veroeffentlichten Browsers zur
   neuen Version auf einem lokalen Testserver ausfuehren. work/rosavio-update-test.cjs
   und rosavio-session.cjs als Vorlage verwenden, Parameter fuer Version/Build-ID,
   Locale und neue URL anpassen. Signaturpruefung stets aktiv lassen; Download,
   Installation und Neustart bestaetigen. Negativtest mit manipuliertem MAR.
7. Erst bei allen bestandenen Tests ein neues Release auf dem kostenlosen
   oeffentlichen Repository aheinen1971-cmd/rosavio veroeffentlichen. Freigabe
   dafuer liegt durch die Nutzeranfrage vor. Feed auf dessen signiertes MAR mit
   richtigem SHA-512 und Byteumfang setzen. Keine privaten Dateien hochladen.
   Bei fehlender GitHub-Anmeldung nur fertigen Stand sichern und Nutzer informieren.
8. Oeffentlichen nativen Update-Test aus einer getrennten Kopie des vorherigen
   Releases ohne lokale URL-Richtlinie ausfuehren; auch alte /rose-Weiterleitung
   fuer installierte Clients testen. Berichte mit Datum in outputs speichern.
   Falls der oeffentliche Test scheitert, vorherigen funktionierenden Latest-Release
   wiederherstellen und Problem melden. Erfolg erst nach bestandenem Test melden.
9. Lokale Metadaten und veroeffentlichtes Quellprojekt nachziehen. Die persoenliche
   Einstellung media.hardware-video-decoding.enabled=false bleibt erhalten.
   Wolkivo bleibt vollstaendig unveraendert. Alte /rose-Adresse nicht neu belegen,
   weil bestehende Rosavio-Installationen deren Weiterleitung benoetigen.

Die Aufgabe bleibt fuer kuenftige Versionen aktiv. Bei unveraendertem Zustand
still bleiben, bei Fehlern oder erforderlicher Nutzerhilfe kurz auf Deutsch melden.

## Stand 17.10.2026, 23 Uhr

Ersten Lauf nach ueber einer Stunde ohne sichtbare Detailausgabe abgebrochen.
Ursache noch nicht bestaetigt. Downloads verwenden jetzt curl mit Verbindungs-
und Gesamtzeitlimit; Installer hat 10-Minuten-Limit. Explizite Phasenmeldungen
zeigen den Fortschritt. Neuer Lauf: https://github.com/aheinen1971-cmd/rosavio/actions/runs/39068999786
Dieser ersetzt den abgebrochenen ersten Probelauf und ist noch nicht bestanden.


## Stand 18.10.2026, kurz nach Mitternacht

Zweiter Lauf 39068999786: Quelle in vier Sekunden vollstaendig geladen,
anschliessend ueber eine Stunde in Windows-tar-Entpackung ohne Fortschritt.
Abgebrochen und Entpackung auf zwei getrennte 7-Zip-Schritte umgestellt
(XZ -> TAR -> Dateien), jeweils 15-Minuten-Limit. Neuer aktiver Probelauf:
https://github.com/aheinen1971-cmd/rosavio/actions/runs/39073441891
Bau und Update-Test weiterhin NICHT bestaetigt.


Zusaetzlich wurde der PowerShell-Aufruf der Node-Tests korrigiert: das komplette
Glob-Muster muss ein einziges Argument sein. Acht Node-Tests und zwei Python-
Signaturtests lokal bestanden. Lauf 39073441891 deshalb nach kurzer Zeit gestoppt.
Massgeblicher neuer Gesamttest: https://github.com/aheinen1971-cmd/rosavio/actions/runs/39073564567


## Stand 18.10.2026: Compiler-Einrichtung

Lauf 39073564567 ist nach 4m35s fehlgeschlagen. 7-Zip-Entpackung und deutsche
Vorbereitung bestanden. Konfiguration scheitert mit Cannot find the target C
compiler / clang-cl. Bootstrap lieferte ohne Toolchain-Ausgabe Erfolg, reicht
also nicht. Jetzt explizit --enable-bootstrap in mozconfig, rustup stable
aktualisieren und RUSTC/CARGO als absolute Pfade setzen; separate configure-Phase
vor dem Build. Keine Signaturpruefung geaendert. Neuer Test:
https://github.com/aheinen1971-cmd/rosavio/actions/runs/39077566832


## Stand 18.10.2026: Toolchain-Dateisuche

Lauf 39077566832 nach 5m32s fehlgeschlagen. Explizites Bootstrap findet wegen
leerem Git-Index keine Taskcluster-Ressourcen: fetch-onnxruntime-deps.sh did not
match anything. Datei ist physisch vorhanden; hash_paths verwendet jedoch
get_tracked_files_finder. Jetzt git add --all und echter Quellarchiv-Commit
statt leerem Commit, bevor Mozillas Toolchain-Pruefung laeuft. Signaturtests
noch nicht erreicht. Neuer Probelauf:
https://github.com/aheinen1971-cmd/rosavio/actions/runs/39081253629


## Stand 18.10.2026: nativer Cloud-Bau laeuft

Lauf 39081253629 weiterhin aktiv. Compiler-/Taskcluster-Vorbereitung jetzt
erfolgreich; tatsaechliche C++-Kompilation im Protokoll (dom/clients/manager).
Rust release profile bereits fertig nach 34m29s, gkrust.lib erzeugt. Kein
Build-Fehler beobachtet. NICHT neu starten: erstmals echter nativer Bau mit
laufendem Fortschritt. Signierung und Update-Tests stehen noch aus.


Pruefung 18.10.2026, etwa 04 Uhr: Lauf 39081253629 weiter ohne Build-Fehler.
Native Kompilation bei 98:53 xpcom/base; vorher toolkit/xre und widget/windows.
Fortschritt vorhanden, nicht abbrechen. Signierung/Update-Test noch ausstehend.



## Lesezeichenleiste nach Updates pruefen (20.10.2026)

Beim naechsten und kuenftigen Updates im isolierten Testprofil direkte
Lesezeichen und Unterordner in der Leiste vorsehen, Sichtbarkeit always.
Vorher/nachher URLs, Titel, Reihenfolge, Ordnerstruktur, Toolbar-Zuordnung
und sichtbare Leiste nach Neustart vergleichen. Zusammen mit Desktop-Start
berichten; fehlende Pruefung als ausstehend kennzeichnen. Persoenliches
Profil nicht fuer Update-Tests verwenden. Der Nutzer hat seine importierten
Firefox-Lesezeichen direkt in die Leiste verschieben lassen; nicht erneut
in Import-Zwischenordner einsortieren.



Neuer Probelauf: https://github.com/aheinen1971-cmd/rosavio/actions/runs/39456937708; weiterhin nicht als vollstaendig bestanden bestaetigt.




## Mehrsprachigkeit in Arbeit (21.10.2026)
Nutzer bestellt de plus en-US/fr/es-ES/nl im Browser und Webseite. scripts/prepare-multilocale.py, check-locales.cjs und cloud-build.ps1 auf GitHub hochgeladen. Native package-multi-locale mit pro Sprache gepinnten Mozilla-Revisionen, angepassten Rosavio-Texten, Standard de. Hauptpaket dist/rosavio; mach build installer. Vor Signierung jede native Sprache mit Neustart pruefen. Noch nicht bestanden. Website docs/index.html plus en/fr/es/nl.html mit Sprachlinks hochgeladen, lokale Seiten geprueft. Browser-Neubau force=true ausgeloest; keine parallelen lokalen Builds. Website nennt Browsersprachen bewusst noch in Arbeit; nach Erfolg Texte aktualisieren. Native Desktop-/Toolbar-Pruefung beim neuen Paket wiederholen. Aktuelle Generator-Datei work/generate-rosavio-languages.py. Neue Quellskripte lokal/remote vorhanden.


## Mehrsprachen-Baureparatur 22.10.2026
Lauf 39670114028: nativer Build und package-multi-locale erfolgreich, Installer bereits erzeugt; anschliessender redundanter mach build installer scheitert: No rule to make target installer. Redundanten Aufruf entfernt. Alle acht Node-Tests und PowerShell-Syntax bestanden. Neue Sprachen noch nicht nativ bestaetigt, bisheriges Latest unveraendert. Website alle fuenf Sprachseiten HTTP200.


## Mehrsprachiger Cloud-Bau erfolgreich 22.10.2026
Lauf 39793448818 vollstaendig success. Latest v158.0.1-rosavio.39793448818, BuildID 20261022141454. Native Fuenfsprachpruefung vor Signierung, MAR-Signaturpruefung und lokaler/oeffentlicher Update-Neustart bestanden. Separater lokaler Desktop-.lnk/Toolbar-Test mit oeffentlichem Update auf genau diesen Build passed=true: outputs/Rosavio-Mehrsprachig-Desktop-Lesezeichen-Test.json. Keine Profilveraenderung beim Nutzer. Lokale Wiederholung check-locales.cjs laeuft noch; Bericht nach Abschluss kopieren. Website in allen fuenf Sprachen erreichbar; Beschreibung von in Arbeit auf verfuegbar aktualisiert. Generierte Zusatztexte bleiben kompakt. Installer-Verknuepfungserzeugung wurde nicht separat geprueft, aber echte .lnk-Starts vor/nach Update.


Lokale Wiederholung aller fuenf nativen Sprachen jetzt bestanden: outputs/Rosavio-Mehrsprachig-Sprachtest.json. Gesamtauftrag Browser-Sprachen plus Website-Sprachen und Desktop-/Toolbar-Erhalt geprueft; keine Installer-Verknuepfungserzeugung behaupten.


## Erweiterung auf zwanzig Sprachen beauftragt 22.10.2026
Nutzer bestellt zusaetzlich it, pt-PT, pl, cs, da, sv-SE, nb-NO, fi, tr, uk, el, ja, ko, ar, he; zusammen mit de/en-US/fr/es-ES/nl 20. Portugiesisch Portugal und Norwegisch Bokmaal als Standardannahme mitgeteilt. Skripte prepare-multilocale/check-locales/cloud-build erweitert und auf GitHub gespeichert. Acht Node-Tests und PS/JS-Syntax bestanden. Native Pruefung neuer Sprachen verlangt Rosavio-Identitaet, aktive Locale, Rosavio im lokalisierten About-Label und keinen englischen About-Text. Website 15 zusaetzliche kompakte Sprachseiten mit lokalen Einfuehrungs-/Update-/Installations-/Lizenztexten; ar/he dir=rtl; 20 Sprachlinks in Details-Auswahl. Lokal alle neuen Seiten/Schreibrichtung/Linkanzahl geprueft, Screenshots ar/he kontrolliert; Browserbau und Update/Desktop/Toolbar-Erhalt noch ausstehend. Website-Generator work/rosavio-extra-website-languages.py und translations JSON. Bestehenden Fuenfsprachgenerator nicht erneut ausfuehren, da er erweiterte Sprachlinks ueberschreibt. Neue Website-Texte nennen zusaetzliche Browser-Sprachen noch als in Arbeit.


Neuer 20-Sprachen-Cloudlauf: https://github.com/aheinen1971-cmd/rosavio/actions/runs/39833487343 (noch nicht bestanden). Alle neuen Website-Dateien hochgeladen; Pages-Auslieferung noch nachpruefen.

