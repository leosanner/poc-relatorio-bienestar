import sys
import types
import unittest
from pathlib import Path

if "docxtpl" not in sys.modules:
    fake_docxtpl = types.ModuleType("docxtpl")

    class DummyDocxTemplate:
        pass

    class DummyRichText:
        def __init__(self, text, color=None):
            self.text = text
            self.color = color

    fake_docxtpl.DocxTemplate = DummyDocxTemplate
    fake_docxtpl.RichText = DummyRichText
    sys.modules["docxtpl"] = fake_docxtpl

if "rich" not in sys.modules:
    fake_rich = types.ModuleType("rich")
    fake_rich.print = print
    sys.modules["rich"] = fake_rich

if "pandas" not in sys.modules:
    sys.modules["pandas"] = types.ModuleType("pandas")

if "spacy" not in sys.modules:
    sys.modules["spacy"] = types.ModuleType("spacy")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from utils.budget import build_budget_context  # noqa: E402


class BudgetTests(unittest.TestCase):
    def test_budget_uses_injected_extra_session_prices(self):
        protocol_content = {
            "name": "Paciente Teste",
            "table_prosync": [],
            "table_microorganism": [],
            "table_toxins": [],
            "extra_sessions": ["Sessao Especial", "Sessao Especial"],
            "extra_session_prices": {
                "Sessao Especial": {"pix": 111.0, "cartao": 222.0}
            },
        }

        budget_context = build_budget_context(protocol_content)

        self.assertEqual(
            budget_context["extra_sessions_budget"],
            [
                {
                    "name": "Sessao Especial",
                    "pix": "R$ 111,00",
                    "card": "R$ 222,00",
                    "number": "11",
                },
                {
                    "name": "Sessao Especial",
                    "pix": "R$ 111,00",
                    "card": "R$ 222,00",
                    "number": "12",
                },
            ],
        )
        self.assertEqual(budget_context["extra_sessions_total_pix"], "R$ 222,00")
        self.assertEqual(budget_context["extra_sessions_total_card"], "R$ 444,00")


if __name__ == "__main__":
    unittest.main()
