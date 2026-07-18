# Rechtsstand und Freigabeprozess

## Aktueller Stand

- Redaktionell geprüfter Ausgangsstand: **18. Juli 2026**
- Automatische Quellenüberwachung: wöchentlich und manuell auslösbar
- Technische Baseline: vor der ersten öffentlichen Freigabe noch durch eine verantwortliche Person zu bestätigen
- Verantwortlich für Projektfreigaben: **Norman Wagner / WagnerConnect**

Der Eintrag bestätigt die dokumentierte Prüfung des Projekts zu diesem Stichtag. Er ist keine Garantie, dass sich Recht, Rechtsprechung oder Behördenpraxis danach nicht geändert haben.

## Rollen

| Änderung | Mindestprüfung |
| --- | --- |
| Defekter Link, technische Metadaten, Prompt-Neubau | technische Prüfung |
| Neue Dokumentfassung ohne erkennbare inhaltliche Auswirkung | dokumentierte redaktionelle Prüfung im Vier-Augen-Prinzip empfohlen |
| Neue Norm, Rechtsprechung, Behördenleitlinie oder Anwendungsfrist | fachkundige datenschutzrechtliche Prüfung |
| Neue Bewertung eines konkreten fremden Einzelfalls | Prüfung der Befugnis nach dem Rechtsdienstleistungsgesetz und gegebenenfalls anwaltliche Freigabe |

Die Bezeichnung „Jurist“ allein belegt keine Befugnis zur selbstständigen Rechtsberatung. Das öffentliche Projekt bleibt eine allgemeine Compliance-Arbeitshilfe und darf keine verbindliche Einzelfallentscheidung vortäuschen.

## Automatischer Ablauf

1. `legal-watch.yml` ruft die Einträge aus `legal-sources.json` ab.
2. `scripts/legal_watch.py` prüft Erreichbarkeit, erwartete Kennzeichen, technische Fingerabdrücke und Review-Intervalle.
3. Bei Abweichungen wird ein offenes GitHub-Issue mit dem Label `legal-watch` erstellt oder ergänzt.
4. Eine verantwortliche Person prüft die amtliche Quelle und ihre Bedeutung.
5. Erst danach werden Skill, Referenzen, Tests und gegebenenfalls die technische Baseline in einem Pull Request angepasst.
6. Die normale Validierung muss vor dem Zusammenführen vollständig bestehen.

Der Workflow ändert niemals selbstständig Rechtsauslegung, Risikostufe, Frist oder Handlungsempfehlung.

## Technische Baseline freigeben

Erst nach Sichtprüfung aller registrierten Zielseiten ausführen:

```bash
python scripts/legal_watch.py \
  --network \
  --refresh-baseline \
  --reviewer "Vorname Nachname"
```

Der Befehl bestätigt nur die beobachteten technischen Dokumentstände. Eine fachliche Rechtsstandsprüfung muss zusätzlich durch Änderung von `last_reviewed_on` in `legal-sources.json` dokumentiert werden.

## Abschluss eines Rechtsstands-Issues

Das Issue erst schließen, wenn:

- die amtliche Quelle direkt geöffnet wurde,
- Inkrafttreten, Anwendungsdatum und Übergangsrecht geprüft wurden,
- betroffene Skill-Dateien und Testfälle identifiziert wurden,
- Tatsachen und rechtliche Bewertung getrennt dokumentiert sind,
- portable Prompts neu erzeugt wurden,
- Repository-Validierung und Tests bestanden sind,
- diese Datei bei einer materiellen Änderung einen neuen Prüfstand nennt.

## Betriebsgrenze

GitHub kann geplante Workflows in länger inaktiven öffentlichen Repositories deaktivieren. Deshalb ist der Lauf zusätzlich monatlich im Bereich „Actions“ zu kontrollieren. „Kein automatischer Hinweis“ bedeutet nicht „Rechtsstand garantiert aktuell“.
