#!/usr/bin/env python3
"""Prüft Projektdateien heuristisch auf Personendaten und Geheimnisse."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
MAX_FILE_BYTES = 2_000_000
IGNORED_PARTS = {".git", ".venv", "__pycache__", "node_modules"}
ALLOW_MARKER = re.compile(r"privacy-scan:\s*allow\([^)]+\)", re.IGNORECASE)


@dataclass(frozen=True)
class Finding:
    code: str
    path: Path
    line: int
    message: str


PATTERNS = (
    (
        "SECRET_PRIVATE_KEY",
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
        "Möglicher privater Schlüssel",
    ),
    (
        "SECRET_GITHUB_TOKEN",
        re.compile(r"\bgh" r"[pousr]_[A-Za-z0-9]{30,}\b|\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
        "Mögliches GitHub-Token",
    ),
    (
        "SECRET_OPENAI_KEY",
        re.compile(r"\bsk" r"-(?:proj-)?[A-Za-z0-9_-]{20,}\b"),
        "Möglicher API-Schlüssel",
    ),
    (
        "SECRET_AWS_KEY",
        re.compile(r"\bAK" r"IA[0-9A-Z]{16}\b"),
        "Möglicher AWS-Zugriffsschlüssel",
    ),
    (
        "SECRET_SLACK_TOKEN",
        re.compile(r"\bxox" r"[baprs]-[A-Za-z0-9-]{10,}\b"),
        "Mögliches Slack-Token",
    ),
    (
        "SECRET_GOOGLE_KEY",
        re.compile(r"\bAI" r"za[0-9A-Za-z_-]{35}\b"),
        "Möglicher Google-API-Schlüssel",
    ),
    (
        "PERSON_EMAIL",
        re.compile(r"(?<![\w.+-])[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}(?![\w.-])", re.IGNORECASE),
        "Mögliche E-Mail-Adresse",
    ),
    (
        "PERSON_IBAN",
        re.compile(r"\bDE(?:[ -]?\d){20}\b", re.IGNORECASE),
        "Mögliche deutsche IBAN",
    ),
    (
        "PERSON_PHONE_INTL",
        re.compile(r"(?<!\w)(?:\+49|0049)\s*(?:\(0\)\s*)?(?:\d[\s./-]?){6,13}(?!\w)"),
        "Mögliche deutsche Telefonnummer",
    ),
    (
        "PERSON_PHONE_LOCAL",
        re.compile(r"(?<!\w)0\d{2,5}[ /-]\d(?:[\s-]?\d){4,10}(?!\w)"),
        "Mögliche deutsche Telefonnummer",
    ),
)

CARD_CANDIDATE = re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")


def luhn_valid(digits: str) -> bool:
    if not 13 <= len(digits) <= 19 or len(set(digits)) == 1:
        return False
    total = 0
    parity = len(digits) % 2
    for index, character in enumerate(digits):
        value = int(character)
        if index % 2 == parity:
            value *= 2
            if value > 9:
                value -= 9
        total += value
    return total % 10 == 0


def scan_text(path: Path, text: str) -> list[Finding]:
    findings: list[Finding] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if ALLOW_MARKER.search(line):
            continue
        for code, pattern, message in PATTERNS:
            if pattern.search(line):
                findings.append(Finding(code, path, line_number, message))
        for match in CARD_CANDIDATE.finditer(line):
            digits = re.sub(r"\D", "", match.group(0))
            if luhn_valid(digits):
                findings.append(
                    Finding("PERSON_PAYMENT_CARD", path, line_number, "Mögliche Zahlungskartennummer")
                )
                break
    return findings


def scan_file(path: Path) -> list[Finding]:
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return []
        data = path.read_bytes()
    except OSError:
        return []
    if b"\0" in data:
        return []
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return []
    return scan_text(path, text)


def repository_files(root: Path = ROOT) -> list[Path]:
    command = ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"]
    result = subprocess.run(command, cwd=root, check=False, capture_output=True)
    if result.returncode == 0:
        return sorted(root / item for item in result.stdout.decode("utf-8").split("\0") if item)
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and not any(part in IGNORED_PARTS for part in path.relative_to(root).parts)
    )


def scan_paths(paths: Iterable[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for path in paths:
        findings.extend(scan_file(path))
    return findings


def display_path(path: Path, root: Path = ROOT) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, help="Optional: nur diese Dateien prüfen")
    args = parser.parse_args()
    paths = args.paths or repository_files()
    findings = scan_paths(path.resolve() for path in paths)
    if findings:
        for finding in findings:
            print(
                f"FEHLER [{finding.code}] {display_path(finding.path)}:{finding.line}: {finding.message}"
            )
        print(
            "Datenschutzprüfung fehlgeschlagen. Inhalte lokal entfernen oder durch synthetische Daten ersetzen."
        )
        return 1
    print("Keine typischen Personendaten oder Geheimnisse in den geprüften Projektdateien erkannt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
