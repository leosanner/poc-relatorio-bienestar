import hmac
import re
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
    return normalize_text(value).lower()


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


def build_question_answer_rows(record: Mapping[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "Pergunta": normalize_text(question),
            "Resposta": normalize_text(answer),
        }
        for question, answer in record.items()
    ]


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
