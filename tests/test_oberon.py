import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from utils.oberon import food_info, patologies_info  # noqa: E402


class OberonPathologiesTests(unittest.TestCase):
    def test_patologies_info_applies_match_before_return(self):
        result = patologies_info({"neurastenia": "0.222"})
        expected_name = (
            "Desequilíbrio na regulação neurovascular, que pode estar associado a "
            "variações na circulação."
        )

        self.assertEqual(result, {expected_name: "0.222"})
        self.assertNotIn("Neurastenia", result)

    def test_patologies_info_matches_json_keys_case_insensitively(self):
        result = patologies_info({"gastrite atrófica": "0.341"})
        expected_name = (
            "Desequilíbrio do sistema digestório (estômago, duodeno, pâncreas, "
            "intestino e reto)."
        )

        self.assertEqual(result, {expected_name: "0.341"})

    def test_patologies_info_keeps_unmatched_non_stopword(self):
        result = patologies_info({"condição nova": "0.111"})

        self.assertEqual(result, {"Condição nova": "0.111"})


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
