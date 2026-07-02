import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

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
from utils.protocol import (  # noqa: E402
    SESSION_COMPLEMENT_NAME,
    add_session_complements,
    build_protocol_context,
    format_microorganisms_to_docx,
    metals_docx_format,
    microorganisms_content_docx,
    microorganisms_frequencies,
    microorganisms_sessions,
    microorganisms_treatment_block,
)


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
                    "number": "10",
                },
                {
                    "name": "Sessao Especial",
                    "pix": "R$ 111,00",
                    "card": "R$ 222,00",
                    "number": "11",
                },
            ],
        )
        self.assertEqual(budget_context["extra_sessions_total_pix"], "R$ 222,00")
        self.assertEqual(budget_context["extra_sessions_total_card"], "R$ 444,00")

    def test_protocol_rows_include_rpd_header_and_complement(self):
        self.assertEqual(
            microorganisms_content_docx(
                [[["333", "180", "taenia geral", "Parasitas"]]]
            ),
            ["RPD - Parasitas\n# Taenia geral\n333,180"],
        )
        self.assertEqual(
            metals_docx_format([[["chumbo", "333", "180"]]]),
            ["RPD - Metais\n# Chumbo\n333, 180"],
        )
        self.assertEqual(
            add_session_complements(["RPD - Parasitas\n# Taenia geral\n333,180"]),
            ["RPD - Parasitas\n# Taenia geral\n333,180", SESSION_COMPLEMENT_NAME],
        )

    def test_budget_uses_rpd_headers_and_complement_prices(self):
        protocol_content = {
            "name": "Paciente Teste",
            "table_prosync": [],
            "table_microorganism": [],
            "table_toxins": [],
            "extra_sessions": [],
        }

        with patch(
            "utils.budget.microorganisms_treatment_block",
            return_value=(
                ["RPD - Parasitas\n# Taenia geral\n333,180\n# Enterococcus\n786,180"],
                [],
            ),
        ), patch(
            "utils.budget.metals_treatment_block",
            return_value=(["RPD - Metais\n# Chumbo\n333, 180"], []),
        ):
            budget_context = build_budget_context(protocol_content)

        self.assertEqual(
            budget_context["microorganisms_budget"],
            [
                {
                    "name": "RPD - Parasitas\n# Taenia geral\n# Enterococcus",
                    "pix": "R$ 153,00",
                    "card": "R$ 169,00",
                    "h": "Hidrovitalis + Hidrogênio + ILIB",
                    "h_p": "R$ 195,00",
                    "h_c": "R$ 215,00",
                    "number": "10",
                },
            ],
        )
        self.assertEqual(
            budget_context["metals_budget"],
            [
                {
                    "name": "RPD - Metais\n# Chumbo",
                    "pix": "R$ 153,00",
                    "card": "R$ 169,00",
                    "h": "Hidrovitalis + Hidrogênio + ILIB",
                    "h_p": "R$ 195,00",
                    "h_c": "R$ 215,00",
                    "number": "11",
                },
            ],
        )
        self.assertEqual(budget_context["treatments_total_pix"], "R$ 696,00")
        self.assertEqual(budget_context["treatments_total_card"], "R$ 768,00")

    def test_protocol_context_uses_budget_row_shape_with_frequencies(self):
        protocol_content = {
            "name": "Paciente Teste",
            "table_prosync": [],
            "table_microorganism": [],
            "table_toxins": [],
            "extra_sessions": ["Calatonia"],
        }

        with patch(
            "utils.protocol.microorganisms_treatment_block",
            return_value=(
                ["RPD - Parasitas\n# Taenia geral\n333,180\n# Enterococcus\n786,180"],
                [],
            ),
        ), patch(
            "utils.protocol.metals_treatment_block",
            return_value=(["RPD - Metais\n# Chumbo\n333, 180"], []),
        ):
            protocol_context = build_protocol_context(protocol_content)

        self.assertEqual(
            protocol_context["microorganisms_protocol"],
            [
                {
                    "name": "RPD - Parasitas\n# Taenia geral\n333,180\n# Enterococcus\n786,180",
                    "pix": "R$ 153,00",
                    "card": "R$ 169,00",
                    "h": "Hidrovitalis + Hidrogênio + ILIB",
                    "h_p": "R$ 195,00",
                    "h_c": "R$ 215,00",
                    "display": (
                        "RPD - Parasitas\n# Taenia geral\n333,180\n"
                        "# Enterococcus\n786,180\n"
                        "Hidrovitalis + Hidrogênio + ILIB"
                    ),
                    "number": "10",
                },
            ],
        )
        self.assertEqual(
            protocol_context["metals_protocol"],
            [
                {
                    "name": "RPD - Metais\n# Chumbo\n333, 180",
                    "pix": "R$ 153,00",
                    "card": "R$ 169,00",
                    "h": "Hidrovitalis + Hidrogênio + ILIB",
                    "h_p": "R$ 195,00",
                    "h_c": "R$ 215,00",
                    "display": (
                        "RPD - Metais\n# Chumbo\n333, 180\n"
                        "Hidrovitalis + Hidrogênio + ILIB"
                    ),
                    "number": "11",
                },
            ],
        )
        self.assertEqual(protocol_context["total_pix"], "R$ 696,00")
        self.assertEqual(protocol_context["total_card"], "R$ 768,00")

    def test_shared_frequency_keeps_both_microorganism_names(self):
        blocks, not_founded = microorganisms_treatment_block(
            [],
            [
                {"nome": "taenia saginata", "tipo": "Helminto"},
                {"nome": "taenia solium", "tipo": "Helminto"},
            ],
        )

        self.assertEqual(not_founded, [])
        self.assertEqual(len(blocks), 1)
        self.assertIn("# Taenia saginata", blocks[0])
        self.assertIn("# Taenia solium", blocks[0])
        self.assertEqual(blocks[0].count("#"), 2)

    def test_duplicate_microorganism_frequency_pair_is_still_deduped(self):
        protocol_data = {
            "Helminto": ["taenia saginata", "taenia saginata"],
        }
        sessions = microorganisms_sessions(microorganisms_frequencies(protocol_data)[0])
        blocks = format_microorganisms_to_docx(sessions)

        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].count("# Taenia saginata"), 1)


if __name__ == "__main__":
    unittest.main()
