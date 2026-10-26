'use strict';
const english = !navigator.language.toLowerCase().startsWith('de');
const pick = (de, en) => english ? en : de;
document.documentElement.lang = english ? 'en' : 'de';
const privacy = location.href === 'about:rosavio-privacy';
const title = pick(privacy ? 'Datenschutz im Überblick' : 'Neues in Rosavio', privacy ? 'Privacy at a glance' : 'What’s new in Rosavio');
document.title = title + ' · Rosavio';
document.getElementById('title').textContent = title;
document.getElementById('intro').textContent = privacy
  ? pick('Sieh nach, welcher Schutz gerade aktiv ist und was er bewirkt. Diese Übersicht verändert keine Einstellungen.', 'See which protections are currently enabled and what they do. This overview does not change your settings.')
  : pick('Verständliche Hinweise zu dieser Rosavio-Ausgabe. Versionsnummer und Build stammen aus deinem laufenden Browser.', 'Clear notes about this Rosavio edition. The version and build come from your running browser.');
document.getElementById('privacy-link').textContent = pick('Datenschutz im Überblick', 'Privacy at a glance');
document.getElementById('updates-link').textContent = pick('Neues in Rosavio', 'What’s new in Rosavio');
document.getElementById('local-note').textContent = pick('Diese Seite liest nur eine feste Auswahl von Einstellungen. Sie überträgt keine Daten und lädt keine externen Inhalte. Einstellungen und Ausnahmen verwaltest du in den normalen Browser-Einstellungen.', 'This page reads only a fixed selection of settings. It does not transmit data or load external content. Manage settings and exceptions in the normal browser settings.');
document.getElementById('refresh').textContent = pick('Anzeige aktualisieren', 'Refresh overview');
const content = document.getElementById('content'), status = document.getElementById('status');
status.textContent = pick('Einstellungen werden gelesen …', 'Reading settings …');
const element = (tag, text, cls) => { const node = document.createElement(tag); if (text) node.textContent = text; if (cls) node.className = cls; return node; };
const link = (label, href) => { const a = element('a', label); a.href = href; return a; };
function card(parent, id, heading, value, good, explanation, href) {
  const article = element('article'); article.id = id;
  article.append(element('h3', heading), element('p', value, 'state' + (good === null ? '' : good ? ' good' : ' warn')), element('p', explanation, 'explanation'));
  if (href) article.append(link(pick('Einstellungen öffnen', 'Open settings'), href));
  parent.append(article);
}
const onOff = enabled => pick(enabled ? 'Eingeschaltet' : 'Ausgeschaltet', enabled ? 'Enabled' : 'Disabled');
function render(s) {
  content.replaceChildren();
  const privacyHref = 'about:preferences#privacy';
  const securityHref = s.settingsRedesign ? 'about:preferences#connectionSecurity' : privacyHref;
  if (privacy) {
    const grid = element('div', null, 'cards'); content.append(grid);
    const modes = {strict: pick('Streng', 'Strict'), standard: pick('Standard', 'Standard'), custom: pick('Benutzerdefiniert', 'Custom')};
    const trackingState = s.tracking ? onOff(true) : s.trackingPrivate ? pick('Nur in privaten Fenstern', 'In private windows only') : onOff(false);
    card(grid, 'tracking', pick('Schutz vor Aktivitätenverfolgung', 'Tracking protection'), (modes[s.trackingCategory] || pick('Aktuelle Konfiguration', 'Current configuration')) + ' · ' + trackingState, null,
      pick('Der Modus fasst mehrere Regeln zusammen. Tracker-Listen, Cookie-Regeln und Ausnahmen bestimmen den Schutz jeder Webseite. Strengere Regeln können einzelne Seitenfunktionen stören; ändere bei Bedarf gezielt die Ausnahme dieser Seite.', 'The mode combines several rules. Tracker lists, cookie rules and exceptions determine protection on each site. Stricter rules may affect site features; consider a specific exception when needed.'), privacyHref);
    const cookieRules = [pick('Cookies erlaubt', 'Cookies allowed'), pick('Drittanbieter-Cookies blockiert', 'Third-party cookies blocked'), pick('Alle Cookies blockiert', 'All cookies blocked'), pick('Cookies nicht besuchter Seiten blockiert', 'Cookies from unvisited sites blocked'), pick('Tracker-Cookies blockiert', 'Tracker cookies blocked'), pick('Isolierung pro Webseite', 'Isolated by site')];
    card(grid, 'cookies', pick('Websiteübergreifende Cookies', 'Cross-site cookies'), cookieRules[s.cookies] || pick('In den Einstellungen nachsehen', 'Check the settings'), null,
      pick('Cookies können Anmeldungen und Einstellungen speichern. Die Isolierung begrenzt ihre Nutzung über verschiedene Webseiten hinweg. Sie verhindert nicht jede Form der Wiedererkennung.', 'Cookies can store sign-ins and settings. Isolation limits their use across sites. It does not prevent every form of identification.'), privacyHref);
    const sites = s.malware && s.phishing;
    card(grid, 'sites', pick('Gefährliche und betrügerische Webseiten', 'Deceptive and dangerous sites'), sites ? onOff(true) : pick('Nicht vollständig eingeschaltet', 'Not fully enabled'), sites,
      pick('Warnt vor bekannten schädlichen und betrügerischen Seiten. Die Listen werden über das Internet aktualisiert; je nach Prüfung können Sicherheitsanbieter kontaktiert werden. Ein eingeschalteter Schalter ist kein Beweis, dass jede aktuelle Bedrohung erkannt wird.', 'Warns about known harmful and deceptive sites. Lists are updated over the internet; security providers may be contacted depending on the check. An enabled setting does not prove that every current threat will be detected.'), securityHref);
    const downloads = s.downloads && s.malware;
    card(grid, 'downloads', pick('Downloadschutz', 'Download protection'), onOff(downloads), downloads,
      pick('Prüft verdächtige Downloads. Das ersetzt keine Vorsicht beim Öffnen unbekannter Dateien und keine weiteren Schutzfunktionen deines Betriebssystems.', 'Checks suspicious downloads. This does not replace care when opening unknown files or other operating-system protections.'), securityHref);
    const extra = downloads && s.unwanted && s.uncommon;
    card(grid, 'unwanted', pick('Unerwünschte und ungewöhnliche Software', 'Unwanted and uncommon software'), extra ? onOff(true) : pick('Nicht vollständig eingeschaltet', 'Not fully enabled'), extra,
      pick('Ergänzende Warnungen können auch selten heruntergeladene, harmlose Programme betreffen. Prüfe Herkunft und Warnung, bevor du eine Datei freigibst.', 'Additional warnings can also affect harmless, rarely downloaded programs. Check the source and warning before allowing a file.'), securityHref);
    card(grid, 'telemetry', pick('Technische Nutzungsdaten', 'Technical usage data'), s.telemetry ? pick('Datenübermittlung erlaubt', 'Data submission allowed') : pick('Datenübermittlung ausgeschaltet', 'Data submission disabled'), null,
      pick('Berücksichtigt die Datenfreigabe und ob diese Rosavio-Ausgabe technische Nutzungsdaten übermitteln kann. Andere Netzwerkverbindungen, etwa Webseiten, Updates, Sicherheitslisten und Erweiterungen, haben eigene Regeln.', 'Accounts for data-submission settings and whether this Rosavio build can submit technical usage data. Other connections, including websites, updates, security lists and extensions, follow their own rules.'), privacyHref);
    const note = element('section', null, 'note'); note.append(element('h2', pick('Deine Entscheidungen bleiben bei dir', 'Your choices stay with you')), element('p', pick('Ein privates Fenster löscht nach dem Schließen bestimmte lokale Spuren, macht dich im Internet aber nicht anonym. Erweiterungen können je nach erteilten Berechtigungen auf Webseiten zugreifen. Prüfe deshalb auch ihre Berechtigungen.', 'A private window clears certain local traces after closing, but does not make you anonymous online. Extensions may access sites according to their granted permissions. Review their permissions too.')), link(pick('Erweiterungen verwalten', 'Manage extensions'), 'about:addons')); content.append(note);
  } else {
    const section = element('section', null, 'note');
    section.append(element('h2', pick('Neu in dieser Ausgabe', 'New in this edition')));
    const list = element('ul');
    for (const text of [pick('Datenschutz im Überblick: aktive Schutzoptionen und verständliche Erklärungen an einem Ort.', 'Privacy at a glance: active protections and clear explanations in one place.'), pick('Versionshinweise direkt in Rosavio, ohne eine externe Seite laden zu müssen.', 'Release notes inside Rosavio, without loading an external page.'), pick('Schnelle Wege zu den bestehenden Datenschutz- und Erweiterungseinstellungen.', 'Quick links to the existing privacy and extension settings.')]) list.append(element('li', text));
    section.append(list, element('p', pick('Vorhandene Einstellungen werden durch diese Seiten nicht zurückgesetzt.', 'These pages do not reset your existing settings.'))); content.append(section);
    const update = element('section', null, 'note'); update.append(element('h2', pick('So kommen Updates zu dir', 'How updates reach you')), element('p', s.updateAllowed ? pick('Rosavio prüft über seinen eigenen Update-Kanal auf neue Ausgaben. Im Menü Hilfe → Über Rosavio kannst du die Prüfung öffnen. Verfügbare Versionen und dieser Hinweis können unterschiedlich sein, bis ein neuer Bau geprüft und veröffentlicht ist.', 'Rosavio checks its own update channel for new editions. Open Help → About Rosavio to check. Available releases and these notes may differ until a new build has been tested and published.') : pick('Der eingebaute Updater wird durch eine Richtlinie verwaltet. Bei Flatpak kommen Updates über die Softwareverwaltung oder „flatpak update“. In anderen verwalteten Installationen frage die zuständige Administration.', 'The built-in updater is managed by policy. Flatpak updates arrive through the software manager or “flatpak update”. For other managed installations, ask your administrator.')), element('p', pick('macOS-Ausgaben sind nicht von Apple notarisiert. macOS kann den ersten Start blockieren oder eine persönliche Freigabe verlangen.', 'macOS editions are not notarized by Apple. macOS may block the first launch or require your approval.')), link(pick('Alle veröffentlichten Versionen auf GitHub', 'All published releases on GitHub'), 'https://github.com/aheinen1971-cmd/rosavio/releases')); content.append(update);
  }
  const meta = element('p', pick('Diese Installation: Rosavio ', 'This installation: Rosavio ') + s.version + ' · Build ' + s.buildID, 'meta'); meta.id = 'build'; content.append(meta);
  status.textContent = pick('Aktueller Stand aus diesem Browser. Nach Änderungen kannst du die Anzeige aktualisieren.', 'Current values from this browser. Refresh the overview after changing settings.');
  document.documentElement.dataset.ready = 'true';
}
document.addEventListener('RosavioSummary', event => render(event.detail));
document.addEventListener('RosavioSummaryError', () => {status.textContent = pick('Die Einstellungen konnten nicht gelesen werden. Öffne die normalen Browser-Einstellungen.', 'Settings could not be read. Open the normal browser settings.');content.replaceChildren(link(pick('Browser-Einstellungen öffnen', 'Open browser settings'), 'about:preferences#privacy'));});
function request() {document.dispatchEvent(new CustomEvent('RosavioSummaryRequest'));}
document.getElementById('refresh').addEventListener('click', request);
request();
