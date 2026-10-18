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

