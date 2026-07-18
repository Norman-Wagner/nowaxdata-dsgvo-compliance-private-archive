#!/usr/bin/env python3
"""Offline-Validator für Repository, Plugin und Skill."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_PATH = ROOT / ".codex-plugin" / "plugin.json"
LEGAL_SOURCES_PATH = ROOT / "legal-sources.json"
LEGAL_BASELINE_PATH = ROOT / "legal-source-baseline.json"
SKILL = ROOT / "skills" / "pruefe-de-datenschutz"
SKILL_MD = SKILL / "SKILL.md"


def error(errors: list[str], message: str) -> None:
    errors.append(message)


def parse_frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, flags=re.S)
    if not match:
        return {}
    values: dict[str, str] = {}
    for raw in match.group(1).splitlines():
        if ":" not in raw:
            continue
        key, value = raw.split(":", 1)
        values[key.strip()] = value.strip().strip('"\'')
    return values


def validate_markdown_links(errors: list[str]) -> None:
    pattern = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
    for path in ROOT.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        for target in pattern.findall(text):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            clean = target.split("#", 1)[0]
            if clean and not (path.parent / clean).resolve().exists():
                error(errors, f"Defekter lokaler Link in {path.relative_to(ROOT)}: {target}")


def main() -> int:
    errors: list[str] = []

    try:
        plugin = json.loads(PLUGIN_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FEHLER: plugin.json unlesbar: {exc}", file=sys.stderr)
        return 1

    required_plugin = ("name", "version", "description", "author", "skills", "interface")
    for key in required_plugin:
        if not plugin.get(key):
            error(errors, f"plugin.json: Pflichtfeld fehlt: {key}")
    if plugin.get("name") != ROOT.name:
        error(errors, "Pluginname und Ordnername stimmen nicht überein")
    if not re.fullmatch(r"\d+\.\d+\.\d+", str(plugin.get("version", ""))):
        error(errors, "plugin.json: Version ist keine strikte semantische Version")
    if plugin.get("author", {}).get("name") != "Norman Wagner / WagnerConnect":
        error(errors, "plugin.json: gewünschte Urheberangabe fehlt")

    try:
        legal_sources = json.loads(LEGAL_SOURCES_PATH.read_text(encoding="utf-8"))
        legal_baseline = json.loads(LEGAL_BASELINE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        error(errors, f"Rechtsquellenregister unlesbar: {exc}")
        legal_sources = {}
        legal_baseline = {}
    sources = legal_sources.get("sources", []) if isinstance(legal_sources, dict) else []
    if not isinstance(sources, list) or len(sources) < 8:
        error(errors, "Rechtsquellenregister enthält zu wenige Quellen")
    source_ids = {
        item.get("id") for item in sources if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    baseline_sources = legal_baseline.get("sources", {}) if isinstance(legal_baseline, dict) else {}
    if not isinstance(baseline_sources, dict) or not set(baseline_sources).issubset(source_ids):
        error(errors, "Technische Quellen-Baseline passt nicht zum Register")
    if not (ROOT / "RECHTSSTAND.md").is_file():
        error(errors, "RECHTSSTAND.md fehlt")
    if not (ROOT / ".github" / "workflows" / "legal-watch.yml").is_file():
        error(errors, "Workflow zur Rechtsstandsüberwachung fehlt")
    if not (ROOT / ".github" / "workflows" / "release.yml").is_file():
        error(errors, "Workflow zur Release-Prüfung fehlt")
    if not (ROOT / ".github" / "dependabot.yml").is_file():
        error(errors, "Dependabot-Konfiguration fehlt")

    skill_text = SKILL_MD.read_text(encoding="utf-8")
    frontmatter = parse_frontmatter(skill_text)
    if set(frontmatter) != {"name", "description"}:
        error(errors, "SKILL.md: Frontmatter darf nur name und description enthalten")
    if frontmatter.get("name") != SKILL.name:
        error(errors, "SKILL.md: Name und Ordnername stimmen nicht überein")
    if not frontmatter.get("description") or len(frontmatter["description"]) > 900:
        error(errors, "SKILL.md: Description fehlt oder ist unnötig lang")
    if len(skill_text.splitlines()) > 500:
        error(errors, "SKILL.md überschreitet 500 Zeilen")

    openai_yaml = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
    for key in ("display_name:", "short_description:", "default_prompt:", "allow_implicit_invocation:"):
        if key not in openai_yaml:
            error(errors, f"agents/openai.yaml: {key} fehlt")
    if "$pruefe-de-datenschutz" not in openai_yaml:
        error(errors, "agents/openai.yaml: default_prompt nennt den Skill nicht")

    required_refs = {
        "datenschutz-sicherheitsgate.md",
        "quellen-und-zitierregeln.md",
        "frist-und-vorfalltriage.md",
        "pruefmatrix.md",
        "sonderthemen.md",
        "ausgabevorlagen.md",
    }
    found_refs = {path.name for path in (SKILL / "references").glob("*.md")}
    if found_refs != required_refs:
        error(errors, f"Referenzsatz stimmt nicht: {sorted(found_refs)}")

    combined = "\n".join(path.read_text(encoding="utf-8") for path in (SKILL / "references").glob("*.md"))
    for domain in ("eur-lex.europa.eu", "gesetze-im-internet.de", "edpb.europa.eu", "datenschutzkonferenz-online.de"):
        if domain not in combined:
            error(errors, f"Amtliche/behördliche Quellenfamilie fehlt: {domain}")
    if "dsgvo-gesetz.de" not in combined or "Arbeitshilfe" not in combined:
        error(errors, "dsgvo-gesetz.de ist nicht korrekt als Arbeitshilfe eingeordnet")

    for path in list(ROOT.rglob("*.md")) + list(ROOT.rglob("*.json")) + list(ROOT.rglob("*.yaml")):
        text = path.read_text(encoding="utf-8")
        if re.search(r"\[TODO|\bTODO:\s", text, flags=re.I):
            error(errors, f"Unerledigter TODO in {path.relative_to(ROOT)}")

    cases_path = ROOT / "tests" / "cases.json"
    try:
        cases = json.loads(cases_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        error(errors, f"Testfälle unlesbar: {exc}")
        cases = []
    if len(cases) < 10:
        error(errors, "Zu wenige plattformneutrale Testfälle")
    if not any(case.get("expect_trigger") is False for case in cases):
        error(errors, "Negativer Trigger-Test fehlt")
    if not any(case.get("expect_privacy_gate") for case in cases):
        error(errors, "Test für Datenschutz-Sicherheitsgate fehlt")

    validate_markdown_links(errors)

    generated = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_portable_prompts.py"), "--check"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if generated.returncode:
        error(errors, generated.stderr.strip() or "Portable Prompts sind veraltet")

    legal_watch = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "legal_watch.py"),
            "--report",
            os.devnull,
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if legal_watch.returncode:
        error(errors, legal_watch.stderr.strip() or "Rechtsquellenregister ist ungültig")

    if errors:
        for item in errors:
            print(f"FEHLER: {item}")
        print(f"Validierung fehlgeschlagen: {len(errors)} Fehler")
        return 1

    print("Repository-, Plugin- und Skill-Validierung bestanden.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
