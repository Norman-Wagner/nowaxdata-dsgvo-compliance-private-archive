#!/usr/bin/env python3
"""Überwacht amtliche Rechtsquellen, ohne Rechtsänderungen automatisch auszulegen."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "legal-sources.json"
DEFAULT_BASELINE = ROOT / "legal-source-baseline.json"
USER_AGENT = "NOWA-X-DSGVO-Legal-Watch/1.0"


class VisibleTextParser(HTMLParser):
    """Extrahiert sichtbaren Text mit möglichst wenig dynamischem Seitengerüst."""

    ignored_tags = {"script", "style", "noscript", "svg", "template"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._ignored_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in self.ignored_tags:
            self._ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self.ignored_tags and self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._ignored_depth:
            self.parts.append(data)


@dataclass(frozen=True)
class FetchResult:
    body: bytes
    content_type: str
    final_url: str
    status: int


Fetcher = Callable[[dict[str, object], dict[str, object]], FetchResult]


def read_json(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{path.name} ist nicht lesbar: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} muss ein JSON-Objekt enthalten")
    return value


def host_is_allowed(host: str, allowed_hosts: list[str]) -> bool:
    host = host.lower().rstrip(".")
    return any(host == allowed or host.endswith("." + allowed) for allowed in allowed_hosts)


def validate_registry(registry: dict[str, object]) -> list[str]:
    errors: list[str] = []
    if registry.get("schema_version") != 1:
        errors.append("legal-sources.json: schema_version muss 1 sein")

    policy = registry.get("policy")
    sources = registry.get("sources")
    if not isinstance(policy, dict):
        return errors + ["legal-sources.json: policy fehlt oder ist ungültig"]
    if not isinstance(sources, list) or not sources:
        return errors + ["legal-sources.json: sources fehlt oder ist leer"]

    allowed_hosts = policy.get("allowed_hosts")
    if not isinstance(allowed_hosts, list) or not all(isinstance(item, str) and item for item in allowed_hosts):
        errors.append("legal-sources.json: allowed_hosts ist ungültig")
        allowed_hosts = []

    ids: set[str] = set()
    for position, source in enumerate(sources, start=1):
        prefix = f"legal-sources.json: Quelle {position}"
        if not isinstance(source, dict):
            errors.append(f"{prefix} ist kein Objekt")
            continue
        source_id = source.get("id")
        if not isinstance(source_id, str) or not re.fullmatch(r"[a-z0-9-]+", source_id):
            errors.append(f"{prefix}: id ist ungültig")
        elif source_id in ids:
            errors.append(f"{prefix}: id {source_id} ist doppelt")
        else:
            ids.add(source_id)
        for key in ("title", "category", "url"):
            if not isinstance(source.get(key), str) or not source[key]:
                errors.append(f"{prefix}: {key} fehlt")
        url = str(source.get("url", ""))
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "https" or not parsed.hostname:
            errors.append(f"{prefix}: nur vollständige HTTPS-URLs sind erlaubt")
        elif allowed_hosts and not host_is_allowed(parsed.hostname, allowed_hosts):
            errors.append(f"{prefix}: Host {parsed.hostname} ist nicht freigegeben")
        if source.get("hash_mode") not in {"raw", "text"}:
            errors.append(f"{prefix}: hash_mode muss raw oder text sein")
        markers = source.get("required_markers")
        if not isinstance(markers, list) or not markers or not all(isinstance(item, str) and item for item in markers):
            errors.append(f"{prefix}: required_markers ist ungültig")
        try:
            reviewed = date.fromisoformat(str(source.get("last_reviewed_on", "")))
            if reviewed > date.today():
                errors.append(f"{prefix}: last_reviewed_on liegt in der Zukunft")
        except ValueError:
            errors.append(f"{prefix}: last_reviewed_on ist kein ISO-Datum")
        interval = source.get("review_every_days")
        if not isinstance(interval, int) or not 1 <= interval <= 365:
            errors.append(f"{prefix}: review_every_days muss zwischen 1 und 365 liegen")

    for key, lower, upper in (
        ("request_timeout_seconds", 1, 120),
        ("maximum_response_bytes", 1024, 100_000_000),
    ):
        value = policy.get(key)
        if not isinstance(value, int) or not lower <= value <= upper:
            errors.append(f"legal-sources.json: {key} ist ungültig")
    return errors


def validate_baseline(baseline: dict[str, object], source_ids: set[str]) -> list[str]:
    errors: list[str] = []
    if baseline.get("schema_version") != 1:
        errors.append("legal-source-baseline.json: schema_version muss 1 sein")
    entries = baseline.get("sources")
    if not isinstance(entries, dict):
        return errors + ["legal-source-baseline.json: sources ist ungültig"]
    for source_id, entry in entries.items():
        if source_id not in source_ids:
            errors.append(f"legal-source-baseline.json: unbekannte Quelle {source_id}")
            continue
        if not isinstance(entry, dict):
            errors.append(f"legal-source-baseline.json: Eintrag {source_id} ist ungültig")
            continue
        fingerprint = entry.get("sha256")
        if not isinstance(fingerprint, str) or not re.fullmatch(r"[0-9a-f]{64}", fingerprint):
            errors.append(f"legal-source-baseline.json: sha256 für {source_id} ist ungültig")
        try:
            date.fromisoformat(str(entry.get("approved_on", "")))
        except ValueError:
            errors.append(f"legal-source-baseline.json: approved_on für {source_id} ist ungültig")
        if not isinstance(entry.get("approved_by"), str) or not entry["approved_by"].strip():
            errors.append(f"legal-source-baseline.json: approved_by für {source_id} fehlt")
    return errors


def fetch_source(source: dict[str, object], policy: dict[str, object]) -> FetchResult:
    request = urllib.request.Request(
        str(source["url"]),
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml,application/pdf;q=0.9,*/*;q=0.5",
        },
    )
    timeout = int(policy["request_timeout_seconds"])
    maximum = int(policy["maximum_response_bytes"])
    with urllib.request.urlopen(request, timeout=timeout) as response:
        final_url = response.geturl()
        final_host = urllib.parse.urlparse(final_url).hostname or ""
        allowed = [str(item) for item in policy["allowed_hosts"]]
        if not host_is_allowed(final_host, allowed):
            raise ValueError(f"Weiterleitung auf nicht freigegebenen Host: {final_host}")
        body = response.read(maximum + 1)
        if len(body) > maximum:
            raise ValueError(f"Antwort überschreitet {maximum} Bytes")
        content_type = response.headers.get_content_type()
        return FetchResult(body=body, content_type=content_type, final_url=final_url, status=response.status)


def text_payload(body: bytes, content_type: str) -> str:
    decoded = body.decode("utf-8", errors="replace")
    if content_type in {"text/html", "application/xhtml+xml"} or "<html" in decoded[:1000].lower():
        parser = VisibleTextParser()
        parser.feed(decoded)
        decoded = " ".join(parser.parts)
    decoded = html.unescape(decoded)
    decoded = unicodedata.normalize("NFC", decoded)
    return re.sub(r"\s+", " ", decoded).strip()


def fingerprint(source: dict[str, object], fetched: FetchResult) -> tuple[str, str]:
    if source["hash_mode"] == "raw":
        payload = fetched.body
        searchable = fetched.body.decode("utf-8", errors="replace")
    else:
        searchable = text_payload(fetched.body, fetched.content_type)
        payload = searchable.encode("utf-8")
    return hashlib.sha256(payload).hexdigest(), searchable


def evaluate(
    registry: dict[str, object],
    baseline: dict[str, object],
    *,
    today: date,
    network: bool,
    fetcher: Fetcher = fetch_source,
) -> list[dict[str, object]]:
    policy = registry["policy"]
    assert isinstance(policy, dict)
    baseline_sources = baseline.get("sources", {})
    assert isinstance(baseline_sources, dict)
    results: list[dict[str, object]] = []

    for source in registry["sources"]:
        assert isinstance(source, dict)
        reviewed = date.fromisoformat(str(source["last_reviewed_on"]))
        age = (today - reviewed).days
        overdue = age > int(source["review_every_days"])
        result: dict[str, object] = {
            "id": source["id"],
            "title": source["title"],
            "url": source["url"],
            "review_age_days": age,
            "review_overdue": overdue,
            "network_checked": False,
            "changed": False,
            "baseline_missing": False,
            "markers_missing": [],
            "error": None,
            "sha256": None,
        }
        if network:
            try:
                fetched = fetcher(source, policy)
                digest, searchable = fingerprint(source, fetched)
                entry = baseline_sources.get(str(source["id"]))
                result["network_checked"] = True
                result["sha256"] = digest
                result["final_url"] = fetched.final_url
                if not isinstance(entry, dict):
                    result["baseline_missing"] = True
                else:
                    result["changed"] = digest != entry.get("sha256")
                missing = [
                    marker
                    for marker in source["required_markers"]
                    if str(marker).casefold() not in searchable.casefold()
                ]
                result["markers_missing"] = missing
            except (OSError, ValueError, urllib.error.URLError) as exc:
                result["error"] = str(exc)
        result["attention"] = bool(
            overdue
            or result["changed"]
            or result["baseline_missing"]
            or result["markers_missing"]
            or result["error"]
        )
        results.append(result)
    return results


def render_report(results: list[dict[str, object]], today: date, network: bool) -> str:
    lines = [
        "# Automatische Rechtsquellenprüfung",
        "",
        f"Prüftag (UTC): **{today.isoformat()}**. Modus: **{'Netzwerkprüfung' if network else 'Offline-Strukturprüfung'}**.",
        "",
        "> Dieser Bericht erkennt technische Änderungen und überfällige Prüfintervalle. "
        "Er bestätigt weder die juristische Bedeutung einer Änderung noch die Richtigkeit des Skills.",
        "",
        "| Quelle | Abruf | Fingerabdruck | Fachprüfung | Ergebnis |",
        "| --- | --- | --- | --- | --- |",
    ]
    actions: list[str] = []
    for result in results:
        if not network:
            retrieval = "nicht ausgeführt"
            technical = "nicht geprüft"
        elif result["error"]:
            retrieval = "Fehler"
            technical = "nicht prüfbar"
            actions.append(f"**{result['title']}:** Abruffehler prüfen: {result['error']}")
        else:
            retrieval = "erreichbar"
            if result["baseline_missing"]:
                technical = "Baseline fehlt"
                actions.append(f"**{result['title']}:** technische Baseline nach Sichtprüfung freigeben.")
            elif result["changed"]:
                technical = "geändert"
                actions.append(f"**{result['title']}:** Änderung fachlich bewerten und erst danach die Baseline erneuern.")
            else:
                technical = "unverändert"
            if result["markers_missing"]:
                technical += "; Marker fehlt"
                actions.append(
                    f"**{result['title']}:** erwartete Kennzeichen fehlen: "
                    + ", ".join(str(item) for item in result["markers_missing"])
                    + "."
                )
        if result["review_overdue"]:
            review = f"überfällig ({result['review_age_days']} Tage)"
            actions.append(f"**{result['title']}:** fachliche Rechtsstandsprüfung dokumentieren.")
        else:
            review = f"im Intervall ({result['review_age_days']} Tage)"
        outcome = "Prüfung nötig" if result["attention"] else "kein Hinweis"
        lines.append(
            f"| [{result['title']}]({result['url']}) | {retrieval} | {technical} | {review} | {outcome} |"
        )
    lines.extend(["", "## Erforderliche Maßnahmen", ""])
    if actions:
        lines.extend(f"- {item}" for item in dict.fromkeys(actions))
    else:
        lines.append("- Keine automatischen Hinweise. Eine fachliche Freigabe bleibt bei relevanten Rechtsänderungen erforderlich.")
    lines.extend(
        [
            "",
            "## Freigabegrenze",
            "",
            "Der Workflow darf Quellenstatus, Erreichbarkeit und technische Fingerabdrücke prüfen. "
            "Er darf keine Rechtsauslegung, Risikobewertung oder Handlungsempfehlung automatisch ändern.",
            "",
        ]
    )
    return "\n".join(lines)


def write_github_output(attention_count: int) -> None:
    target = os.environ.get("GITHUB_OUTPUT")
    if not target:
        return
    with open(target, "a", encoding="utf-8") as handle:
        handle.write(f"attention={'true' if attention_count else 'false'}\n")
        handle.write(f"attention_count={attention_count}\n")


def refresh_baseline(
    registry: dict[str, object],
    baseline_path: Path,
    reviewer: str,
    today: date,
    fetcher: Fetcher = fetch_source,
) -> int:
    policy = registry["policy"]
    assert isinstance(policy, dict)
    entries: dict[str, dict[str, str]] = {}
    failures: list[str] = []
    for source in registry["sources"]:
        assert isinstance(source, dict)
        try:
            fetched = fetcher(source, policy)
            digest, searchable = fingerprint(source, fetched)
            missing = [
                marker
                for marker in source["required_markers"]
                if str(marker).casefold() not in searchable.casefold()
            ]
            if missing:
                failures.append(f"{source['id']}: Marker fehlen: {', '.join(str(item) for item in missing)}")
                continue
            entries[str(source["id"])] = {
                "sha256": digest,
                "approved_on": today.isoformat(),
                "approved_by": reviewer,
                "observed_url": fetched.final_url,
            }
        except (OSError, ValueError, urllib.error.URLError) as exc:
            failures.append(f"{source['id']}: {exc}")
    if failures:
        for failure in failures:
            print(f"FEHLER: {failure}", file=sys.stderr)
        print("Baseline wurde nicht verändert.", file=sys.stderr)
        return 1
    payload = {
        "schema_version": 1,
        "notice": "Technische Fingerabdrücke nach menschlicher Sichtprüfung freigegeben; keine juristische Freigabe.",
        "sources": entries,
    }
    baseline_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Technische Baseline für {len(entries)} Quellen aktualisiert.")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--network", action="store_true", help="Quellen wirklich abrufen")
    parser.add_argument("--report", type=Path, help="Markdown-Bericht schreiben")
    parser.add_argument("--json-report", type=Path, help="Maschinenlesbaren Bericht schreiben")
    parser.add_argument("--today", type=date.fromisoformat, default=date.today())
    parser.add_argument(
        "--refresh-baseline",
        action="store_true",
        help="Fingerabdrücke nach menschlicher Sichtprüfung neu freigeben",
    )
    parser.add_argument("--reviewer", help="Verantwortliche Person für --refresh-baseline")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        registry = read_json(args.registry)
        baseline = read_json(args.baseline)
    except ValueError as exc:
        print(f"FEHLER: {exc}", file=sys.stderr)
        return 1

    errors = validate_registry(registry)
    sources = registry.get("sources", [])
    source_ids = {str(item.get("id")) for item in sources if isinstance(item, dict)}
    errors.extend(validate_baseline(baseline, source_ids))
    if errors:
        for error in errors:
            print(f"FEHLER: {error}", file=sys.stderr)
        return 1

    if args.refresh_baseline:
        if not args.network:
            print("FEHLER: --refresh-baseline erfordert --network", file=sys.stderr)
            return 1
        if not args.reviewer or len(args.reviewer.strip()) < 3:
            print("FEHLER: --reviewer muss die freigebende Person nennen", file=sys.stderr)
            return 1
        return refresh_baseline(registry, args.baseline, args.reviewer.strip(), args.today)

    results = evaluate(registry, baseline, today=args.today, network=args.network)
    report = render_report(results, args.today, args.network)
    if args.report:
        args.report.write_text(report, encoding="utf-8")
    else:
        print(report)
    if args.json_report:
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "check_date": args.today.isoformat(),
            "network": args.network,
            "results": results,
        }
        args.json_report.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    attention_count = sum(bool(item["attention"]) for item in results)
    write_github_output(attention_count)
    print(f"Rechtsquellenprüfung abgeschlossen: {attention_count} Hinweis(e).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
