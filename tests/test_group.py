import sys
import types
import unittest
from pathlib import Path

# Defensive stubs (group.py is dependency-free, but other modules in src may not
# be imported transitively; keep parity with the rest of the suite).
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

from utils.group import (  # noqa: E402
    GroupPartition,
    build_individual_content,
    build_individual_report_content,
    build_shared_content,
    extract_category_elements,
    format_shared_name,
    normalize_name,
    partition_group_elements,
)


def _row(nome, tipo="Parasitas", sintomas="", d="180"):
    return {"nome": nome, "tipo": tipo, "sintomas": sintomas, "D": d}


def _tox(nome, d="180"):
    return {"nome": nome, "D": d}


class NormalizeNameTests(unittest.TestCase):
    def test_lowercases_and_collapses_whitespace(self):
        self.assertEqual(normalize_name("E.  Coli"), "e. coli")
        self.assertEqual(normalize_name("  Taenia   Geral  "), "taenia geral")
        self.assertEqual(normalize_name("E. Coli"), normalize_name("e.  coli"))

    def test_handles_none_and_empty(self):
        self.assertEqual(normalize_name(None), "")
        self.assertEqual(normalize_name(""), "")


class ExtractCategoryElementsTests(unittest.TestCase):
    def test_unifies_prosync_and_oberon_deduped_first_wins(self):
        content = {
            "table_prosync": [_row("E. Coli", d="333")],
            "table_microorganism": [_row("e.  coli", d="786"), _row("Giardia")],
        }
        rows = extract_category_elements(content, "microorganisms")
        names = [r["nome"] for r in rows]
        self.assertEqual(names, ["E. Coli", "Giardia"])
        # First occurrence wins -> the prosync row (D=333).
        self.assertEqual(rows[0]["D"], "333")

    def test_skips_rows_with_missing_or_empty_name(self):
        content = {
            "table_toxins": [_tox(""), _tox(None), _tox("Chumbo")],
        }
        rows = extract_category_elements(content, "toxins")
        self.assertEqual([r["nome"] for r in rows], ["Chumbo"])


class PartitionGroupElementsTests(unittest.TestCase):
    def test_element_in_all_patients_is_common_across_origins(self):
        # "E. Coli" present in all 3 patients, but from different origins / spellings.
        p1 = {
            "table_prosync": [_row("E. Coli")],
            "table_microorganism": [_row("Giardia")],
            "table_toxins": [_tox("Chumbo")],
        }
        p2 = {
            "table_prosync": [],
            "table_microorganism": [_row("e.  coli")],
            "table_toxins": [_tox("Chumbo")],
        }
        p3 = {
            "table_prosync": [_row("E.   COLI")],
            "table_microorganism": [],
            "table_toxins": [_tox("chumbo")],
        }
        part = partition_group_elements([p1, p2, p3])
        self.assertIsInstance(part, GroupPartition)
        common_micro = [r["nome"] for r in part.common_elements["microorganisms"]]
        self.assertEqual(common_micro, ["E. Coli"])
        common_tox = [r["nome"] for r in part.common_elements["toxins"]]
        self.assertEqual(common_tox, ["Chumbo"])

    def test_common_representative_comes_from_first_patient(self):
        rep_row = _row("E. Coli", d="111")
        p1 = {"table_prosync": [rep_row], "table_microorganism": [], "table_toxins": []}
        p2 = {
            "table_prosync": [],
            "table_microorganism": [_row("e. coli", d="999")],
            "table_toxins": [],
        }
        part = partition_group_elements([p1, p2])
        common = part.common_elements["microorganisms"]
        self.assertEqual(len(common), 1)
        # Representative is the exact first-patient row (identity + fields).
        self.assertIs(common[0], rep_row)
        self.assertEqual(common[0]["D"], "111")

    def test_element_in_only_some_patients_is_not_common(self):
        # Giardia only in 2 of 3 patients -> NOT common (INV-04); appears in unique.
        p1 = {
            "table_prosync": [_row("Giardia"), _row("E. Coli")],
            "table_microorganism": [],
            "table_toxins": [],
        }
        p2 = {
            "table_prosync": [_row("Giardia"), _row("E. Coli")],
            "table_microorganism": [],
            "table_toxins": [],
        }
        p3 = {
            "table_prosync": [_row("E. Coli")],
            "table_microorganism": [],
            "table_toxins": [],
        }
        part = partition_group_elements([p1, p2, p3])
        common = [r["nome"] for r in part.common_elements["microorganisms"]]
        self.assertEqual(common, ["E. Coli"])
        self.assertNotIn("Giardia", common)
        # Giardia appears in the unique sets of the patients that have it.
        self.assertEqual(
            [r["nome"] for r in part.per_patient_unique[0]["microorganisms"]],
            ["Giardia"],
        )
        self.assertEqual(
            [r["nome"] for r in part.per_patient_unique[1]["microorganisms"]],
            ["Giardia"],
        )
        self.assertEqual(
            [r["nome"] for r in part.per_patient_unique[2]["microorganisms"]],
            [],
        )

    def test_unique_remainder_excludes_common_and_is_deduped(self):
        p1 = {
            "table_prosync": [_row("E. Coli"), _row("Salmonella")],
            "table_microorganism": [_row("e. coli"), _row("salmonella")],
            "table_toxins": [],
        }
        p2 = {
            "table_prosync": [_row("E. Coli")],
            "table_microorganism": [],
            "table_toxins": [],
        }
        part = partition_group_elements([p1, p2])
        unique_p1 = [r["nome"] for r in part.per_patient_unique[0]["microorganisms"]]
        # E. Coli is common -> excluded; Salmonella deduped to a single entry.
        self.assertEqual(unique_p1, ["Salmonella"])

    def test_empty_group_returns_empty_common(self):
        part = partition_group_elements([])
        self.assertEqual(part.common_elements["microorganisms"], [])
        self.assertEqual(part.common_elements["toxins"], [])
        self.assertEqual(part.per_patient_unique, [])

    def test_no_common_case_returns_empty_common_lists(self):
        p1 = {"table_prosync": [_row("Giardia")], "table_microorganism": [], "table_toxins": []}
        p2 = {"table_prosync": [_row("E. Coli")], "table_microorganism": [], "table_toxins": []}
        part = partition_group_elements([p1, p2])
        self.assertEqual(part.common_elements["microorganisms"], [])
        self.assertEqual(part.common_elements["toxins"], [])

    def test_failed_patient_none_is_tolerated(self):
        # A patient that failed processing is passed as None; the partition must
        # not crash and that slot's unique remainder is empty (RF-12). With a
        # missing patient nothing can be common to ALL patients.
        p1 = {"table_prosync": [_row("Giardia")], "table_microorganism": [], "table_toxins": []}
        part = partition_group_elements([p1, None])
        self.assertEqual(part.common_elements["microorganisms"], [])
        self.assertEqual(len(part.per_patient_unique), 2)
        self.assertEqual(part.per_patient_unique[1]["microorganisms"], [])
        self.assertEqual(
            [r["nome"] for r in part.per_patient_unique[0]["microorganisms"]],
            ["Giardia"],
        )


class BuildContentTests(unittest.TestCase):
    def test_format_shared_name(self):
        self.assertEqual(
            format_shared_name(["Ana", "Bruno", "Carla"]),
            "Compartilhado: Ana, Bruno, Carla",
        )
        # Blanks are stripped out.
        self.assertEqual(
            format_shared_name(["Ana", "", "  ", "Carla"]),
            "Compartilhado: Ana, Carla",
        )

    def test_build_shared_content_maps_keys_and_has_no_extra_sessions(self):
        common = {
            "microorganisms": [_row("E. Coli")],
            "toxins": [_tox("Chumbo")],
        }
        content = build_shared_content(common, ["Ana", "Bruno"])
        self.assertEqual(content["name"], "Compartilhado: Ana, Bruno")
        self.assertEqual(content["table_microorganism"], [_row("E. Coli")])
        self.assertEqual(content["table_prosync"], [])
        self.assertEqual(content["table_toxins"], [_tox("Chumbo")])
        self.assertEqual(content["extra_sessions"], [])
        self.assertEqual(content["extra_session_prices"], {})

    def test_build_shared_content_tolerates_missing_categories(self):
        content = build_shared_content({}, ["Ana"])
        self.assertEqual(content["table_microorganism"], [])
        self.assertEqual(content["table_toxins"], [])

    def test_build_individual_content(self):
        unique = {
            "microorganisms": [_row("Giardia")],
            "toxins": [_tox("Mercurio")],
        }
        content = build_individual_content(
            unique,
            extra_sessions=["Calatonia"],
            patient_name="Ana",
            extra_session_prices={"Calatonia": {"pix": 1.0}},
        )
        self.assertEqual(content["name"], "Ana")
        self.assertEqual(content["table_microorganism"], [_row("Giardia")])
        self.assertEqual(content["table_prosync"], [])
        self.assertEqual(content["table_toxins"], [_tox("Mercurio")])
        self.assertEqual(content["extra_sessions"], ["Calatonia"])
        self.assertEqual(content["extra_session_prices"], {"Calatonia": {"pix": 1.0}})

    def test_build_individual_content_defaults(self):
        content = build_individual_content({}, [], "Ana")
        self.assertEqual(content["extra_sessions"], [])
        self.assertEqual(content["extra_session_prices"], {})
        self.assertEqual(content["table_microorganism"], [])

    def test_build_individual_report_content(self):
        other = {
            "table_crystals": [{"nome": "Quartzo"}],
            "table_food": ["Banana"],
            "table_emotions": {"raiva": 1},
            "table_patologies": {"x": 1},
        }
        content = build_individual_report_content(
            unique_micro=[_row("Giardia")],
            unique_toxins=[_tox("Mercurio")],
            other_categories=other,
            patient_name="Ana",
        )
        self.assertEqual(content["name"], "Ana")
        self.assertEqual(content["table_microorganism"], [_row("Giardia")])
        self.assertEqual(content["table_prosync"], [])
        self.assertEqual(content["table_toxins"], [_tox("Mercurio")])
        self.assertEqual(content["table_crystals"], [{"nome": "Quartzo"}])
        self.assertEqual(content["table_food"], ["Banana"])
        self.assertEqual(content["table_emotions"], {"raiva": 1})
        self.assertEqual(content["table_patologies"], {"x": 1})
        self.assertIn("date", content)


if __name__ == "__main__":
    unittest.main()
