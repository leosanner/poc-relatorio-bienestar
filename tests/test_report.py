import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from utils.report import format_food_table_to_docx_template  # noqa: E402


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
