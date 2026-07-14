import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from utils.oberon import food_info, patologies_info  # noqa: E402


class OberonPathologiesTests(unittest.TestCase):
    def test_patologies_info_formats_input_without_applying_match(self):
        result = patologies_info({"  GASTRITE ATRÓFICA  ": "0.341"})

        self.assertEqual(result, {"Gastrite atrófica": "0.341"})

    def test_patologies_info_keeps_input_previously_listed_as_stopword(self):
        result = patologies_info(
            {
                "  NEURASTENIA ": "0.222",
                "condição nova": "0.111",
            }
        )

        self.assertEqual(
            result,
            {
                "Condição nova": "0.111",
                "Neurastenia": "0.222",
            },
        )

    def test_patologies_info_orders_formatted_input_by_d_value(self):
        result = patologies_info(
            {
                "segunda condição": "0.341",
                "primeira condição": "0.111",
            }
        )

        self.assertEqual(
            list(result.items()),
            [
                ("Primeira condição", "0.111"),
                ("Segunda condição", "0.341"),
            ],
        )


class OberonFoodTests(unittest.TestCase):
    def test_food_info_splits_foods_into_four_compatibility_groups(self):
        result = food_info(
            {
                "altamente": "0.300",
                "compativel": "0.700",
                "pouco": "1.000",
                "incompativel": "1.001",
            }
        )

        self.assertEqual(
            result,
            [
                {"Altamente": "0.300"},
                {"Compativel": "0.700"},
                {"Pouco": "1.000"},
                {"Incompativel": "1.001"},
            ],
        )


if __name__ == "__main__":
    unittest.main()
