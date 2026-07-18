# NOWA X DSGVO Compliance

Herstellerneutraler Datenschutz-Skill für KI-Systeme. Entwickelt von **Norman Wagner / WagnerConnect**. Ein Projekt von **nowaXdata – Der digitale Datenschutzordner**.

Der Skill erstellt quellenbasierte Erstprüfungen zu DSGVO (Datenschutz-Grundverordnung), BDSG (Bundesdatenschutzgesetz), TDDDG (Telekommunikation-Digitale-Dienste-Datenschutz-Gesetz) und angrenzenden Regeln. Er erkennt dringende Fristen, verlangt aktuelle amtliche Quellen und verhindert, dass echte Personendaten unnötig in Ausgaben, Dateien oder Beispiele übernommen werden.

## Nutzung mit verschiedenen KI-Systemen

| Umgebung | Empfohlene Nutzung |
| --- | --- |
| ChatGPT Work und Codex | Plugin-Verzeichnis verwenden; die Hülle liegt in `.codex-plugin/plugin.json`. |
| Agent-Skills-kompatible Systeme | Ordner `skills/pruefe-de-datenschutz` als Skill installieren. |
| Claude | Denselben Skill-Ordner als benutzerdefinierten Skill verwenden. |
| Gemini, DeepSeek, Perplexity und andere | `dist/dsgvo-portable-prompt.md` als System- oder Projektanweisung einfügen. |
| Systeme mit kleinem Kontextfenster | `dist/dsgvo-portable-prompt-compact.md` verwenden und die Referenzdateien bei Bedarf ergänzen. |

Nicht jede KI unterstützt eigene Skills, Dateien oder Systemanweisungen. Der portable Prompt deckt diese Lücke ab, soweit das jeweilige System lange Anweisungen zulässt.

## Architektur

```text
nowax-dsgvo-compliance/
├── .codex-plugin/plugin.json
├── .github/workflows/
│   ├── legal-watch.yml
│   ├── release.yml
│   └── validate.yml
├── legal-sources.json
├── legal-source-baseline.json
├── RECHTSSTAND.md
├── skills/pruefe-de-datenschutz/
│   ├── SKILL.md
│   ├── agents/openai.yaml
│   ├── references/
│   └── scripts/check_legal_output.py
├── dist/
│   ├── dsgvo-portable-prompt.md
│   └── dsgvo-portable-prompt-compact.md
├── tests/cases.json
└── scripts/
    ├── build_portable_prompts.py
    ├── legal_watch.py
    └── validate_repo.py
```

- `SKILL.md` enthält nur den stabilen Arbeitsablauf. Das verbessert die automatische Auswahl und hält den geladenen Kontext klein.
- `references/` trennt Fachmodule. Die KI lädt nur das, was der Fall braucht.
- `agents/openai.yaml` und `.codex-plugin/plugin.json` sind optionale OpenAI-Adapter. Die Rechtslogik bleibt davon unabhängig.
- `dist/` macht denselben Kern für KI-Systeme ohne Skill-Unterstützung nutzbar.
- Die Prüfskripte erkennen Strukturfehler und fehlende Quellen. Sie können keine juristische Richtigkeit garantieren.

## Laufende Aktualisierung

Der Workflow `legal-watch.yml` prüft die registrierten amtlichen und behördlichen Quellen wöchentlich sowie auf manuellen Start. Er erkennt Nichterreichbarkeit, fehlende Kennzeichen, geänderte technische Fingerabdrücke und überfällige fachliche Prüfintervalle. Bei Auffälligkeiten erstellt oder ergänzt er ein GitHub-Issue; er ändert niemals automatisch eine Rechtsauslegung.

`legal-sources.json` ist das maschinenlesbare Quellenregister. `legal-source-baseline.json` enthält ausschließlich nach menschlicher Sichtprüfung bestätigte technische Fingerabdrücke. Verantwortlichkeiten, Freigabegrenzen und der Abschlussprozess stehen in [RECHTSSTAND.md](RECHTSSTAND.md).

Vor der ersten öffentlichen Freigabe muss eine verantwortliche Person die technische Baseline bestätigen. Bei neuen Normen, Urteilen, Behördenleitlinien oder Anwendungsfristen ist eine fachkundige datenschutzrechtliche Prüfung vorgesehen. Für reine Link-, Build- und Strukturpflege ist keine juristische Prüfung erforderlich.

Geplante GitHub-Workflows können bei längerer Inaktivität eines öffentlichen Repositorys deaktiviert werden. Der erfolgreiche Lauf ist deshalb monatlich manuell zu kontrollieren.

`release.yml` prüft bei Tags und manuellen Läufen das vollständige Projekt. Bei einem Tag muss beispielsweise `v0.4.1` exakt zur Version `0.4.1` im Plugin-Manifest passen. Der Workflow veröffentlicht bewusst nichts automatisch; eine Veröffentlichung bleibt eine kontrollierte Maintainer-Entscheidung.

## Sicherheitsgrenzen

- Keine echten Personendaten, Zugangsdaten oder Mandatsgeheimnisse in Issues, Beispielen oder Testfällen veröffentlichen.
- Keine Meldung an Behörden, Nachricht an Betroffene oder sonstige externe Handlung ohne menschliche Prüfung und ausdrückliche Freigabe.
- Keine erfundenen Urteile, Aktenzeichen, Fundstellen oder Zitate.
- Keine Behauptung, das Ergebnis sei garantiert rechtssicher.

Der Skill unterstützt Erstprüfung und interne Compliance. Er ersetzt keine verbindliche Einzelfallberatung durch eine dazu befugte Person. Wer ihn als Rechtsdienstleistung anbietet, muss insbesondere das RDG (Rechtsdienstleistungsgesetz) und berufsrechtliche Grenzen eigenständig prüfen.

## Validierung

```bash
python scripts/build_portable_prompts.py --check
python scripts/validate_repo.py
python scripts/legal_watch.py --report /tmp/legal-watch-report.md
python -m unittest discover -s tests -v
python skills/pruefe-de-datenschutz/scripts/check_legal_output.py beispiel.md
```

Rechtsstand des eingebauten Quellenregisters: **18. Juli 2026**. Jede konkrete Prüfung muss die Aktualität erneut feststellen.

## Lizenz und Namensnennung

Der Quelltext steht unter Apache License 2.0. Die Lizenz gewährt keine Rechte an den Namen und Kennzeichen **NOWA X**, **NOWA X Data** oder **WagnerConnect**. Einzelheiten stehen in `LICENSE.txt` und `NOTICE.txt`.
