from __future__ import annotations

import importlib.util
import sys
import unittest
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "legal_watch.py"
SPEC = importlib.util.spec_from_file_location("legal_watch", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def registry(last_reviewed_on: str = "2026-07-01") -> dict[str, object]:
    return {
        "schema_version": 1,
        "policy": {
            "allowed_hosts": ["example.test"],
            "request_timeout_seconds": 10,
            "maximum_response_bytes": 100000,
        },
        "sources": [
            {
                "id": "test-law",
                "title": "Testgesetz",
                "category": "verbindliches-recht",
                "url": "https://example.test/law",
                "hash_mode": "text",
                "required_markers": ["Testgesetz"],
                "last_reviewed_on": last_reviewed_on,
                "review_every_days": 30,
            }
        ],
    }


def fetcher(body: bytes):
    def inner(source: dict[str, object], policy: dict[str, object]):
        return MODULE.FetchResult(body, "text/html", str(source["url"]), 200)

    return inner


class LegalWatchTests(unittest.TestCase):
    def test_registry_validation(self) -> None:
        self.assertEqual(MODULE.validate_registry(registry()), [])

    def test_missing_baseline_requests_attention(self) -> None:
        results = MODULE.evaluate(
            registry(),
            {"schema_version": 1, "sources": {}},
            today=date(2026, 7, 18),
            network=True,
            fetcher=fetcher(b"<html><body>Testgesetz</body></html>"),
        )
        self.assertTrue(results[0]["baseline_missing"])
        self.assertTrue(results[0]["attention"])

    def test_unchanged_fingerprint_passes(self) -> None:
        source_registry = registry()
        fetched = MODULE.FetchResult(
            b"<html><body>Testgesetz</body></html>",
            "text/html",
            "https://example.test/law",
            200,
        )
        source = source_registry["sources"][0]
        digest, _ = MODULE.fingerprint(source, fetched)
        baseline = {
            "schema_version": 1,
            "sources": {
                "test-law": {
                    "sha256": digest,
                    "approved_on": "2026-07-18",
                    "approved_by": "Test Review",
                }
            },
        }
        results = MODULE.evaluate(
            source_registry,
            baseline,
            today=date(2026, 7, 18),
            network=True,
            fetcher=fetcher(fetched.body),
        )
        self.assertFalse(results[0]["attention"])

    def test_changed_content_and_overdue_review_are_detected(self) -> None:
        baseline = {
            "schema_version": 1,
            "sources": {
                "test-law": {
                    "sha256": "0" * 64,
                    "approved_on": "2026-01-01",
                    "approved_by": "Test Review",
                }
            },
        }
        results = MODULE.evaluate(
            registry(last_reviewed_on="2026-01-01"),
            baseline,
            today=date(2026, 7, 18),
            network=True,
            fetcher=fetcher(b"<html><body>Testgesetz geaendert</body></html>"),
        )
        self.assertTrue(results[0]["changed"])
        self.assertTrue(results[0]["review_overdue"])

    def test_missing_marker_is_detected(self) -> None:
        results = MODULE.evaluate(
            registry(),
            {"schema_version": 1, "sources": {}},
            today=date(2026, 7, 18),
            network=True,
            fetcher=fetcher(b"<html><body>Andere Seite</body></html>"),
        )
        self.assertEqual(results[0]["markers_missing"], ["Testgesetz"])


if __name__ == "__main__":
    unittest.main()
