from io import BytesIO
from pathlib import Path

from docxtpl import DocxTemplate

from utils.budget import build_budget_context


SRC = Path(__file__).parent.parent
CONTROL_TEMPLATE_PATH = SRC / "assets" / "control" / "template_controle.docx"
CONTROL_DATE_PLACEHOLDER = "__/__/____"
CONTROL_SIGNATURE_PLACEHOLDER = "__________________"
CONTROL_DYNAMIC_START_WEEK = 10


def build_control_context(protocol_content: dict) -> dict:
    budget_context = build_budget_context(protocol_content)
    sessions = []

    for budget_key in (
        "microorganisms_budget",
        "metals_budget",
        "extra_sessions_budget",
    ):
        for row in budget_context.get(budget_key, []):
            session_name = str(row.get("name", "")).strip()
            if session_name:
                week_number = len(sessions) + CONTROL_DYNAMIC_START_WEEK
                sessions.append(
                    {
                        "week": week_number,
                        "name": session_name,
                        "date_placeholder": CONTROL_DATE_PLACEHOLDER,
                        "signature_placeholder": CONTROL_SIGNATURE_PLACEHOLDER,
                    }
                )

    return {
        "name": budget_context.get("name", ""),
        "date": budget_context.get("date", ""),
        "control": sessions,
        "microorganisms_not_founded": budget_context.get(
            "microorganisms_not_founded", []
        ),
        "metals_not_founded": budget_context.get("metals_not_founded", []),
    }


def generate_control(protocol_content: dict):
    if not CONTROL_TEMPLATE_PATH.exists():
        print(f"Template not found at {CONTROL_TEMPLATE_PATH}")
        return

    content = build_control_context(protocol_content)
    doc = DocxTemplate(CONTROL_TEMPLATE_PATH)
    doc.render(content)

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    return buffer
