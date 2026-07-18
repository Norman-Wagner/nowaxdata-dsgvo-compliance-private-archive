#!/usr/bin/env python3
"""Prüft die Struktur eines erzeugten Datenschutz-Memos.

Das Skript erkennt formale Lücken. Es bewertet weder die Richtigkeit einer
Rechtsauffassung noch die Vollständigkeit einer Anonymisierung.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_CONCEPTS = {
    "Kurzfazit": re.compile(r"(?im)^#{1,6}\s+.*(?:kurzfazit|ergebnis)"),
    "Sachverhalt": re.compile(r"(?im)^#{1,6}\s+.*(?:sachverhalt|fakten)"),
    "Rechtsprüfung": re.compile(r"(?im)^#{1,6}\s+.*(?:rechtsprüfung|rechtliche einordnung|warum)"),
    "Maßnahmen": re.compile(r"(?im)^#{1,6}\s+.*(?:maßnahmen|jetzt tun|handlung)"),
    "Offene Punkte": re.compile(r"(?im)^#{1,6}\s+.*(?:offen|annahmen|fehlende)"),
    "Stand": re.compile(r"(?im)^#{1,6}\s+.*(?:stand|quellen)"),
}

OFFICIAL_DOMAINS = (
    "eur-lex.europa.eu",
    "gesetze-im-internet.de",
    "edpb.europa.eu",
    "datenschutzkonferenz-online.de",
    "bfdi.bund.de",
    "curia.europa.eu",
    "rechtsprechung-im-internet.de",
)

OVERCLAIMS = (
    "100% rechtssicher",
    "100 prozent rechtssicher",
    "garantiert rechtssicher",
    "vollständig dsgvo-konform",
    "risikofrei",
)


def check(text: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for label, pattern in REQUIRED_CONCEPTS.items():
        if not pattern.search(text):
            errors.append(f"Pflichtabschnitt fehlt: {label}")

    lowered = text.casefold()
    for phrase in OVERCLAIMS:
        if phrase in lowered:
            errors.append(f"Unzulässiges Sicherheitsversprechen: {phrase}")

    if not re.search(r"\b20\d{2}-\d{2}-\d{2}\b|\b\d{1,2}\.\s*[A-Za-zÄÖÜäöüß]+\s+20\d{2}\b", text):
        errors.append("Kein eindeutiges Standdatum gefunden")

    if not any(domain in lowered for domain in OFFICIAL_DOMAINS):
        if "aktueller rechtsstand nicht verifiziert" not in lowered:
            errors.append("Keine amtliche oder behördliche Onlinequelle gefunden")

    if "dsgvo-gesetz.de" in lowered and not any(domain in lowered for domain in OFFICIAL_DOMAINS[:2]):
        errors.append("dsgvo-gesetz.de wird ohne amtliche Gegenquelle verwendet")

    for line_no, line in enumerate(text.splitlines(), start=1):
        if re.search(r"\bTTDSG\b", line) and not re.search(r"(?i)ehem|histor|alt|früher|veraltet", line):
            errors.append(f"Zeile {line_no}: TTDSG als aktueller Gesetzesname verdächtig")
        if re.search(r"(?i)\bTODO\b|\[TODO", line):
            errors.append(f"Zeile {line_no}: unerledigter TODO-Hinweis")

    email_hits = re.findall(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", text, flags=re.I)
    if email_hits:
        warnings.append("E-Mail-Adresse gefunden; prüfen, ob sie wirklich nötig und zur Ausgabe freigegeben ist")

    phone_hits = [
        hit
        for hit in re.findall(r"(?<!\w)(?:\+?\d[\d ()/.-]{7,}\d)(?!\w)", text)
        if not re.fullmatch(r"20\d{2}-\d{2}-\d{2}", hit)
    ]
    if phone_hits:
        warnings.append("Mögliche Telefonnummer oder lange Nummer gefunden; Personendatenprüfung nötig")

    if "belegt" not in lowered and "bewertung" not in lowered:
        warnings.append("Trennung zwischen belegter Quelle und eigener Bewertung nicht erkennbar")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path, help="Markdown-Datei mit dem Prüfergebnis")
    args = parser.parse_args()

    if not args.file.is_file():
        print(f"FEHLER: Datei nicht gefunden: {args.file}", file=sys.stderr)
        return 2

    text = args.file.read_text(encoding="utf-8")
    errors, warnings = check(text)

    for item in warnings:
        print(f"WARNUNG: {item}")
    for item in errors:
        print(f"FEHLER: {item}")

    if errors:
        print(f"Ergebnis: {len(errors)} Fehler, {len(warnings)} Warnungen")
        return 1

    print(f"Ergebnis: Strukturprüfung bestanden, {len(warnings)} Warnungen")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
