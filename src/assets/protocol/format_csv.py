import pandas as pd
import json
from pathlib import Path

from difflib import SequenceMatcher
from typing import List, Optional, Tuple


def best_string_match(
    query: str,
    terms: List[str],
    early_threshold: float = 0.9,
    min_threshold: float = 0.65,
):

    best_term = None
    best_score = 0.0

    query = query.lower()

    for term in terms:
        score = SequenceMatcher(None, query, term.lower()).ratio()

        # Early return
        if score >= early_threshold:
            return [query, term, score]

        if score > best_score:
            best_score = score
            best_term = term

    if best_score >= min_threshold:
        return [query, best_term, best_score]

    return [query, "", 0]


PARENT = Path(__file__).parent
FILE_NAME = "teste.xlsx"

OBERON_FILE = PARENT.parent / "oberon/correspondencia/microrganismos_atualizado.json"

FILE_DIR = PARENT / FILE_NAME


def load_json_match(file_name):
    FILE = PARENT.parent / f"oberon/correspondencia/{file_name}.json"
    with open(FILE, "r", encoding="utf8") as file:
        data = json.load(file)

    return data


microorganisms = load_json_match("microrganismos_atualizado")
toxins = load_json_match("toxinas_atualizado")

total_info = []

for data in [microorganisms, toxins]:
    for k, v in data.items():
        total_info.append(k.lower())
        total_info.append(v.lower())

df = pd.read_excel(FILE_DIR, skiprows=1)

print(df)

dec_freqs = df[["DESCRIÇÃO", "FREQUENCIA"]]


founded = []
not_founded = []

similarity = []

data_with_frequencies = {}


for d, f in zip(df["DESCRIÇÃO"], df["FREQUENCIA"]):
    fmt_v = d.lower().strip()
    if fmt_v in total_info:
        founded.append(fmt_v)
    else:
        not_founded.append(fmt_v)

    data_with_frequencies[fmt_v] = f
    similarity.append(best_string_match(fmt_v, total_info))


json_summary = {
    "founded": {"total": len(founded), "values": founded},
    "not_founded": {"total": len(not_founded), "values": not_founded},
    "similarities": similarity,
}

with open(PARENT / "summary_results_micro.json", "w", encoding="utf8") as file:
    data = json.dump(json_summary, file, ensure_ascii=False, indent=2)

print("Total encontrado: ", len(founded))
print("Total não encontrado: ", len(not_founded))
print("Total sem similaridade:", len([z for z in similarity if len(z) == 0]))


# Para cada tipo
# Rodar algoritmo de similaridade
# Caso não encontrar, registrar os faltantes
# ! Mas os faltantes devem ser da tabela original usada no relatório.


all_descs = []
all_descs.extend(not_founded)
all_descs.extend(founded)


for dict_data, name in zip([microorganisms, toxins], ["microrganismos", "toxinas"]):
    sum_for_micro = {}
    c = 0
    for k, v in dict_data.items():
        sim_k = best_string_match(k, all_descs)
        sim_v = best_string_match(v, all_descs)

        if sim_k[-1] != 0:
            freq = data_with_frequencies.get(sim_k[1])
            list_content = sim_k.copy()
            sim_k.append(freq)
            sum_for_micro[k] = sim_k
            continue

        if sim_v[-1] != 0:
            freq = data_with_frequencies.get(sim_v[1])
            list_content = sim_v.copy()
            sim_v.append(freq)
            sum_for_micro[v] = sim_v
            continue

        sum_for_micro[v] = ""
        c += 1

    with open(PARENT / f"{name}.json", "w", encoding="utf8") as file:
        data = json.dump(sum_for_micro, file, ensure_ascii=False, indent=2)

    print(f"Relações de {name} encontrados:", len(dict_data) - c)
    print(f"Relações de {name} não encontrados:", c)
