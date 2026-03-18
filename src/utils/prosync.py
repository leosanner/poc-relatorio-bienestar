import pdfplumber
from pathlib import Path
import json
from utils.oberon import microorganism_info

current_path = Path(__file__)
ROOT = current_path.parent.parent
PROSYNC_DATA_PATH = ROOT / "assets/prosync"
OBERON_DATA_PATH = ROOT / "assets/oberon"


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def preprocess_text(
    content,
):
    r = []
    for token in content:
        if not token:
            continue
        if token.startswith("."):
            continue

        r.append(token)

    return r


def extract_pdf_content(path):
    content = []

    with pdfplumber.open(path) as pdf:
        for p in pdf.pages:
            for table in p.extract_tables():
                for r in table:
                    content.append(r)

    return content


def retrival_pdf_information(content: list):
    summary = {}
    parasites = load_json(PROSYNC_DATA_PATH / "parasitas.json")["parasitas"]

    for row in content:
        if row == None:
            continue

        for token in row:
            if token.strip() == "Teste Controle":
                summary["Controle"] = int(row[-1])

            if (token.strip() in parasites) and token.strip() not in list(
                summary.keys()
            ):
                test_value = row[-2].split("/")
                summary[token.strip()] = int(test_value[0])

    return summary


def filter_prosync_by_control_std(
    prosync_microorganisms: list[dict], prosync_std: float | None = None
):
    if not prosync_microorganisms:
        return prosync_microorganisms

    control_data = prosync_microorganisms[0]
    control_value = control_data.get("D")

    if control_data.get("nome", "").lower() != "controle" or control_value is None:
        return prosync_microorganisms

    if prosync_std is None:
        return prosync_microorganisms

    control_value = float(control_value)
    std_value = control_value * float(prosync_std)
    lower_bound = control_value - std_value
    upper_bound = control_value + std_value

    filtered_microorganisms = [control_data]

    for microorganism in prosync_microorganisms[1:]:
        microorganism_value = microorganism.get("D")
        if microorganism_value is None:
            continue

        microorganism_value = float(microorganism_value)
        if (microorganism_value < lower_bound) or (microorganism_value > upper_bound):
            filtered_microorganisms.append(microorganism)

    return filtered_microorganisms


def extract_prosync_content(path, prosync_std: float | None = None):
    pdf_content = extract_pdf_content(path)
    pdf_content = [preprocess_text(content) for content in pdf_content]
    summ = retrival_pdf_information(pdf_content)
    prosync_microorganisms = find_microorgnism_prosyn_info(summ)

    return filter_prosync_by_control_std(prosync_microorganisms, prosync_std)


# Melhorar isso para ficar unificado com o do oberon
def find_microorgnism_prosyn_info(prosync_summary: dict):
    microorganisms = load_json(
        OBERON_DATA_PATH / "informacoes/microrganismos_atualizado.json"
    )
    microorganisms_matches = load_json(
        OBERON_DATA_PATH / "correspondencia/microrganismos_atualizado.json"
    )

    DEFAULT_VALUE = {
        "nome": "",
        "sintomas": "não encontrado",
        "fonte": "não encontrado",
        "tipo": "não encontrado",
    }

    content = []

    return microorganism_info(prosync_summary, for_prosync=True)

    # Solução prévia
    for k, v in prosync_summary.items():
        formated_key = k.title()
        retrival_information = {}

        for m_type, objs in microorganisms.items():
            for obj in objs:
                if obj["nome"].title() == formated_key:
                    retrival_information = obj.copy()
                    retrival_information["D"] = v
                    retrival_information["tipo"] = m_type
                    retrival_information["nome"] = formated_key

                    content.append(retrival_information)

                    break

        if len(retrival_information) == 0:
            print(k.title(), v)
            d = DEFAULT_VALUE.copy()
            d["nome"] = k.title()
            d["D"] = v

            content.append(d)

    return content
