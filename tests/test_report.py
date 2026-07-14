import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from utils.report import (  # noqa: E402
    format_food_table_to_docx_template,
    load_path_by_company,
)


class ReportTemplatePathTests(unittest.TestCase):
    def test_defaults_to_bienestar_oberon_template(self):
        template_path = load_path_by_company()

        self.assertEqual(template_path.name, "relatorio_bienestar_1.docx")

    def test_resolves_all_company_and_template_variant_combinations(self):
        expected_templates = {
            ("Bienestar", "Oberon"): "relatorio_bienestar_1.docx",
            ("Bienestar", "MetaHunter"): "relatorio_bienestar_metahunter.docx",
            ("Alecrim", "Oberon"): "relatorio_alecrim.docx",
            ("Alecrim", "MetaHunter"): "relatorio_alecrim_metahunter.docx",
            ("VitaeFlux", "Oberon"): "relatorio_vitaeflux.docx",
            ("VitaeFlux", "MetaHunter"): "relatorio_vitaeflux_metahunter.docx",
        }

        for combination, expected_file_name in expected_templates.items():
            with self.subTest(combination=combination):
                template_path = load_path_by_company(*combination)
                self.assertEqual(template_path.name, expected_file_name)
                self.assertTrue(template_path.exists())

    def test_rejects_unsupported_template_combination(self):
        with self.assertRaisesRegex(
            ValueError, "Unsupported report template combination"
        ):
            load_path_by_company("Unknown", "Oberon")


class ReportFoodTableTests(unittest.TestCase):
    def test_format_food_table_to_docx_template_outputs_four_food_pairs(self):
        result = format_food_table_to_docx_template(
            [
                {"Banana": "0.100", "Maca": "0.200"},
                {"Arroz": "0.500"},
                {"Leite": "0.800"},
                {"Amendoim": "1.200"},
            ]
        )

        self.assertEqual(
            result,
            [
                [
                    "Banana",
                    "0.100",
                    "Arroz",
                    "0.500",
                    "Leite",
                    "0.800",
                    "Amendoim",
                    "1.200",
                ],
                ["Maca", "0.200", " ", " ", " ", " ", " ", " "],
            ],
        )


if __name__ == "__main__":
    unittest.main()
