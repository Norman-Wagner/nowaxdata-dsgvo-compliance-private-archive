# Rechtsstand und Freigabeprozess

## Aktueller Stand

- Redaktionell geprüfter Ausgangsstand: **18. Juli 2026**
- Automatische Quellenüberwachung: wöchentlich und manuell auslösbar
- Technische Baseline: am **18. Juli 2026** automatisch aus zehn erreichbaren amtlichen oder behördlichen Quellen erfasst
- Verantwortlich für Projektfreigaben: **Norman Wagner / WagnerConnect**

Die Baseline bestätigt nur den technisch beobachteten Dokumentstand. Sie ist keine menschliche oder juristische Freigabe und keine Garantie, dass sich Recht, Rechtsprechung oder Behördenpraxis danach nicht geändert haben.

## Rollen

| Änderung | Mindestprüfung |
| --- | --- |
| Defekter Link, technische Metadaten, Zeichenkodierung, Prompt-Neubau oder erste Baseline | technische Prüfung; kein Jurist erforderlich |
| Neue Dokumentfassung ohne erkennbare inhaltliche Auswirkung | dokumentierte redaktionelle Prüfung im Vier-Augen-Prinzip empfohlen |
| Neue Norm, Rechtsprechung, Behördenleitlinie oder Anwendungsfrist | fachkundige datenschutzrechtliche Prüfung |
| Neue Bewertung eines konkreten fremden Einzelfalls | Prüfung der Befugnis nach dem Rechtsdienstleistungsgesetz und gegebenenfalls anwaltliche Freigabe |

Die Bezeichnung „Jurist“ allein belegt keine Befugnis zur selbstständigen Rechtsberatung. Das öffentliche Projekt bleibt eine allgemeine Compliance-Arbeitshilfe und darf keine verbindliche Einzelfallentscheidung vortäuschen.

## Automatischer Ablauf

1. `legal-watch.yml` ruft die Einträge aus `legal-sources.json` ab.
2. `scripts/legal_watch.py` prüft Erreichbarkeit, erwartete Kennzeichen, technische Fingerabdrücke und Review-Intervalle.
3. Bei Abweichungen wird ein offenes GitHub-Issue mit dem Label `legal-watch` erstellt oder ergänzt.
4. Eine verantwortliche Person prüft die amtliche Quelle und ihre Bedeutung.
5. Erst danach werden Skill, Referenzen, Tests und gegebenenfalls die technische Baseline angepasst.
6. Die normale Validierung muss vor dem Zusammenführen vollständig bestehen.

Der Workflow ändert niemals selbstständig Rechtsauslegung, Risikostufe, Frist oder Handlungsempfehlung.

## Technische Baseline erfassen

Für die erste technische Ausgangsbeobachtung oder nach einem dokumentierten Quellenreview ausführen:

```bash
python scripts/legal_watch.py \
  --network \
  --capture-baseline \
  --captured-by "System oder verantwortliche Person"
```

Der Befehl speichert nur technische Fingerabdrücke, Zieladressen und Erfassungsdatum. Er darf nicht als Rechtsfreigabe bezeichnet werden. Eine fachliche Rechtsstandsprüfung wird getrennt durch das Prüfdatum in `legal-sources.json` und die zugehörige Issue- oder Commit-Dokumentation nachgewiesen.

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
