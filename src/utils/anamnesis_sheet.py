import hmac
import re
import unicodedata
from collections.abc import Callable, Mapping
from typing import Any


ANAMNESIS_ACCESS_SECRET_KEY = "anamnesis_access_secret"
SUPPORTED_ANAMNESIS_CLINICS = ("Bienestar", "VitaeFlux")
NO_ANAMNESIS_FOUND_MESSAGE = (
    "Nenhuma anamnese encontrada para este paciente nesta clínica."
)
UNAVAILABLE_ANAMNESIS_MESSAGE = (
    "Nao foi possivel consultar a anamnese agora. "
    "Verifique a configuracao do Google Sheets e tente novamente."
)
MISSING_ANAMNESIS_ACCESS_SECRET_MESSAGE = (
    "Anamnese indisponível. Configure o secret de acesso para habilitar a consulta."
)
LOCKED_ANAMNESIS_MESSAGE = (
    "Informe o secret da anamnese para consultar os dados."
)
INVALID_ANAMNESIS_ACCESS_SECRET_MESSAGE = (
    "Secret da anamnese inválido."
)

PATIENT_NAME_ALIASES = (
    "nome do paciente",
    "nome paciente",
    "paciente",
    "nome",
    "nome completo",
    "nome completo do paciente",
    "qual o seu nome",
    "qual o nome do paciente",
)
TIMESTAMP_ALIASES = (
    "carimbo de data/hora",
    "timestamp",
    "data/hora",
    "data e hora",
    "data",
)
EMAIL_ALIASES = (
    "endereco de e-mail",
    "endereço de e-mail",
    "email",
    "e-mail",
)
ANAMNESIS_EMPTY_VALUE_PLACEHOLDER = "--"
ANAMNESIS_FIELD_COLUMN = "Campo"
ANAMNESIS_ANSWER_COLUMN = "Resposta"
ANAMNESIS_SECTION_LABELS = {
    "dados_pessoais": "Dados pessoais",
    "indicadores_do_historico_de_saude": "Indicadores do histórico de saúde",
}
ANAMNESIS_SECTION_QUESTION_MAPS = {
    "dados_pessoais": {
        "Idade": "Idade",
        "Data de nascimento": "Data de nasc.",
        "CPF": "CPF",
        "Sexo": "Sexo",
        "Tipo sanguíneo": "Tipo Sanguíneo",
        "Peso": "Peso",
        "Altura": "Altura",
        "Profissão": "Profissão",
        "Nome da mãe": "Nome da mãe",
        "Estado civil": "Estado civil",
        "Você possui filhos? Se sim, informar nome e idade de cada um.": "Filhos",
        "Celular": "Celular",
        "Celular de uma pessoa próxima, com nome e parentesco": (
            "Contato de emergência"
        ),
        "Celular de uma pessoa  próxima (nome e parentesco).": (
            "Contato de emergência"
        ),
        "E-mail": "Email",
    },
    "indicadores_do_historico_de_saude": {
        (
            "Qual a sua queixa principal? O que você percebeu de diferente ou que "
            "tem te incomodado?"
        ): "Queixa Principal",
        (
            "Conte um pouco sobre seu histórico médico: condições crônicas ou "
            "recorrentes, alergias, infecções relevantes, tratamentos contínuos e "
            "internações significativas."
        ): "Histórico médico",
        (
            "Conte um pouco sobre seu histórico médico? (Condições crônicas ou "
            "recorrentes; alergias; infecções relevantes; tratamentos contínuos; "
            "internações significativas.)"
        ): "Histórico médico",
        (
            "Histórico familiar de doenças do lado paterno: doenças crônicas ou "
            "condições de saúde significativas, como diabetes, hipertensão, câncer, "
            "doenças cardíacas etc., que afetem ou tenham afetado pai, avós, tios "
            "e primos de primeiro grau."
        ): "Histórico familiar (paterno)",
        (
            "Histórico familiar de doenças do lado paterno: Indique quaisquer "
            "doenças crônicas ou condições de saúde significativas (ex: diabetes, "
            "hipertensão, câncer, doenças cardíacas, etc.) que afetem ou tenham "
            "afetado membros da família (pai, avós, tios e primos de primeiro grau)."
        ): "Histórico familiar (paterno)",
        (
            "Histórico familiar de doenças do lado paterno: no caso de câncer, "
            "indique o tipo."
        ): "Histórico familiar (paterno)",
        (
            "Histórico familiar de doenças do lado materno: doenças crônicas ou "
            "condições de saúde significativas, como diabetes, hipertensão, câncer, "
            "doenças cardíacas etc., que afetem ou tenham afetado mãe, avós, tios "
            "e primos de primeiro grau."
        ): "Histórico familiar (materno)",
        (
            "Histórico familiar de doenças do lado materno: Indique quaisquer "
            "doenças crônicas ou condições de saúde significativas (ex: diabetes, "
            "hipertensão, câncer, doenças cardíacas, etc.) que afetem ou tenham "
            "afetado membros da família (pai, avós, tios e primos de primeiro grau)."
        ): "Histórico familiar (materno)",
        (
            "Histórico familiar de doenças do lado materno: no caso de câncer, "
            "indique o tipo."
        ): "Histórico familiar (materno)",
        "Faz algum tratamento atualmente? Se sim, qual?": "Tratamentos atuais",
        "Passou por cirurgias? Se sim, indique quais.": "Cirurgias",
        (
            "Avalie de 0 a 10 sua dor, sendo 0 nenhuma dor e 10 dor extremamente "
            "forte."
        ): "Escala de dor",
        (
            "Você tem algum desconforto, sintoma ou patologia ligado ao sistema "
            "tegumentar? Pele, unhas, cabelos, glândulas sudoríparas ou glândulas "
            "sebáceas."
        ): "Alterações - sistema tegumentar",
        (
            "Você tem algum desconforto, sintoma ou patologia ligado ao sistema "
            "tegumentar? (Pele; Unhas; Cabelos; Glândulas sudoríparas; Glândulas "
            "sebáceas)"
        ): "Alterações - sistema tegumentar",
        (
            "Você tem algum desconforto, sintoma ou patologia ligado ao sistema "
            "sensorial?"
        ): "Alterações - sistema sensorial",
        (
            "Você tem algum desconforto, sintoma ou patologia ligado ao sensorial?"
        ): "Alterações - sistema sensorial",
        (
            "Existem sensações ou pensamentos que te acompanham com frequência e "
            "que de alguma forma te incomodam ou te fazem sentir um peso? Se sim, "
            "marque todas as que se aplicam."
        ): "Fatores emocionais",
        "Mora em edifício? Se sim, em que andar?": "Fatores ambientais",
        "Mora perto de canais, rios ou mangues?": "Fatores ambientais",
        "Vacinas recentes, tomadas há menos de 6 anos.": "Vacinas",
        (
            "Vacinas recentes (menos de 6 anos) que tomou: "
            "(Marque todas as que se aplicam)"
        ): "Vacinas",
    },
}


class AnamnesisLookupError(Exception):
    pass


def get_configured_anamnesis_access_secret(
    config: Mapping[str, Any] | None,
) -> str:
    if not config:
        return ""

    return normalize_text(config.get(ANAMNESIS_ACCESS_SECRET_KEY))


def is_anamnesis_access_authorized(
    config: Mapping[str, Any] | None,
    submitted_secret: Any,
) -> bool:
    configured_secret = get_configured_anamnesis_access_secret(config)
    submitted_secret = normalize_text(submitted_secret)

    if not configured_secret or not submitted_secret:
        return False

    return hmac.compare_digest(configured_secret, submitted_secret)


def normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def normalize_lookup_key(value: Any) -> str:
    normalized = normalize_text(value).lower()
    normalized = "".join(
        character
        for character in unicodedata.normalize("NFKD", normalized)
        if not unicodedata.combining(character)
    )
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return normalize_text(normalized)


def build_header_lookup(record: Mapping[str, Any]) -> dict[str, str]:
    return {normalize_lookup_key(header): header for header in record.keys()}


def resolve_patient_name_column(
    records: list[dict[str, Any]],
    configured_name_column: str | None = None,
) -> str:
    if not records:
        raise AnamnesisLookupError("The anamnesis sheet contains no records.")

    header_lookup = build_header_lookup(records[0])
    configured_column = normalize_lookup_key(configured_name_column)

    if configured_column:
        if configured_column in header_lookup:
            return header_lookup[configured_column]
        raise AnamnesisLookupError("Configured patient name column was not found.")

    for alias in PATIENT_NAME_ALIASES:
        normalized_alias = normalize_lookup_key(alias)
        if normalized_alias in header_lookup:
            return header_lookup[normalized_alias]

    raise AnamnesisLookupError("Patient name column was not found.")


def search_anamnesis_candidates(
    records: list[dict[str, Any]],
    search_term: str,
    name_column: str,
) -> list[dict[str, Any]]:
    normalized_search = normalize_lookup_key(search_term)
    if not normalized_search:
        return []

    candidates = []
    for index, record in enumerate(records):
        patient_name = normalize_text(record.get(name_column))
        if not patient_name:
            continue

        if normalized_search not in normalize_lookup_key(patient_name):
            continue

        candidates.append(
            {
                "record_index": index,
                "patient_name": patient_name,
                "timestamp": find_first_field_value(record, TIMESTAMP_ALIASES),
                "email": find_first_field_value(record, EMAIL_ALIASES),
                "record": dict(record),
            }
        )

    return candidates


def find_first_field_value(
    record: Mapping[str, Any],
    aliases: tuple[str, ...],
) -> str:
    header_lookup = build_header_lookup(record)
    for alias in aliases:
        header = header_lookup.get(normalize_lookup_key(alias))
        if header:
            value = normalize_text(record.get(header))
            if value:
                return value

    return ""


def format_candidate_label(candidate: Mapping[str, Any]) -> str:
    label_parts = [normalize_text(candidate.get("patient_name")) or "Paciente sem nome"]
    timestamp = normalize_text(candidate.get("timestamp"))
    email = normalize_text(candidate.get("email"))

    if timestamp:
        label_parts.append(timestamp)
    if email:
        label_parts.append(email)

    return " | ".join(label_parts)


def build_anamnesis_section_tables(
    record: Mapping[str, Any],
) -> dict[str, list[dict[str, str]]]:
    header_lookup = build_header_lookup(record)
    section_tables = {}

    for section_key, question_map in ANAMNESIS_SECTION_QUESTION_MAPS.items():
        section_tables[section_key] = build_anamnesis_section_rows(
            record,
            header_lookup,
            question_map,
        )

    return section_tables


def build_anamnesis_section_rows(
    record: Mapping[str, Any],
    header_lookup: Mapping[str, str],
    question_map: Mapping[str, str],
) -> list[dict[str, str]]:
    field_order = []
    values_by_field: dict[str, list[str]] = {}

    for source_question, output_field in question_map.items():
        if output_field not in values_by_field:
            field_order.append(output_field)
            values_by_field[output_field] = []

        source_header = header_lookup.get(normalize_lookup_key(source_question))
        if not source_header:
            continue

        answer = normalize_text(record.get(source_header))
        if answer:
            values_by_field[output_field].append(answer)

    return [
        {
            ANAMNESIS_FIELD_COLUMN: output_field,
            ANAMNESIS_ANSWER_COLUMN: (
                "; ".join(values_by_field[output_field])
                if values_by_field[output_field]
                else ANAMNESIS_EMPTY_VALUE_PLACEHOLDER
            ),
        }
        for output_field in field_order
    ]


def build_question_answer_rows(record: Mapping[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "Pergunta": row[ANAMNESIS_FIELD_COLUMN],
            "Resposta": row[ANAMNESIS_ANSWER_COLUMN],
        }
        for section_rows in build_anamnesis_section_tables(record).values()
        for row in section_rows
    ]


def build_report_anamnesis_rows(
    access_granted: bool,
    selected_sections: Mapping[str, list[dict[str, Any]]] | None,
) -> dict[str, list[dict[str, Any]]]:
    if not access_granted:
        return {}

    return {
        section_key: [
            {
                "campo": normalize_text(
                    row.get(ANAMNESIS_FIELD_COLUMN) or row.get("Pergunta")
                ),
                "resposta": normalize_text(row.get(ANAMNESIS_ANSWER_COLUMN))
                or ANAMNESIS_EMPTY_VALUE_PLACEHOLDER,
            }
            for row in section_rows
        ]
        for section_key, section_rows in (selected_sections or {}).items()
    }


def resolve_report_patient_name(
    typed_patient_name: Any,
    access_granted: bool,
    lookup_state: Mapping[str, Any] | None,
    selected_candidate_index: int | None = None,
) -> str:
    typed_patient_name = normalize_text(typed_patient_name)
    if not access_granted or not lookup_state:
        return typed_patient_name

    if lookup_state.get("status") != "ready":
        return typed_patient_name

    candidates = lookup_state.get("candidates") or []
    if not candidates:
        return typed_patient_name

    selected_candidate_index = selected_candidate_index or 0
    if selected_candidate_index < 0 or selected_candidate_index >= len(candidates):
        return typed_patient_name

    anamnesis_patient_name = normalize_text(
        candidates[selected_candidate_index].get("patient_name")
    )
    return anamnesis_patient_name or typed_patient_name


def load_google_sheet_records(
    spreadsheet_id: str,
    worksheet_name: str,
    service_account_info: Mapping[str, Any],
) -> list[dict[str, Any]]:
    try:
        import gspread
    except ImportError as exc:
        raise AnamnesisLookupError("Google Sheets dependency is not installed.") from exc

    client = gspread.service_account_from_dict(
        dict(service_account_info),
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets.readonly",
            "https://www.googleapis.com/auth/drive.readonly",
        ],
    )
    worksheet = client.open_by_key(spreadsheet_id).worksheet(worksheet_name)
    return worksheet.get_all_records(default_blank="")


def load_anamnesis_lookup(
    clinic_name: str,
    search_term: str,
    spreadsheet_id: str | None,
    worksheet_name: str | None,
    service_account_info: Mapping[str, Any] | None,
    configured_name_column: str | None = None,
    remote_loader: Callable[[str, str, Mapping[str, Any]], list[dict[str, Any]]]
    | None = None,
) -> dict[str, Any]:
    remote_loader = remote_loader or load_google_sheet_records

    try:
        if clinic_name not in SUPPORTED_ANAMNESIS_CLINICS:
            return {
                "status": "unavailable",
                "message": "Anamnese indisponível para esta clínica nesta versão.",
                "candidates": [],
            }

        if not spreadsheet_id or not worksheet_name or not service_account_info:
            raise AnamnesisLookupError("Google Sheets configuration is incomplete.")

        records = remote_loader(
            spreadsheet_id,
            worksheet_name,
            service_account_info,
        )
        if not records:
            return {
                "status": "not_found",
                "message": NO_ANAMNESIS_FOUND_MESSAGE,
                "candidates": [],
            }

        name_column = resolve_patient_name_column(records, configured_name_column)
        candidates = search_anamnesis_candidates(records, search_term, name_column)
        if not candidates:
            return {
                "status": "not_found",
                "message": NO_ANAMNESIS_FOUND_MESSAGE,
                "candidates": [],
            }

        return {
            "status": "ready",
            "message": None,
            "candidates": candidates,
        }
    except Exception:
        return {
            "status": "error",
            "message": UNAVAILABLE_ANAMNESIS_MESSAGE,
            "candidates": [],
        }
