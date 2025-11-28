from pathlib import Path
import os
import json

current_path = Path(__file__)
ROOT = current_path.parent.parent
OBERON_DATA_PATH = ROOT / "assets/oberon"
FILE_NAME = "example.txt"


def load_txt(path, encoding="utf-8"):
    if hasattr(path, "read"):
        content = path.read()
        if isinstance(content, bytes):
            return content.decode(encoding)
        return content

    with open(path, "r", encoding=encoding) as file:
        return file.read()


def format_file_name(file_name):
    file_name = file_name.replace(".txt", "")
    file_name = file_name.split("-")[-1]

    return file_name.lower().strip()


def extract_row_content(row: str, term="D="):
    idx = row.find(term)

    if idx == -1:
        return None

    name = row[:idx].strip()
    value = row[idx + len(term) :].strip()

    return (name, term, value)


def extract_oberon_content(file_path, enc="utf-8"):
    txt = load_txt(file_path, enc)
    content = []

    for row in txt.splitlines():
        if "D=" in row:
            result = extract_row_content(row.strip())

            if result:
                content.append(result)

    content = {line[0]: line[2] for line in content}

    return content


def load_test_information(file_name):
    data_path = OBERON_DATA_PATH / "informacoes"

    with open(data_path / file_name, "r", encoding="utf-8") as file:
        return json.load(file)


def load_match_information(file_name):
    data_path = OBERON_DATA_PATH / "correspondencia"

    with open(data_path / file_name, "r", encoding="utf-8") as file:
        return json.load(file)


def toxins_info(oberon_toxin_content: dict, json_file="toxinas.json"):

    DEFAULT_VALUE = {
        "nome": "",
        "tipo": "não encontrado",
        "efeitos": "não encontrado",
        "fontes": "não encontrado",
    }

    toxins_information = load_test_information(json_file)
    toxins_match = load_match_information(json_file)

    content = []

    for k, v in oberon_toxin_content.items():
        if toxins_match.get(k.lower()):
            match_name = toxins_match.get(k.lower()).lower()

            for t in toxins_information:
                if t.get("nome").lower() == match_name:
                    t["D"] = v

                    content.append(t)

                    break
        else:
            d = DEFAULT_VALUE.copy()
            d["nome"] = k
            d["D"] = v

            content.append(d)

    return content


def crystal_info(oberon_crystal_content: dict, json_file="cristais.json"):

    DEFAULT_VALUE = {
        "cristal": "",
        "beneficios_fisicos": "não encontrado",
        "beneficios_emocionais": "não encontrado",
    }

    crystal_information = load_test_information(json_file)
    crystal_match = load_match_information(json_file)

    content = []

    for k, v in oberon_crystal_content.items():
        if crystal_match.get(k):
            match_name = crystal_match.get(k)

            for t in crystal_information:
                if t["cristal"] == match_name:
                    t["D"] = v

                    content.append(t)

                    break
        else:
            d = DEFAULT_VALUE.copy()
            d["cristal"] = k
            d["D"] = v

            content.append(d)

    return content


def microorganism_info(
    oberon_microorganism_content: dict, json_file="microrganismos.json"
):

    DEFAULT_VALUE = {
        "nome": "",
        "sintomas": "não encontrado",
        "fonte": "não encontrado",
        "tipo": "não encontrado",
    }

    microorganism_information = load_test_information(json_file)
    microorganism_match = load_match_information(json_file)

    content = []

    for k, v in oberon_microorganism_content.items():
        if microorganism_match.get(k):
            match_name = microorganism_match.get(k)

            for m_type, objs in microorganism_information.items():
                for obj in objs:

                    if obj["nome"] == match_name:
                        obj["D"] = v
                        obj["tipo"] = m_type

                        content.append(obj)

                        break
        else:
            d = DEFAULT_VALUE.copy()
            d["nome"] = k
            d["D"] = v

            content.append(d)

    return content
