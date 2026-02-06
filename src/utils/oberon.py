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
    "clamydia",
    "chlamydia",
    "Cryptococcus neoformans",
    "cytomegalovirus",
    "epstein barr",
    "h. pylori",
    "meningitidis",
    "mycobacterium tuberculosis",
    "staphylococcus",
    "streptococcus",
    "Streptococcus pneumoniae",
    "papiloma",
    "hepatite",
    "varicela",
    "haemophilus influenza",
]


def verify_parentesis(text: str):
    return ("(" in text) and (")" in text)


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
    oberon_microorganism_content: dict,
    json_file="microrganismos_atualizado.json",
    for_prosync=False,
):

    DEFAULT_VALUE = {
        "nome": "",
        "sintomas": "não encontrado",
        "fonte": "Não encontrado",
        "tipo": "não encontrado",
    }

    scpecial_micro = [
        "Hepatite D",
        "Hepatite C",
        "Hepatite E",
        "Hepatite B",
        "Influenza A",
        "Hepadnovirus B",
        "Salmonella paratyphi B",
        "Coxsackie B4",
    ]

    content = []
    control = None
    if for_prosync:

        for k, v in oberon_microorganism_content.items():
            if k.lower() == "controle":
                control = {"nome": "Controle", "D": int(v)}

    microorganism_sw = load_stopwords("microrganismos.json")
    microorganism_information = load_test_information(json_file)
    microorganism_match = load_match_information(json_file)

    microorganism_sw = [w.lower() for w in microorganism_sw]

    for k, v in oberon_microorganism_content.items():
        formated_key = k.title()
        new_obj = {}

        if k.lower() in microorganism_sw:
            continue

        if microorganism_match.get(formated_key):
            match_name = microorganism_match.get(formated_key).title()
            if match_name.lower() in microorganism_sw:
                continue

            for m_type, objs in microorganism_information.items():
                for obj in objs:
                    if obj["nome"].title() == match_name:

                        if obj["nome"].lower() in scpecial_micro:
                            new_obj["nome"] = match_name.title()

                        elif verify_parentesis(obj["nome"]):
                            new_obj["nome"] = match_name

                        else:
                            new_obj["nome"] = first_char_uppercase(match_name)

                        new_obj["D"] = v
                        new_obj["tipo"] = m_type.title()
                        new_obj["sintomas"] = obj["sintomas"]
                        content.append(new_obj)

                        break
        else:
            d = DEFAULT_VALUE.copy()
            d["nome"] = first_char_uppercase(k)
            d["D"] = v

            content.append(d)

    sorted_elements = sort_by_d(content)  # ver exemplo com reverse
    unique_content = remove_duplicates(sorted_elements)

    if control:
        unique_content.insert(0, control)

    return unique_content


def food_info(food_content: dict):
    food_sw = load_stopwords("alimentos.json")
    food_sw = [f.lower() for f in food_sw]
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

    results_sorted = sort_by_d(unique_results)

    output_results_splitted = [{} for _ in range(3)]

    for food_name, food_value in results_sorted:
        if 0 <= float(food_value) <= 0.300:
            output_results_splitted[0][food_name] = food_value

        if 0.300 < float(food_value) <= 1:
            output_results_splitted[1][food_name] = food_value

        if float(food_value) > 1:
            output_results_splitted[2][food_name] = food_value

    return output_results_splitted


def emotions_info(emotions_content: dict):
    formated_content = {}
    formated_content = dict(
        sorted(emotions_content.items(), key=lambda x: x[1], reverse=False)
    )

    emotions_stopwords = load_stopwords("emocoes.json")
    emotions_match = load_match_information("emocoes.json")

    formated_content = {
        k.lower(): v
        for k, v in formated_content.items()
        if k.lower() not in emotions_stopwords
    }
    formated_content_matched = {}

    for k, v in formated_content.items():
        if emotions_match.get(k):
            formated_content_matched[emotions_match.get(k)] = v

        else:
            formated_content_matched[k] = v

    return {first_char_uppercase(k): v for k, v in formated_content_matched.items()}


def patologies_info(patologies_content: dict):
    matchs = load_match_information("patologias.json")
    formated_content = {}

    for patologie_name, d in patologies_content.items():
        match = matchs.get(patologie_name.strip().lower())
        name_in_file = match if match else patologie_name.strip().lower()
        formated_content[name_in_file] = d

    formated_content = dict(
        sorted(patologies_content.items(), key=lambda x: x[1], reverse=False)
    )

    return {first_char_uppercase(k): v for k, v in formated_content.items()}
