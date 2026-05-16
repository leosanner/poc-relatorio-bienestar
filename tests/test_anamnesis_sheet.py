import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from utils.anamnesis_sheet import (  # noqa: E402
    AnamnesisLookupError,
    NO_ANAMNESIS_FOUND_MESSAGE,
    UNAVAILABLE_ANAMNESIS_MESSAGE,
    build_question_answer_rows,
    format_candidate_label,
    load_anamnesis_lookup,
    resolve_patient_name_column,
    search_anamnesis_candidates,
)


class AnamnesisSheetTests(unittest.TestCase):
    def test_resolve_patient_name_column_uses_configured_header(self):
        records = [{" Nome Completo ": "Ana Silva", "Outro": "valor"}]

        name_column = resolve_patient_name_column(
            records,
            configured_name_column="nome completo",
        )

        self.assertEqual(name_column, " Nome Completo ")

    def test_resolve_patient_name_column_uses_supported_alias(self):
        records = [{"Carimbo de data/hora": "2026-05-10", "Nome do Paciente": "Ana"}]

        name_column = resolve_patient_name_column(records)

        self.assertEqual(name_column, "Nome do Paciente")

    def test_resolve_patient_name_column_rejects_unknown_header(self):
        with self.assertRaises(AnamnesisLookupError):
            resolve_patient_name_column([{"Responsavel": "Ana"}])

    def test_search_accepts_case_whitespace_and_partial_matches(self):
        records = [
            {
                "Nome": "  Maria   Clara  Souza ",
                "Carimbo de data/hora": "2026-05-10 09:00",
                "Endereço de e-mail": "maria@example.com",
            },
            {"Nome": "Joao Silva", "Carimbo de data/hora": "2026-05-11 10:00"},
        ]

        candidates = search_anamnesis_candidates(records, "maria clara", "Nome")

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["patient_name"], "Maria Clara Souza")
        self.assertEqual(candidates[0]["timestamp"], "2026-05-10 09:00")
        self.assertEqual(candidates[0]["email"], "maria@example.com")

    def test_search_returns_duplicate_candidates_for_staff_selection(self):
        records = [
            {"Nome": "Ana Lima", "Timestamp": "2026-05-10"},
            {"Nome": "Ana Lima", "Timestamp": "2026-05-12"},
        ]

        candidates = search_anamnesis_candidates(records, "ana", "Nome")

        self.assertEqual(len(candidates), 2)
        self.assertEqual([candidate["record_index"] for candidate in candidates], [0, 1])
        self.assertEqual(format_candidate_label(candidates[1]), "Ana Lima | 2026-05-12")

    def test_build_question_answer_rows_keeps_all_record_columns(self):
        rows = build_question_answer_rows(
            {
                "Nome": "Ana",
                "Sintoma principal": "Dor",
                "Observacao": None,
            }
        )

        self.assertEqual(
            rows,
            [
                {"Pergunta": "Nome", "Resposta": "Ana"},
                {"Pergunta": "Sintoma principal", "Resposta": "Dor"},
                {"Pergunta": "Observacao", "Resposta": ""},
            ],
        )

    def test_lookup_returns_no_result_state_without_treating_it_as_error(self):
        result = load_anamnesis_lookup(
            clinic_name="Bienestar",
            search_term="Carlos",
            spreadsheet_id="sheet-id",
            worksheet_name="Respostas",
            service_account_info={"client_email": "test@example.com"},
            remote_loader=lambda *_args: [{"Nome": "Ana Lima"}],
        )

        self.assertEqual(result["status"], "not_found")
        self.assertEqual(result["message"], NO_ANAMNESIS_FOUND_MESSAGE)
        self.assertEqual(result["candidates"], [])

    def test_lookup_returns_sanitized_unavailable_state_on_technical_failure(self):
        def failing_loader(*_args):
            raise RuntimeError("private_key=SECRET stack trace from sdk")

        result = load_anamnesis_lookup(
            clinic_name="Bienestar",
            search_term="Ana",
            spreadsheet_id="sheet-id",
            worksheet_name="Respostas",
            service_account_info={"private_key": "SECRET"},
            remote_loader=failing_loader,
        )

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["message"], UNAVAILABLE_ANAMNESIS_MESSAGE)
        self.assertNotIn("SECRET", result["message"])
        self.assertNotIn("private_key", result["message"])

    def test_lookup_marks_unsupported_clinic_unavailable_without_remote_call(self):
        calls = []

        result = load_anamnesis_lookup(
            clinic_name="Alecrim",
            search_term="Ana",
            spreadsheet_id="sheet-id",
            worksheet_name="Respostas",
            service_account_info={"client_email": "test@example.com"},
            remote_loader=lambda *_args: calls.append(True),
        )

        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
