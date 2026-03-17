from utils.protocol import metals_treatment_block, microorganisms_treatment_block
from pathlib import Path
from rich import print
from io import BytesIO
from docxtpl import DocxTemplate


SRC = Path(__file__).parent.parent
ASSETS = SRC / "assets"
BUDGET_ASSETS_PATH = ASSETS / "budget"
BUDGET_TEMPLATE_PATH = BUDGET_ASSETS_PATH / "template_orcamento.docx"


def extract_only_substance_name(content: list[str]):
    sessions = []
    for treatment in content:
        session = []
        for session_row in treatment.split("\n"):
            if session_row.startswith("#"):
                session.append(session_row)

        if len(session) == 0 and treatment.lower().startswith("sessão"):
            session.append(treatment)

        sessions.append(session)

    return sessions


def format_budget_for_docx(content: list[list[str]]):
    formated_content = []

    for session in content:
        treatment = "\n".join(session)
        formated_content.append(treatment)

    return formated_content


def format_not_founded(content):
    return "\n".join(content) if len(content) > 0 else "Todos foram encontrados"


def format_content_for_budget(microorganisms_prosync, microorganisms_oberon, toxins):
    t_t_b, not_founded_metals = metals_treatment_block(toxins)
    m_t_b, not_founded_microorganisms = microorganisms_treatment_block(
        microorganisms_prosync, microorganisms_oberon
    )

    metals = extract_only_substance_name(m_t_b)
    microorganisms = extract_only_substance_name(t_t_b)

    microorganisms_formated_sessions = format_budget_for_docx(microorganisms)
    metals_formated_sessions = format_budget_for_docx(metals)

    return (
        [
            microorganisms_formated_sessions,
            format_not_founded(not_founded_microorganisms),
        ],
        [metals_formated_sessions, format_not_founded(not_founded_metals)],
    )


def generate_budget(protocol_content):
    microorganisms_prosync = protocol_content.get("table_prosync", {})
    microorganisms_oberon = protocol_content.get("table_microorganism", {})
    toxins = protocol_content.get("table_toxins", {})

    microorganisms, metals = format_content_for_budget(
        microorganisms_prosync, microorganisms_oberon, toxins
    )

    if not BUDGET_TEMPLATE_PATH.exists():
        print(f"Template not found at {BUDGET_TEMPLATE_PATH}")
        return

    content = {
        "name": "Nome teste",
        "microorganisms_budget": microorganisms[0],
        "microorganisms_not_founded": [microorganisms[1]],
        "metals_budget": metals[0],
        "metals_not_founded": [metals[1]],
    }

    doc = DocxTemplate(BUDGET_TEMPLATE_PATH)
    doc.render(content)

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    return buffer
