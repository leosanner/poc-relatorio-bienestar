from pathlib import Path
import os
import json
import re
from utils.format_string import first_char_uppercase
from utils.sort_elements import sort_by_d, remove_duplicates
from utils.find_most_related_term import find_related_term

current_path = Path(__file__)
ROOT = current_path.parent.parent
OBERON_DATA_PATH = ROOT / "assets/oberon"
FILE_NAME = "example.txt"

important_microrganisms = [
    "ascaris",
    "bacillus cereus",
    "candida",
    "chlamydia",
    "cytomegalovirus",
    "epstein barr",
    "h. pylori",
    "meningitidis",
    "mycobacterium tuberculosis",
    "staphylococcus",
    "hepatite",
    "varicela",
]


def load_stopwords(file_name):
    data_path = OBERON_DATA_PATH / "elementos-excluir"

    with open(data_path / file_name, "r", encoding="utf-8") as file:
        return json.load(file)


def load_txt(path, encoding):
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
    value = re.sub(r"[^0-9\.]", "", value)

    return (name, term, value)


def extract_oberon_content(file_path, enc="utf-8"):
    txt = load_txt(file_path, encoding=enc)
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


def toxins_info(oberon_toxin_content: dict, json_file="toxinas_atualizado.json"):

    DEFAULT_VALUE = {
        "nome": "",
        "tipo": "não encontrado",
        "efeitos": "não encontrado",
        "fontes": "não encontrado",
    }

    toxins_sw = load_stopwords("toxinas.json")
    toxins_information = load_test_information(json_file)
    toxins_match = load_match_information(json_file)
    content = []

    for k, v in oberon_toxin_content.items():
        if find_related_term(k, toxins_sw):
            continue

        formatted_key = k.title()

        if toxins_match.get(formatted_key):
            match_name = toxins_match.get(formatted_key)
            for t in toxins_information:
                if t.get("nome").title() == match_name.title():
                    t["nome"] = first_char_uppercase(match_name)

                    t["D"] = v
                    content.append(t)

                    break

        else:
            d = DEFAULT_VALUE.copy()
            d["nome"] = k.title()
            d["D"] = v

            content.append(d)

    unique_content = remove_duplicates(content)

    return sort_by_d(unique_content)


def crystal_info(oberon_crystal_content: dict, json_file="cristais.json"):

    DEFAULT_VALUE = {
        "cristal": "",
        "beneficios_fisicos": "não encontrado",
        "beneficios_emocionais": "não encontrado",
    }

    crystal_information = load_test_information(json_file)
    crystal_match = load_match_information(json_file)
    crystal_sw = load_stopwords(json_file)

    content = []

    for k, v in oberon_crystal_content.items():
        if find_related_term(k, crystal_sw):
            continue

        formatted_key = k.title()
        if crystal_match.get(formatted_key):
            match_name = crystal_match.get(formatted_key)

            for t in crystal_information:
                if t["cristal"].title() == match_name:
                    t["nome"] = first_char_uppercase(match_name)

                    t["D"] = v

                    content.append(t)

                    break
        else:
            d = DEFAULT_VALUE.copy()
            d["cristal"] = k.title()
            d["D"] = v

            content.append(d)

    unique_content = remove_duplicates(content)

    return sort_by_d(unique_content)


def microorganism_info(
    oberon_microorganism_content: dict, json_file="microrganismos_atualizado.json"
):

    DEFAULT_VALUE = {
        "nome": "",
        "sintomas": "não encontrado",
        "fonte": "Não encontrado",
        "tipo": "não encontrado",
    }

    microorganism_sw = load_stopwords("microrganismos.json")
    microorganism_information = load_test_information(json_file)
    microorganism_match = load_match_information(json_file)

    content = []

    for k, v in oberon_microorganism_content.items():
        formated_key = k.title()
        if k.lower() in microorganism_sw:
            continue

        if microorganism_match.get(formated_key):
            match_name = microorganism_match.get(formated_key).title()
            for m_type, objs in microorganism_information.items():
                for obj in objs:
                    if obj["nome"].title() == match_name:
                        obj["nome"] = first_char_uppercase(match_name)
                        obj["D"] = v
                        obj["tipo"] = m_type.title()
                        content.append(obj)

                        break
        else:
            d = DEFAULT_VALUE.copy()
            d["nome"] = first_char_uppercase(k)
            d["D"] = v

            content.append(d)

    unique_content = remove_duplicates(content)

    return sort_by_d(unique_content)


def food_info(food_content: dict):
    food_sw = load_stopwords("alimentos.json")
    food_match = load_match_information("alimentos.json")

    content = []

    for k, v in food_content.items():
        if k.lower() in food_sw:
            continue

        if food_match.get(k.lower()):
            content.append([first_char_uppercase(food_match.get(k.lower())), v])
            continue

        content.append([first_char_uppercase(k), v])

    duplicates = []
    unique_results = []

    for food, d in content:
        if food in duplicates:
            continue
        else:
            duplicates.append(food)
            unique_results.append([food, d])

    return sort_by_d(unique_results)
