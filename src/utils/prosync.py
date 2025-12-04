import pdfplumber
from pathlib import Path
import json

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
            if token.strip() == "Teste Controle'":
                summary["Controle"] = float(row[-1])

            if (token.strip() in parasites) and token.strip() not in list(
                summary.keys()
            ):
                test_value = row[-2].split("/")
                summary[token.strip()] = float(test_value[0])

    return summary


def extract_prosync_content(path):
    pdf_content = extract_pdf_content(path)
    pdf_content = [preprocess_text(content) for content in pdf_content]
    summ = retrival_pdf_information(pdf_content)

    return summ


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

    for k, v in prosync_summary.items():
        formated_key = k.title()
        test_content = {}

        for m_type, objs in microorganisms.items():
            for obj in objs:
                if obj["nome"] == formated_key:
                    retrival_information = obj.copy()
                    retrival_information["D"] = v
                    retrival_information["tipo"] = m_type
                    retrival_information["nome"] = formated_key

                    content.append(retrival_information)

                    break

        if len(test_content) == 0:
            d = DEFAULT_VALUE.copy()
            d["nome"] = k.title()
            d["D"] = v

            content.append(d)

    #! Parei aqui

    return content
