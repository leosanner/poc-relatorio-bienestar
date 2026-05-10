import json
import re
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any


COMPANY_COLUMN_KEY_BY_NAME = {
    "Bienestar": "bienestar",
    "VitaeFlux": "vitaeflux",
    "Alecrim": "alecrim",
}
PRICE_FIELDS = ("pix", "cartao")
REQUIRED_HEADERS = ("nome tratamento",) + tuple(
    f"{company_key} {price_field}"
    for company_key in COMPANY_COLUMN_KEY_BY_NAME.values()
    for price_field in PRICE_FIELDS
)
FALLBACK_CATALOG_PATH = (
    Path(__file__).resolve().parent.parent
    / "assets"
    / "budget"
    / "extra_sessions_catalog_fallback.json"
)
FALLBACK_WARNING_MESSAGE = (
    "Nao foi possivel atualizar as sessoes extras pelo Google Sheets. "
    "O sistema esta usando o catalogo local de contingencia."
)
UNAVAILABLE_ERROR_MESSAGE = (
    "Nao foi possivel carregar o catalogo de sessoes extras. "
    "Verifique a configuracao do Google Sheets e o arquivo local de contingencia."
)


class ExtraSessionsCatalogError(Exception):
    pass


def normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def normalize_key(value: Any) -> str:
    return normalize_text(value).lower()


def parse_price(value: Any, field_name: str, treatment_name: str) -> float | None:
    if value is None or value == "":
        return None

    if isinstance(value, bool):
        raise ExtraSessionsCatalogError(
            f"Invalid price for '{treatment_name}' in '{field_name}'."
        )

    if isinstance(value, (int, float)):
        return float(value)

    normalized_value = normalize_text(value)
    if not normalized_value:
        return None

    normalized_value = (
        normalized_value.replace("R$", "")
        .replace(" ", "")
        .replace("\u00a0", "")
    )
    normalized_value = re.sub(r"[^0-9,.-]", "", normalized_value)

    if normalized_value.count(",") + normalized_value.count(".") > 1:
        last_separator_index = max(
            normalized_value.rfind(","),
            normalized_value.rfind("."),
        )
        integer_part = re.sub(r"[,.]", "", normalized_value[:last_separator_index])
        decimal_part = re.sub(r"[,.]", "", normalized_value[last_separator_index + 1 :])
        normalized_value = (
            f"{integer_part}.{decimal_part}" if decimal_part else integer_part
        )
    elif "," in normalized_value and "." in normalized_value:
        if normalized_value.rfind(",") > normalized_value.rfind("."):
            normalized_value = normalized_value.replace(".", "").replace(",", ".")
        else:
            normalized_value = normalized_value.replace(",", "")
    elif "," in normalized_value:
        normalized_value = normalized_value.replace(".", "").replace(",", ".")

    try:
        return float(normalized_value)
    except ValueError as exc:
        raise ExtraSessionsCatalogError(
            f"Invalid price for '{treatment_name}' in '{field_name}'."
        ) from exc


def normalize_extra_sessions_records(
    records: list[dict[str, Any]],
    source_name: str,
) -> list[dict[str, Any]]:
    if not records:
        raise ExtraSessionsCatalogError(f"{source_name} returned no records.")

    available_headers = {
        normalize_key(header)
        for record in records
        for header in record.keys()
    }
    missing_headers = [
        header for header in REQUIRED_HEADERS if header not in available_headers
    ]
    if missing_headers:
        raise ExtraSessionsCatalogError(
            f"{source_name} is missing required headers: {', '.join(missing_headers)}."
        )

    catalog = []
    seen_treatments = set()

    for raw_record in records:
        record = {normalize_key(header): value for header, value in raw_record.items()}
        treatment_name = normalize_text(record.get("nome tratamento"))
        if not treatment_name:
            continue

        normalized_name = normalize_key(treatment_name)
        if normalized_name in seen_treatments:
            raise ExtraSessionsCatalogError(
                f"Duplicate treatment name found in {source_name}: {treatment_name}."
            )
        seen_treatments.add(normalized_name)

        prices = {}
        for company_name, company_key in COMPANY_COLUMN_KEY_BY_NAME.items():
            company_prices = {}
            for price_field in PRICE_FIELDS:
                field_name = f"{company_key} {price_field}"
                company_prices[price_field] = parse_price(
                    record.get(field_name),
                    field_name=field_name,
                    treatment_name=treatment_name,
                )
            prices[company_name] = company_prices

        catalog.append(
            {
                "treatment_name": treatment_name,
                "prices": prices,
            }
        )

    if not catalog:
        raise ExtraSessionsCatalogError(f"{source_name} contains no usable treatments.")

    return catalog


def load_google_sheet_records(
    spreadsheet_id: str,
    worksheet_name: str,
    service_account_info: Mapping[str, Any],
) -> list[dict[str, Any]]:
    try:
        import gspread
    except ImportError as exc:
        raise ExtraSessionsCatalogError(
            "Google Sheets dependency is not installed."
        ) from exc

    client = gspread.service_account_from_dict(
        dict(service_account_info),
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets.readonly",
            "https://www.googleapis.com/auth/drive.readonly",
        ],
    )
    worksheet = client.open_by_key(spreadsheet_id).worksheet(worksheet_name)
    return worksheet.get_all_records(default_blank="")


def load_fallback_records(fallback_path: Path = FALLBACK_CATALOG_PATH) -> list[dict[str, Any]]:
    with fallback_path.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    if not isinstance(payload, list):
        raise ExtraSessionsCatalogError("Fallback catalog must be a list of records.")

    return payload


def load_extra_sessions_catalog(
    spreadsheet_id: str | None,
    worksheet_name: str | None,
    service_account_info: Mapping[str, Any] | None,
    fallback_path: Path = FALLBACK_CATALOG_PATH,
    remote_loader: Callable[[str, str, Mapping[str, Any]], list[dict[str, Any]]]
    | None = None,
) -> dict[str, Any]:
    remote_loader = remote_loader or load_google_sheet_records

    try:
        if not spreadsheet_id or not worksheet_name or not service_account_info:
            raise ExtraSessionsCatalogError("Google Sheets configuration is incomplete.")

        remote_records = remote_loader(
            spreadsheet_id,
            worksheet_name,
            service_account_info,
        )
        catalog = normalize_extra_sessions_records(
            remote_records,
            source_name="Google Sheets",
        )
        return {
            "catalog": catalog,
            "source": "google",
            "status": "ready",
            "message": None,
        }
    except Exception:
        try:
            fallback_catalog = normalize_extra_sessions_records(
                load_fallback_records(fallback_path),
                source_name="Fallback catalog",
            )
            return {
                "catalog": fallback_catalog,
                "source": "fallback",
                "status": "warning",
                "message": FALLBACK_WARNING_MESSAGE,
            }
        except Exception:
            return {
                "catalog": [],
                "source": "unavailable",
                "status": "error",
                "message": UNAVAILABLE_ERROR_MESSAGE,
            }


def get_clinic_prices(
    catalog_item: Mapping[str, Any],
    clinic_name: str,
) -> dict[str, float] | None:
    prices = catalog_item.get("prices", {}).get(clinic_name, {})
    pix = prices.get("pix")
    cartao = prices.get("cartao")

    if pix is None or cartao is None:
        return None

    return {
        "pix": float(pix),
        "cartao": float(cartao),
    }


def build_catalog_options_for_clinic(
    catalog: list[dict[str, Any]],
    clinic_name: str,
) -> list[dict[str, Any]]:
    options = []

    for item in catalog:
        clinic_prices = get_clinic_prices(item, clinic_name)
        if not clinic_prices:
            continue

        options.append(
            {
                "treatment_name": item["treatment_name"],
                "prices": clinic_prices,
            }
        )

    return options


def build_selected_session_price_lookup(
    catalog: list[dict[str, Any]],
    clinic_name: str,
    selected_sessions: list[str],
) -> dict[str, dict[str, float]]:
    catalog_by_name = {item["treatment_name"]: item for item in catalog}
    selected_prices = {}

    for session_name in selected_sessions:
        catalog_item = catalog_by_name.get(session_name)
        if not catalog_item:
            continue

        clinic_prices = get_clinic_prices(catalog_item, clinic_name)
        if clinic_prices:
            selected_prices[session_name] = clinic_prices

    return selected_prices
