from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "check_repository_privacy.py"
SPEC = importlib.util.spec_from_file_location("check_repository_privacy", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class RepositoryPrivacyTests(unittest.TestCase):
    def scan(self, content: str):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.txt"
            path.write_text(content, encoding="utf-8")
            return MODULE.scan_file(path)

    def test_harmless_project_text_passes(self) -> None:
        findings = self.scan("Stand: 2026-07-18\nQuelle: https://eur-lex.europa.eu/\n")
        self.assertEqual(findings, [])

    def test_email_and_phone_are_detected(self) -> None:
        email = "anna" + "@" + "example.org"
        phone = "+49" + " 30 12345678"
        codes = {item.code for item in self.scan(f"Kontakt: {email}\nTelefon: {phone}\n")}
        self.assertIn("PERSON_EMAIL", codes)
        self.assertIn("PERSON_PHONE_INTL", codes)

    def test_common_secret_is_detected(self) -> None:
        token = "gh" + "p_" + "A" * 40
        codes = {item.code for item in self.scan("Token: " + token)}
        self.assertIn("SECRET_GITHUB_TOKEN", codes)

    def test_iban_and_payment_card_are_detected(self) -> None:
        iban = "DE" + "".join(("89", " 3704", " 0044", " 0532", " 0130", " 00"))
        card = "4111" + " 1111 1111 1111"
        codes = {item.code for item in self.scan(f"IBAN: {iban}\nKarte: {card}\n")}
        self.assertIn("PERSON_IBAN", codes)
        self.assertIn("PERSON_PAYMENT_CARD", codes)

    def test_reviewed_public_value_can_be_allowed_per_line(self) -> None:
        email = "public" + "@" + "example.org"
        findings = self.scan(f"Kontakt: {email}  # privacy-scan: allow(öffentlicher Projektkontakt)\n")
        self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()
