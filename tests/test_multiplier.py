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

from utils.budget import build_budget_context, format_currency  # noqa: E402
from utils.protocol import build_protocol_context  # noqa: E402


# "álcoois e solventes" is a real, non-excluded metal in
# src/assets/protocol/toxinas_manus.json, so a RPD - Metais treatment row is
# produced. Treatment unit price is "RPD" (pix 153 / cartao 169) plus the
# complement "Hidrovitalis + ILIB + Hidrogênio" (pix 195 / cartao 215).
RPD_PIX = 153.0
RPD_CARD = 169.0
COMPLEMENT_PIX = 195.0
COMPLEMENT_CARD = 215.0


def make_protocol_content():
    return {
        "name": "Paciente Teste",
        "table_prosync": [],
        "table_microorganism": [],
        "table_toxins": [{"nome": "álcoois e solventes"}],
        "extra_sessions": ["Calatonia"],
        "extra_session_prices": {
            "Calatonia": {"pix": 152.0, "cartao": 168.0},
        },
    }


class MultiplierTests(unittest.TestCase):
    def test_default_multiplier_is_noop(self):
        budget_default = build_budget_context(make_protocol_content())
        budget_explicit = build_budget_context(make_protocol_content(), 1.0)
        self.assertEqual(
            budget_default["treatments_total_pix"],
            budget_explicit["treatments_total_pix"],
        )
        self.assertEqual(
            budget_default["treatments_total_card"],
            budget_explicit["treatments_total_card"],
        )

        protocol_default = build_protocol_context(make_protocol_content())
        protocol_explicit = build_protocol_context(make_protocol_content(), 1.0)
        self.assertEqual(
            protocol_default["total_pix"], protocol_explicit["total_pix"]
        )
        self.assertEqual(
            protocol_default["total_card"], protocol_explicit["total_card"]
        )

    def test_multiplier_scales_treatment_totals(self):
        base_pix = RPD_PIX + COMPLEMENT_PIX
        base_card = RPD_CARD + COMPLEMENT_CARD

        budget = build_budget_context(make_protocol_content(), 2.0)
        self.assertEqual(
            budget["treatments_total_pix"], format_currency(base_pix * 2.0)
        )
        self.assertEqual(
            budget["treatments_total_card"], format_currency(base_card * 2.0)
        )

        protocol = build_protocol_context(make_protocol_content(), 2.0)
        self.assertEqual(protocol["total_pix"], format_currency(base_pix * 2.0))
        self.assertEqual(protocol["total_card"], format_currency(base_card * 2.0))

        # Exactly double the multiplier=1.0 values.
        budget_base = build_budget_context(make_protocol_content(), 1.0)
        self.assertEqual(
            budget["treatments_total_pix"], format_currency(base_pix * 2.0)
        )
        self.assertEqual(
            budget_base["treatments_total_pix"], format_currency(base_pix)
        )

    def test_extra_sessions_total_unaffected_by_multiplier(self):
        budget_1x = build_budget_context(make_protocol_content(), 1.0)
        budget_2x = build_budget_context(make_protocol_content(), 2.0)

        self.assertEqual(
            budget_1x["extra_sessions_total_pix"],
            budget_2x["extra_sessions_total_pix"],
        )
        self.assertEqual(
            budget_1x["extra_sessions_total_card"],
            budget_2x["extra_sessions_total_card"],
        )
        self.assertEqual(
            budget_1x["extra_sessions_total_pix"], format_currency(152.0)
        )


if __name__ == "__main__":
    unittest.main()
