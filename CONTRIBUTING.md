# Beitragen

Beiträge sind willkommen, wenn sie die Quellenqualität, Sicherheit oder Herstellerneutralität des Projekts verbessern.

## Datenschutz vor dem Einreichen

- Nur vollständig erfundene oder zuverlässig anonymisierte Beispiele verwenden.
- Keine Namen realer betroffener Personen, Kontaktdaten, Aktenzeichen mit Personenbezug, Gesundheitsdaten, Zugangsdaten oder vertraulichen Dokumente veröffentlichen.
- Keine produktiven API-Schlüssel, Tokens, Passwörter oder privaten Schlüssel einreichen.
- Verdächtige Inhalte vor dem Commit mit `python scripts/check_repository_privacy.py` prüfen.
- Vertrauliche Sicherheitsmeldungen ausschließlich nach [SECURITY.md](SECURITY.md) übermitteln.

Pseudonymisierte Daten bleiben grundsätzlich personenbezogen. Das Ersetzen eines Namens durch ein Kürzel reicht daher nicht aus, wenn die Person über andere Angaben bestimmbar bleibt.

## Änderungen am Rechtsstand

1. Die amtliche oder behördliche Primärquelle direkt verlinken.
2. Veröffentlichungs-, Inkrafttretens- und gegebenenfalls Anwendungsdatum trennen.
3. Beobachtete Änderung und eigene rechtliche Bewertung getrennt beschreiben.
4. Betroffene Skill-Anweisungen, Referenzen, Testfälle und portable Prompts nennen.
5. Bei einer neuen Norm, Rechtsprechung, Behördenleitlinie, Frist oder materiellen Auslegung eine fachkundige datenschutzrechtliche Prüfung dokumentieren.

`dsgvo-gesetz.de` kann als gut lesbare Arbeitshilfe dienen, ersetzt aber bei tragenden Aussagen nicht EUR-Lex, `gesetze-im-internet.de`, amtliche Rechtsprechung oder eine zuständige Aufsichtsbehörde.

## Technische Änderungen

Vor einem Pull Request ausführen:

```bash
python scripts/check_repository_privacy.py
python scripts/build_portable_prompts.py --check
python scripts/validate_repo.py
python scripts/legal_watch.py --report /tmp/legal-watch-report.md
python -m unittest discover -s tests -v
```

Bei Änderungen am Skill-Kern anschließend die portablen Dateien mit `python scripts/build_portable_prompts.py` neu erzeugen.

## Pull-Request-Umfang

- Einen klaren Zweck pro Pull Request verfolgen.
- Automatisch erzeugte Dateien zusammen mit ihrer Quelle aktualisieren.
- Unsicherheiten und noch fehlende fachliche Freigaben offen nennen.
- Keine Aussage verwenden, die eine Garantie, Zertifizierung oder verbindliche Rechtsberatung vortäuscht.

Mit einem Beitrag wird bestätigt, dass der eingereichte Inhalt unter der Apache License 2.0 veröffentlicht werden darf. Namen und Kennzeichen bleiben nach `NOTICE.txt` ausgenommen.
