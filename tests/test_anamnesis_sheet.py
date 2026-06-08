import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from utils.anamnesis_sheet import (  # noqa: E402
    AnamnesisLookupError,
    NO_ANAMNESIS_FOUND_MESSAGE,
    UNAVAILABLE_ANAMNESIS_MESSAGE,
    build_anamnesis_section_tables,
    build_report_anamnesis_rows,
    build_question_answer_rows,
    format_candidate_label,
    get_configured_anamnesis_access_secret,
    is_anamnesis_access_authorized,
    load_anamnesis_lookup,
    resolve_patient_name_column,
    resolve_report_patient_name,
    search_anamnesis_candidates,
)


class AnamnesisSheetTests(unittest.TestCase):
    def test_get_configured_anamnesis_access_secret_defaults_to_empty(self):
        self.assertEqual(get_configured_anamnesis_access_secret({}), "")
        self.assertEqual(get_configured_anamnesis_access_secret(None), "")

    def test_get_configured_anamnesis_access_secret_reads_and_trims_secret(self):
        self.assertEqual(
            get_configured_anamnesis_access_secret(
                {"anamnesis_access_secret": "  senha-clinica  "}
            ),
            "senha-clinica",
        )

    def test_anamnesis_access_requires_matching_submitted_secret(self):
        config = {"anamnesis_access_secret": "senha-clinica"}

        self.assertTrue(is_anamnesis_access_authorized(config, "senha-clinica"))
        self.assertFalse(is_anamnesis_access_authorized(config, "senha-errada"))
        self.assertFalse(is_anamnesis_access_authorized(config, ""))
        self.assertFalse(is_anamnesis_access_authorized({}, "senha-clinica"))

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

    def test_build_anamnesis_section_tables_filters_and_renames_questions(self):
        sections = build_anamnesis_section_tables(
            {
                " idade ": " 34 ",
                "CPF": "123",
                "Pergunta sem mapeamento": "Nao deve aparecer",
                "Qual a sua queixa principal? O que você percebeu de diferente ou que tem te incomodado?": "Cansaço",
            }
        )

        self.assertEqual(
            sections["dados_pessoais"][:3],
            [
                {"Campo": "Idade", "Resposta": "34"},
                {"Campo": "Data de nasc.", "Resposta": "--"},
                {"Campo": "CPF", "Resposta": "123"},
            ],
        )
        self.assertEqual(
            sections["indicadores_do_historico_de_saude"][0],
            {"Campo": "Queixa Principal", "Resposta": "Cansaço"},
        )

    def test_build_anamnesis_section_tables_accepts_sheet_header_variations(self):
        sections = build_anamnesis_section_tables(
            {
                "CPF.": "123",
                "Tipo Sanguineo.": "AB +",
                "Celular de uma pessoa  próxima (nome e parentesco).": "Mae 9999",
                "Conte um pouco sobre seu histórico médico? (Condições crônicas ou recorrentes; alergias; infecções relevantes; tratamentos contínuos; internações significativas.)\n": "Alergia",
                "Vacinas  recentes (menos de 6 anos)  que tomou:  (Marque todas as que se aplicam) ": "Febre amarela",
            }
        )

        self.assertIn(
            {"Campo": "CPF", "Resposta": "123"},
            sections["dados_pessoais"],
        )
        self.assertIn(
            {"Campo": "Tipo Sanguíneo", "Resposta": "AB +"},
            sections["dados_pessoais"],
        )
        self.assertIn(
            {"Campo": "Contato de emergência", "Resposta": "Mae 9999"},
            sections["dados_pessoais"],
        )
        self.assertIn(
            {"Campo": "Histórico médico", "Resposta": "Alergia"},
            sections["indicadores_do_historico_de_saude"],
        )
        self.assertIn(
            {"Campo": "Vacinas", "Resposta": "Febre amarela"},
            sections["indicadores_do_historico_de_saude"],
        )

    def test_build_anamnesis_section_tables_joins_duplicate_output_fields(self):
        sections = build_anamnesis_section_tables(
            {
                "Histórico familiar de doenças do lado paterno: doenças crônicas ou condições de saúde significativas, como diabetes, hipertensão, câncer, doenças cardíacas etc., que afetem ou tenham afetado pai, avós, tios e primos de primeiro grau.": "Diabetes",
                "Histórico familiar de doenças do lado paterno: no caso de câncer, indique o tipo.": "Pulmão",
                "Mora em edifício? Se sim, em que andar?": "Sim, 4o andar",
                "Mora perto de canais, rios ou mangues?": "Perto de canal",
            }
        )

        self.assertEqual(
            sections["indicadores_do_historico_de_saude"][2],
            {"Campo": "Histórico familiar (paterno)", "Resposta": "Diabetes; Pulmão"},
        )
        self.assertEqual(
            sections["indicadores_do_historico_de_saude"][-2],
            {
                "Campo": "Fatores ambientais",
                "Resposta": "Sim, 4o andar; Perto de canal",
            },
        )

    def test_build_question_answer_rows_returns_flattened_mapped_rows(self):
        rows = build_question_answer_rows({"Idade": "34"})

        self.assertEqual(
            rows[:2],
            [
                {"Pergunta": "Idade", "Resposta": "34"},
                {"Pergunta": "Data de nasc.", "Resposta": "--"},
            ],
        )

    def test_report_anamnesis_rows_are_empty_without_access(self):
        selected_rows = {"dados_pessoais": [{"Campo": "Idade", "Resposta": "34"}]}

        rows = build_report_anamnesis_rows(False, selected_rows)

        self.assertEqual(rows, {})

    def test_report_anamnesis_rows_are_available_with_access(self):
        selected_rows = {
            "dados_pessoais": [{"Campo": "Idade", "Resposta": "34"}],
            "indicadores_do_historico_de_saude": [
                {"Campo": "Histórico médico", "Resposta": "--"}
            ],
        }

        rows = build_report_anamnesis_rows(True, selected_rows)

        self.assertEqual(
            rows,
            {
                "dados_pessoais": [{"campo": "Idade", "resposta": "34"}],
                "indicadores_do_historico_de_saude": [
                    {"campo": "Histórico médico", "resposta": "--"}
                ],
            },
        )

    def test_report_patient_name_uses_typed_name_without_anamnesis_access(self):
        lookup_state = {
            "status": "ready",
            "candidates": [{"patient_name": "Nome da Anamnese"}],
        }

        patient_name = resolve_report_patient_name(
            "Nome Digitado",
            False,
            lookup_state,
            0,
        )

        self.assertEqual(patient_name, "Nome Digitado")

    def test_report_patient_name_uses_selected_anamnesis_candidate_name(self):
        lookup_state = {
            "status": "ready",
            "candidates": [
                {"patient_name": "Primeira Pessoa"},
                {"patient_name": " Nome da Anamnese  "},
            ],
        }

        patient_name = resolve_report_patient_name(
            "Nome Digitado",
            True,
            lookup_state,
            1,
        )

        self.assertEqual(patient_name, "Nome da Anamnese")

    def test_report_patient_name_falls_back_to_typed_name_without_valid_candidate(self):
        lookup_state = {
            "status": "not_found",
            "candidates": [{"patient_name": "Nome da Anamnese"}],
        }

        patient_name = resolve_report_patient_name(
            "Nome Digitado",
            True,
            lookup_state,
            0,
        )

        self.assertEqual(patient_name, "Nome Digitado")

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
