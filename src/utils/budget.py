from utils.protocol import (
    add_midterm_analysis_sessions,
    metals_treatment_block,
    microorganisms_treatment_block,
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


def load_prices() -> dict:
    with open(PRICES_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def format_currency(value: float | int) -> str:
    formatted_value = f"{value:,.2f}"
    formatted_value = formatted_value.replace(",", "X").replace(".", ",").replace(
        "X", "."
    )
    return f"R$ {formatted_value}"


def extract_only_substance_name(content: list[str]) -> list[str]:
    sessions = []
    for treatment in content:
        session_names = []
        for session_row in treatment.splitlines():
            cleaned_row = session_row.strip()
            if cleaned_row.startswith("#"):
                cleaned_row = cleaned_row.lstrip("#").strip()
                if cleaned_row:
                    session_names.append(cleaned_row)

        if len(session_names) == 0 and treatment.strip().lower().startswith("sessão"):
            session_names.append(treatment.strip())

        sessions.append("\n".join(session_names))

    return sessions


def format_not_founded(content: list[str]) -> list[str]:
    return content if len(content) > 0 else ["Todos foram encontrados"]


def create_budget_rows(
    session_names: list[str], price: dict[str, float | int]
) -> tuple[list[dict[str, str]], float, float]:
    rows = []
    total_pix = 0.0
    total_card = 0.0

    pix = float(price.get("pix", 0))
    card = float(price.get("cartao", 0))

    for session_name in session_names:
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
        "microorganisms_budget": extract_only_substance_name(
            microorganisms_treatment
        ),
        "microorganisms_not_founded": format_not_founded(
            not_founded_microorganisms
        ),
        "metals_budget": extract_only_substance_name(metals_treatment),
        "metals_not_founded": format_not_founded(not_founded_metals),
    }


def build_budget_context(protocol_content: dict) -> dict:
    microorganisms_prosync = protocol_content.get("table_prosync", {})
    microorganisms_oberon = protocol_content.get("table_microorganism", {})
    toxins = protocol_content.get("table_toxins", {})
    extra_sessions = protocol_content.get("extra_sessions", [])
    extra_session_prices = protocol_content.get("extra_session_prices")

    formatted_budget_content = format_content_for_budget(
        microorganisms_prosync, microorganisms_oberon, toxins
    )
    prices = load_prices()
    default_treatment_price = prices.get(DEFAULT_TREATMENT_PRICE_NAME)
    if not default_treatment_price:
        raise ValueError(
            f"Default treatment price '{DEFAULT_TREATMENT_PRICE_NAME}' not found."
        )

    microorganisms_budget, microorganisms_total_pix, microorganisms_total_card = (
        create_budget_rows(
            formatted_budget_content["microorganisms_budget"], default_treatment_price
        )
    )
    metals_budget, metals_total_pix, metals_total_card = create_budget_rows(
        formatted_budget_content["metals_budget"], default_treatment_price
    )
    extra_session_price_lookup = (
        prices if extra_session_prices is None else extra_session_prices
    )
    extra_sessions_budget, extra_total_pix, extra_total_card = (
        create_extra_sessions_rows(extra_sessions, extra_session_price_lookup)
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


def generate_budget(protocol_content):
    if not BUDGET_TEMPLATE_PATH.exists():
        print(f"Template not found at {BUDGET_TEMPLATE_PATH}")
        return

    content = build_budget_context(protocol_content)
    doc = DocxTemplate(BUDGET_TEMPLATE_PATH)
    doc.render(content)

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    return buffer
