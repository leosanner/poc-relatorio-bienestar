from utils.protocol import (
    add_midterm_analysis_sessions,
    metals_treatment_block,
    microorganisms_treatment_block,
    SESSION_COMPLEMENT_NAME,
)
from pathlib import Path
from datetime import datetime
from rich import print
from io import BytesIO
import json
from docxtpl import DocxTemplate


SRC = Path(__file__).parent.parent
ASSETS = SRC / "assets"
BUDGET_ASSETS_PATH = ASSETS / "budget"
BUDGET_TEMPLATE_PATH = BUDGET_ASSETS_PATH / "template_orcamento.docx"
PRICES_PATH = BUDGET_ASSETS_PATH / "prices.json"
DEFAULT_TREATMENT_PRICE_NAME = "RPD"
SESSION_COMPLEMENT_PRICE_NAME = "Hidrovitalis + ILIB + Hidrogênio"


def load_prices() -> dict:
    with open(PRICES_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def format_currency(value: float | int) -> str:
    formatted_value = f"{value:,.2f}"
    formatted_value = formatted_value.replace(",", "X").replace(".", ",").replace(
        "X", "."
    )
    return f"R$ {formatted_value}"


def is_frequency_time_row(content: str) -> bool:
    parts = [part.strip() for part in content.split(",")]
    if len(parts) != 2:
        return False

    try:
        float(parts[0])
        float(parts[1])
    except ValueError:
        return False

    return True


def extract_treatment_budget_items(content: list[str]) -> list[dict[str, str]]:
    sessions = []
    for treatment in content:
        treatment = treatment.strip()
        if not treatment:
            continue

        if treatment == SESSION_COMPLEMENT_NAME:
            continue

        session_names = []
        for session_row in treatment.splitlines():
            cleaned_row = session_row.strip()
            if cleaned_row.startswith("RPD -") or cleaned_row.startswith("#"):
                if cleaned_row:
                    session_names.append(cleaned_row)
                continue

            if not is_frequency_time_row(cleaned_row) and cleaned_row:
                session_names.append(cleaned_row)

        if len(session_names) == 0 and treatment.lower().startswith("sessão"):
            session_names.append(treatment)

        if session_names:
            sessions.append(
                {
                    "name": "\n".join(session_names),
                    "price_name": DEFAULT_TREATMENT_PRICE_NAME,
                }
            )

    return sessions


def is_rpd_treatment(session_name: str) -> bool:
    return session_name.lstrip().startswith("RPD -")


def format_not_founded(content: list[str]) -> list[str]:
    return content if len(content) > 0 else ["Todos foram encontrados"]


def add_row_numbers(
    rows: list[dict[str, str]], start_number: int
) -> tuple[list[dict[str, str]], int]:
    numbered_rows = []
    current_number = start_number

    for row in rows:
        numbered_rows.append({**row, "number": str(current_number)})
        current_number += 1

    return numbered_rows, current_number


def create_budget_rows(
    session_items: list[dict[str, str]],
    prices: dict[str, dict[str, float | int]],
    multiplier: float = 1.0,
) -> tuple[list[dict[str, str]], float, float]:
    rows = []
    total_pix = 0.0
    total_card = 0.0
    session_complement_price = prices.get(SESSION_COMPLEMENT_PRICE_NAME)
    if not session_complement_price:
        raise ValueError(
            f"Treatment price '{SESSION_COMPLEMENT_PRICE_NAME}' not found."
        )

    for session_item in session_items:
        session_name = session_item["name"]
        price_name = session_item["price_name"]
        price = prices.get(price_name)
        if not price:
            raise ValueError(f"Treatment price '{price_name}' not found.")

        pix = float(price.get("pix", 0)) * multiplier
        card = float(price.get("cartao", 0)) * multiplier
        row = {
            "name": session_name,
            "pix": format_currency(pix),
            "card": format_currency(card),
            "h": "",
            "h_p": "",
            "h_c": "",
        }

        if is_rpd_treatment(session_name):
            complement_pix = float(session_complement_price.get("pix", 0)) * multiplier
            complement_card = (
                float(session_complement_price.get("cartao", 0)) * multiplier
            )
            row.update(
                {
                    "h": SESSION_COMPLEMENT_NAME,
                    "h_p": format_currency(complement_pix),
                    "h_c": format_currency(complement_card),
                }
            )
            pix += complement_pix
            card += complement_card

        rows.append(row)
        total_pix += pix
        total_card += card

    return rows, total_pix, total_card


def create_extra_sessions_rows(
    extra_sessions: list[str], prices: dict[str, dict[str, float | int]]
) -> tuple[list[dict[str, str]], float, float]:
    rows = []
    total_pix = 0.0
    total_card = 0.0

    for session_name in extra_sessions:
        price = prices.get(session_name)
        if not price:
            rows.append(
                {
                    "name": session_name,
                    "pix": "Não encontrado",
                    "card": "Não encontrado",
                }
            )
            continue

        pix = float(price.get("pix", 0))
        card = float(price.get("cartao", 0))
        rows.append(
            {
                "name": session_name,
                "pix": format_currency(pix),
                "card": format_currency(card),
            }
        )
        total_pix += pix
        total_card += card

    return rows, total_pix, total_card


def format_content_for_budget(microorganisms_prosync, microorganisms_oberon, toxins):
    metals_treatment, not_founded_metals = metals_treatment_block(toxins)
    microorganisms_treatment, not_founded_microorganisms = (
        microorganisms_treatment_block(
            microorganisms_prosync, microorganisms_oberon
        )
    )
    total_metals_sessions = len(metals_treatment)
    metals_treatment = add_midterm_analysis_sessions(metals_treatment)
    microorganisms_treatment = add_midterm_analysis_sessions(
        microorganisms_treatment, initial_session_count=total_metals_sessions
    )

    return {
        "microorganisms_budget": extract_treatment_budget_items(
            microorganisms_treatment
        ),
        "microorganisms_not_founded": format_not_founded(
            not_founded_microorganisms
        ),
        "metals_budget": extract_treatment_budget_items(metals_treatment),
        "metals_not_founded": format_not_founded(not_founded_metals),
    }


def build_budget_context(protocol_content: dict, multiplier: float = 1.0) -> dict:
    microorganisms_prosync = protocol_content.get("table_prosync", {})
    microorganisms_oberon = protocol_content.get("table_microorganism", {})
    toxins = protocol_content.get("table_toxins", {})
    extra_sessions = protocol_content.get("extra_sessions", [])
    extra_session_prices = protocol_content.get("extra_session_prices")

    formatted_budget_content = format_content_for_budget(
        microorganisms_prosync, microorganisms_oberon, toxins
    )
    prices = load_prices()
    microorganisms_budget, microorganisms_total_pix, microorganisms_total_card = (
        create_budget_rows(
            formatted_budget_content["microorganisms_budget"], prices, multiplier
        )
    )
    metals_budget, metals_total_pix, metals_total_card = create_budget_rows(
        formatted_budget_content["metals_budget"], prices, multiplier
    )
    extra_session_price_lookup = (
        prices if extra_session_prices is None else extra_session_prices
    )
    extra_sessions_budget, extra_total_pix, extra_total_card = (
        create_extra_sessions_rows(extra_sessions, extra_session_price_lookup)
    )
    next_row_number = 10
    microorganisms_budget, next_row_number = add_row_numbers(
        microorganisms_budget, next_row_number
    )
    metals_budget, next_row_number = add_row_numbers(
        metals_budget, next_row_number
    )
    extra_sessions_budget, next_row_number = add_row_numbers(
        extra_sessions_budget, next_row_number
    )

    treatments_total_pix = microorganisms_total_pix + metals_total_pix
    treatments_total_card = microorganisms_total_card + metals_total_card
    total_pix = treatments_total_pix + extra_total_pix
    total_card = treatments_total_card + extra_total_card

    return {
        "name": protocol_content.get("name", "") or "",
        "date": protocol_content.get("date")
        or datetime.now().strftime("%d/%m/%Y"),
        "microorganisms_budget": microorganisms_budget,
        "microorganisms_not_founded": formatted_budget_content[
            "microorganisms_not_founded"
        ],
        "metals_budget": metals_budget,
        "metals_not_founded": formatted_budget_content["metals_not_founded"],
        "extra_sessions_budget": extra_sessions_budget,
        "treatments_total_pix": format_currency(treatments_total_pix),
        "treatments_total_card": format_currency(treatments_total_card),
        "extra_sessions_total_pix": format_currency(extra_total_pix),
        "extra_sessions_total_card": format_currency(extra_total_card),
        "total_pix": format_currency(total_pix),
        "total_card": format_currency(total_card),
    }


def generate_budget(protocol_content, multiplier: float = 1.0):
    if not BUDGET_TEMPLATE_PATH.exists():
        print(f"Template not found at {BUDGET_TEMPLATE_PATH}")
        return

    content = build_budget_context(protocol_content, multiplier)
    doc = DocxTemplate(BUDGET_TEMPLATE_PATH)
    doc.render(content)

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    return buffer
