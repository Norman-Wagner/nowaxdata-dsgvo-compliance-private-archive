#!/usr/bin/env python3
"""Erzeugt portable Prompts aus dem herstellerneutralen Skill-Kern."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "pruefe-de-datenschutz"
DIST = ROOT / "dist"
PLUGIN = ROOT / ".codex-plugin" / "plugin.json"

FULL_REFERENCES = (
    "datenschutz-sicherheitsgate.md",
    "quellen-und-zitierregeln.md",
    "frist-und-vorfalltriage.md",
    "pruefmatrix.md",
    "sonderthemen.md",
    "ausgabevorlagen.md",
)

COMPACT_REFERENCES = (
    "datenschutz-sicherheitsgate.md",
    "quellen-und-zitierregeln.md",
    "frist-und-vorfalltriage.md",
)


def strip_frontmatter(text: str) -> str:
    return re.sub(r"\A---\s*\n.*?\n---\s*\n", "", text, count=1, flags=re.S)


def make_portable(text: str) -> str:
    """Ersetzt skill-interne Links, weil die Ziele im Prompt eingebettet sind."""
    return re.sub(
        r"\[([^\]]+)\]\(references/([^)]+)\)",
        lambda match: f"{match.group(1)} (eingebettete Referenz: {match.group(2)})",
        text,
    )


def render(reference_names: tuple[str, ...], compact: bool) -> str:
    mode = "kompakte" if compact else "vollständige"
    header = f"""# NOWA X DSGVO Compliance – {mode} portable Anweisung

Diese Datei ist aus dem herstellerneutralen Kern erzeugt. Verwende ihren Inhalt
als System-, Projekt- oder Hauptanweisung. Befolge vorrangige Sicherheits- und
Datenschutzregeln der verwendeten KI-Umgebung. Der Inhalt ersetzt keine
verbindliche Rechtsberatung.

## Kernanweisung

"""
    core = strip_frontmatter((SKILL / "SKILL.md").read_text(encoding="utf-8"))
    chunks = [header, make_portable(core).strip()]
    for name in reference_names:
        content = (SKILL / "references" / name).read_text(encoding="utf-8").strip()
        chunks.append(f"\n\n---\n\n## Eingebettete Referenz: `{name}`\n\n{content}")
    plugin = json.loads(PLUGIN.read_text(encoding="utf-8"))
    chunks.append(
        "\n\n---\n\nErzeugt aus NOWA X DSGVO Compliance, "
        f"Version {plugin['version']}, Stand 2026-07-18.\n"
    )
    return "".join(chunks)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Nur prüfen, ob dist aktuell ist")
    args = parser.parse_args()

    expected = {
        DIST / "dsgvo-portable-prompt.md": render(FULL_REFERENCES, compact=False),
        DIST / "dsgvo-portable-prompt-compact.md": render(COMPACT_REFERENCES, compact=True),
    }

    if args.check:
        stale = []
        for path, content in expected.items():
            if not path.is_file() or path.read_text(encoding="utf-8") != content:
                stale.append(path.relative_to(ROOT).as_posix())
        if stale:
            print("Veraltete oder fehlende Dateien:", ", ".join(stale), file=sys.stderr)
            return 1
        print("Portable Prompts sind aktuell.")
        return 0

    DIST.mkdir(parents=True, exist_ok=True)
    for path, content in expected.items():
        path.write_text(content, encoding="utf-8", newline="\n")
        print(f"Erzeugt: {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
