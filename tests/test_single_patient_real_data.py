"""Integration tests for the single-patient flow using REAL Oberon TXT data.

These exercise the same pipeline the Streamlit single-patient tab runs:
    extract_oberon_content -> <category>_info -> generate_content_for_report
    -> build_protocol_context / build_budget_context / build_control_context

The real input files live under ``tests/data/p1/`` (git-ignored). When that data
is absent (e.g. CI / a fresh clone) every test here is skipped, so the suite
stays green without the private patient data.

Only the *.docx rendering step needs the real ``docxtpl`` library; everything
asserted here builds plain context dicts, so the suite-wide docxtpl/pandas/spacy
stubs (mirrored below) do not interfere.
"""

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

from utils.oberon import (  # noqa: E402
    crystal_info,
    emotions_info,
    extract_oberon_content,
    food_info,
    microorganism_info,
    patologies_info,
    toxins_info,
)
from utils.report import generate_content_for_report  # noqa: E402
from utils.protocol import build_protocol_context  # noqa: E402
from utils.budget import build_budget_context  # noqa: E402
from utils.control import build_control_context, CONTROL_DYNAMIC_START_WEEK  # noqa: E402

DATA_DIR = Path(__file__).resolve().parent / "data" / "p1"

# Same encodings the app tries, in order, before giving up on a TXT.
ENCODINGS = ["cp1252", "utf-8", "latin1", "iso-8859-1", "utf-8-sig"]

# Map each TXT file name (component-only) to its app category key + processor.
OBERON_FILES = {
    "toxinas": ("toxinas.txt", toxins_info),
    "microrganismos": ("microorganismos.txt", microorganism_info),
    "cristais": ("pedras.txt", crystal_info),
    "alimentos": ("alimentos.txt", food_info),
    "emocoes": ("emocoes.txt", emotions_info),
    "patologias": ("patologias.txt", patologies_info),
}


def _read_oberon(path: Path) -> dict:
    """Encoding-tolerant read mirroring the app's per-file loop."""
    for enc in ENCODINGS:
        try:
            content = extract_oberon_content(str(path), enc=enc)
            if len(content) > 0:
                return content
        except Exception:
            continue
    return {}


def load_patient_oberon_content(folder: Path):
    """Process a patient folder of Oberon TXTs into the ``selected_oberon_data``
    + ``oberon_thresholds`` shapes ``generate_content_for_report`` expects.

    Thresholds default to ``[0.0, 1.0]`` (the app's defaults), so every parsed
    row is kept — matching a run where staff selected all rows.
    """
    oberon_data = {}
    thresholds = {}
    for category, (file_name, processor) in OBERON_FILES.items():
        path = folder / file_name
        if not path.exists():
            continue
        raw = _read_oberon(path)
        oberon_data[category] = processor(raw)
        thresholds[category] = [0.0, 1.0]
    return oberon_data, thresholds


@unittest.skipUnless(
    DATA_DIR.is_dir(), f"real patient data not present at {DATA_DIR}"
)
class SinglePatientRealDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        oberon_data, thresholds = load_patient_oberon_content(DATA_DIR)
        cls.oberon_data = oberon_data
        cls.content = generate_content_for_report(
            [], oberon_data, thresholds, "Paciente 1"
        )
        cls.content["extra_sessions"] = []
        cls.content["extra_session_prices"] = {}

    # --- extraction / content-dict assembly ---

    def test_oberon_files_were_parsed(self):
        # microrganismos.txt is the richest file; it must parse to many rows.
        self.assertGreater(len(self.oberon_data["microrganismos"]), 50)
        self.assertGreater(len(self.oberon_data["toxinas"]), 0)
        self.assertGreater(len(self.oberon_data["cristais"]), 0)

    def test_content_dict_has_expected_shape(self):
        for key in (
            "name",
            "table_prosync",
            "table_toxins",
            "table_microorganism",
            "table_crystals",
            "table_food",
            "table_emotions",
            "table_patologies",
        ):
            self.assertIn(key, self.content)
        self.assertEqual(self.content["name"], "Paciente 1")
        self.assertEqual(self.content["table_prosync"], [])

    def test_microorganism_rows_have_name_and_type(self):
        micro = self.content["table_microorganism"]
        self.assertGreater(len(micro), 0)
        for row in micro:
            self.assertTrue(str(row.get("nome", "")).strip())
            self.assertIn("tipo", row)

    # --- protocol context on real data ---

    def test_build_protocol_context_runs_on_real_data(self):
        ctx = build_protocol_context(self.content)
        self.assertIsInstance(ctx["microorganisms_protocol"], list)
        self.assertIsInstance(ctx["metals_protocol"], list)
        self.assertGreater(
            len(ctx["microorganisms_protocol"]),
            0,
            "real microorganism data should yield treatment sessions",
        )
        self.assertTrue(ctx["total_pix"].startswith("R$"))
        self.assertTrue(ctx["total_card"].startswith("R$"))

    def test_protocol_row_numbering_starts_at_10(self):
        ctx = build_protocol_context(self.content)
        first_numbers = [
            int(row["number"]) for row in ctx["microorganisms_protocol"][:1]
        ]
        if first_numbers:
            self.assertEqual(first_numbers[0], 10)

    # --- budget context on real data ---

    def test_build_budget_context_runs_on_real_data(self):
        ctx = build_budget_context(self.content)
        self.assertIsInstance(ctx["microorganisms_budget"], list)
        self.assertGreater(len(ctx["microorganisms_budget"]), 0)
        for total_key in ("total_pix", "total_card", "treatments_total_pix"):
            self.assertTrue(ctx[total_key].startswith("R$"))

    # --- control context on real data ---

    def test_build_control_context_weeks_are_sequential_from_10(self):
        ctx = build_control_context(self.content)
        sessions = ctx["control"]
        self.assertGreater(len(sessions), 0)
        weeks = [s["week"] for s in sessions]
        self.assertEqual(weeks[0], CONTROL_DYNAMIC_START_WEEK)
        # weeks increment by 1 with no gaps
        self.assertEqual(weeks, list(range(weeks[0], weeks[0] + len(weeks))))


if __name__ == "__main__":
    unittest.main()
