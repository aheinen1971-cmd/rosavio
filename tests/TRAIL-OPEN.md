# Rosenpfad-Suchtreffer direkt öffnen

17.11.2026, lokal vorbereitet: Bei aktiver Suche zeigt jeder passende Treffer einen vorhandenen, in allen 20 Sprachen übersetzten „Weiterlesen“-Link. Er öffnet die gespeicherte HTTP-/HTTPS-Adresse einschließlich Lesestellenfragment in einem neuen Tab mit `noopener noreferrer`. Er ändert weder die aktuelle Pfadposition noch Reihenfolge, Texte, Suchanfrage oder ungespeicherte Entwürfe. Nach Leeren der Suche oder bei keinem Treffer sind die Zusatzlinks verborgen.

Isolierte native Windows-Rendererprüfung in allen 20 Sprachen: vorhandene Markierungen, Unicode, HTML-artige Zitate, 30 Stationen, Trefferauswahl, Leeren, Linkziel, Daten-/Speicherisolation und RTL bestanden. Zusätzlich echte Linkklicks mit neuem Tab auf eine lokale Testseite in allen 20 Sprachen bestanden, ohne Zugriff auf persönliche Seiten oder Profile. DE/AR/JA-Bildkontrolle bestanden.

Nachweise: `work/trail-open-qa/results.json`, `real-click-results.json`, `work/check-trail-open-native.cjs`, `work/check-trail-open-click.cjs`. Der native Paketprüfer `check-rose-path.cjs` prüft die Linkeigenschaften bei künftigen Paketläufen mit. Neue Windows-/Linux-/Flatpak-Paketqualifikation und Veröffentlichung sind noch nicht erfolgt. Kein vollständiger Browserneubau.
