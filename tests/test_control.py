import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

if "docxtpl" not in sys.modules:
    fake_docxtpl = types.ModuleType("docxtpl")

    class DummyDocxTemplate:
        def __init__(self, path):
            self.path = path

        def render(self, content):
            self.content = content

        def save(self, buffer):
            buffer.write(b"docx")

    fake_docxtpl.DocxTemplate = DummyDocxTemplate
    sys.modules["docxtpl"] = fake_docxtpl

if "rich" not in sys.modules:
    fake_rich = types.ModuleType("rich")
    fake_rich.print = print
    sys.modules["rich"] = fake_rich

if "pandas" not in sys.modules:
    sys.modules["pandas"] = types.ModuleType("pandas")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from utils.control import (  # noqa: E402
    CONTROL_DATE_PLACEHOLDER,
    CONTROL_SIGNATURE_PLACEHOLDER,
    build_control_context,
)


class ControlTests(unittest.TestCase):
    def test_control_context_uses_budget_sessions_without_prices(self):
        budget_context = {
            "name": "Paciente Teste",
            "date": "12/06/2026",
            "microorganisms_budget": [
                {
                    "name": "RPD - Fungos",
                    "pix": "R$ 520,00",
                    "card": "R$ 620,00",
                    "h": "Hidrovitalis + Hidrogênio + ILIB",
                }
            ],
            "metals_budget": [
                {"name": "Detox metais", "pix": "R$ 520,00", "card": "R$ 620,00"}
            ],
            "extra_sessions_budget": [
                {"name": "Calatonia", "pix": "R$ 152,00", "card": "R$ 168,00"}
            ],
            "microorganisms_not_founded": ["Candida auris"],
            "metals_not_founded": ["Mercurio"],
        }

        with patch("utils.control.build_budget_context", return_value=budget_context):
            control_context = build_control_context({})

        self.assertEqual(control_context["name"], "Paciente Teste")
        self.assertEqual(control_context["date"], "12/06/2026")
        self.assertEqual(
            control_context["control"],
            [
                {
                    "week": 10,
                    "name": "RPD - Fungos",
                    "h": "Hidrovitalis + Hidrogênio + ILIB",
                    "date_placeholder": CONTROL_DATE_PLACEHOLDER,
                    "signature_placeholder": CONTROL_SIGNATURE_PLACEHOLDER,
                },
                {
                    "week": 11,
                    "name": "Detox metais",
                    "h": "",
                    "date_placeholder": CONTROL_DATE_PLACEHOLDER,
                    "signature_placeholder": CONTROL_SIGNATURE_PLACEHOLDER,
                },
                {
                    "week": 12,
                    "name": "Calatonia",
                    "h": "",
                    "date_placeholder": CONTROL_DATE_PLACEHOLDER,
                    "signature_placeholder": CONTROL_SIGNATURE_PLACEHOLDER,
                },
            ],
        )
        self.assertEqual(control_context["microorganisms_not_founded"], ["Candida auris"])
        self.assertEqual(control_context["metals_not_founded"], ["Mercurio"])


if __name__ == "__main__":
    unittest.main()
