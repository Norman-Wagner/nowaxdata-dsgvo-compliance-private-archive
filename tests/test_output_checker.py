from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "skills" / "pruefe-de-datenschutz" / "scripts" / "check_legal_output.py"
SPEC = importlib.util.spec_from_file_location("check_legal_output", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


VALID = """# Kurzfazit

Vorläufig tragfähig.

# Sachverhalt

Ein Verantwortlicher plant eine Verarbeitung.

# Rechtsprüfung

Belegt ist der Maßstab aus Art. 6 DSGVO. Die Bewertung hängt vom Zweck ab.
[DSGVO bei EUR-Lex](https://eur-lex.europa.eu/eli/reg/2016/679/oj/deu)

# Maßnahmen

Den Zweck dokumentieren.

# Offene Punkte

Die Speicherdauer ist offen.

# Quellen und Stand

Stand: 2026-07-18.
"""


class OutputCheckerTests(unittest.TestCase):
    def test_valid_structure_passes(self) -> None:
        errors, warnings = MODULE.check(VALID)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_overclaim_fails(self) -> None:
        errors, _ = MODULE.check(VALID + "\nDas ist garantiert rechtssicher.\n")
        self.assertTrue(any("Sicherheitsversprechen" in item for item in errors))

    def test_secondary_source_alone_fails(self) -> None:
        text = VALID.replace(
            "[DSGVO bei EUR-Lex](https://eur-lex.europa.eu/eli/reg/2016/679/oj/deu)",
            "[DSGVO](https://dsgvo-gesetz.de/)",
        )
        errors, _ = MODULE.check(text)
        self.assertTrue(any("amtliche" in item or "Gegenquelle" in item for item in errors))

    def test_iso_date_is_not_a_phone_warning(self) -> None:
        _, warnings = MODULE.check(VALID)
        self.assertFalse(any("Telefonnummer" in item for item in warnings))


if __name__ == "__main__":
    unittest.main()
