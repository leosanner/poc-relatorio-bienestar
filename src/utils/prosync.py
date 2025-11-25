import pdfplumber
from pathlib import Path
import json
from pprint import pprint

current_path = Path(__file__)
ROOT = current_path.parent.parent
PROSYNC_DATA_PATH = ROOT / 'assets/prosync'

def load_json(path):
    with open(path, 'r', encoding='utf-8') as file:
        return json.load(file)

def preprocess_text(content, ):
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

def retrival_pdf_information(content:list):
    summary = {}
    parasites = load_json(PROSYNC_DATA_PATH/'parasitas.json')['parasitas']

    for row in content:
        if row == None:
            continue

        for token in row:
            if token.strip() == "Teste Controle":
                summary['controle'] = float(row[-1])

            if (token.strip() in parasites ) and token.strip() not in list(summary.keys()):
                test_value = row[-2].split('/')
                summary[token.strip()] = float(test_value[0])

    return summary


def extract_prosync_content(path):
    pdf_content = extract_pdf_content(path)
    pdf_content = [preprocess_text(content) for content in pdf_content]
    summ = retrival_pdf_information(pdf_content)

    return summ
