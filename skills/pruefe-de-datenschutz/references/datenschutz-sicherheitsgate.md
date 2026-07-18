# Datenschutz-Sicherheitsgate

## Reihenfolge

Wende dieses Gate vor jeder inhaltlichen Prüfung, Übersetzung, Strukturierung, Speicherung, Recherche oder Werkzeugnutzung an.

1. Prüfe, ob der Input echte oder möglicherweise personenbeziehbare Daten enthält.
2. Prüfe, ob eine strengere System-, Nutzer- oder Organisationsregel die Verarbeitung sperrt.
3. Bestimme, ob konkrete Identifikatoren für die Rechtsfrage überhaupt nötig sind.
4. Entferne oder abstrahiere unnötige Identifikatoren, bevor andere Werkzeuge oder externe Quellen genutzt werden.

## Als personenbeziehbar behandeln

- Namen, Anschriften, Telefonnummern, E-Mail-Adressen und Geburtsdaten,
- Personal-, Kunden-, Fall-, Vertrags-, Versicherungs- und Zahlungsdaten,
- Gesundheits-, Religions-, Gewerkschafts-, Sexual-, biometrische und genetische Daten,
- strafrechtliche Angaben,
- Fotos, Stimmen, Unterschriften, Kennzeichen, IP-Adressen, Geräte- und Protokolldaten,
- berufliche Kontaktdaten natürlicher Personen,
- öffentliche Daten und Kombinationen, die eine Person bestimmbar machen,
- pseudonymisierte Daten, solange eine Zuordnung mit vertretbarem Aufwand möglich ist.

## Reaktion

### Strenge Sperrregel aktiv

- Stoppe die weitere inhaltliche Verarbeitung der betroffenen Daten.
- Wiederhole die Daten nicht.
- Gib nur einen allgemeinen Warnhinweis aus.
- Bitte um eine bereinigte Fassung, wenn die Aufgabe sonst nicht fortgesetzt werden kann.

### Keine strenge Sperrregel, Identität nicht nötig

- Verwende Rollen wie `betroffene Person`, `Mitarbeiter A`, `Anbieter B` oder `Vorgang 1`.
- Behalte nur Sachverhaltsmerkmale, die die rechtliche Bewertung verändern.
- Übernimm die Originalwerte weder in Ausgaben noch in Dateinamen, Suchanfragen, Logs, Commits oder Testfälle.

### Identität ausnahmsweise rechtlich nötig

- Erkläre knapp, warum die konkrete Identität erheblich ist.
- Verarbeite nur das Minimum und nur im vom Nutzer freigegebenen Zielsystem.
- Nutze keine öffentlichen Suchdienste zur Anreicherung eines privaten Falls.
- Prüfe vor Speicherung, ob eine lokale oder organisatorische Regel sie erlaubt.

## Besondere Warnzeichen

Verlange grundsätzlich eine pseudonymisierte Fassung bei Gesundheitsdaten, Kindern, Beschäftigtenakten, Bestattungs- oder Familiensachverhalten, Berufsgeheimnissen, Ausweisen, Bankdaten, Zugangsdaten und vollständigen Behördenakten.

Die DSGVO (Datenschutz-Grundverordnung) gilt nach Erwägungsgrund 27 grundsätzlich nicht für Daten Verstorbener. Prüfe trotzdem, ob dieselben Informationen lebende Angehörige, Beschäftigte oder andere Personen identifizieren und ob nationales, kirchliches, berufs- oder sektorspezifisches Recht greift.

## Kein falsches Sicherheitsversprechen

Automatische Erkennung kann Personendaten übersehen. Behaupte nie, ein Dokument sei sicher anonymisiert, nur weil typische Muster entfernt wurden. Prüfe Kontext, Kombinationen und Re-Identifizierbarkeit.
