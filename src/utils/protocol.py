from itertools import groupby
from docxtpl import DocxTemplate
from io import BytesIO
from pathlib import Path
import pandas as pd
from collections import Counter
from rich import print
from utils.format_string import first_char_uppercase
import json

TOL_TIME = 70 * 60

path = Path(__file__).parent.parent
PROTOCOL_TEMPLATE_PATH = path / "assets/protocol/template_protocolo_microrganismos.docx"
ASSETS = path / "assets"
PROTOCOL_ASSETS_PATH = ASSETS / "protocol"

# Desenvolvimento do protocolo
# Microrganismo de 0,000 até 0,350 – estarão em preto no relatório e na 1ª etapa do protocolo
# Microrganismo de 0,351 até 0,450 - estarão em laranja no relatório e na 2ª etapa do protocolo
# Microrganismo considerados perigoso sempre na 1ª etapa do protocolo
# Microrganismos que não tem frequência no RPD, colocar na sessão de Metaterapia Oberon
# No relatório colocar apenas o microrganismo “adulto”, os spores, eggs e unicubated serão colocados no protocolo e orçamento. Exemplo: Fascíola hepática (relatório/protocolo/orçamento), Fascíola hepática eggs (protocolo/orçamento)
# No Protocolo montar as sessões de RPD por tipo de microrganismo “grupinhos/família” (bactéria, fungo, hetelmintos, protozoário), por exemplo: todas as fascíolas, fasciolopsis juntos, todos os clostridium juntos.

# ========================== Procedimento Padrão Metais ========================== #
# ? Primeira etapa -> detox
# * Bloco geral para todos pacientes
# ? Análise término
# ================================================================== #

# ========================== Bloco parasitas ========================== #


def load_json(path_: Path | str) -> dict:
    with open(path_, "r", encoding="utf-8") as file:
        return json.load(file)


def write_json_file(file_name: str, obj):
    with open(f"{file_name}.json", "w", encoding="utf8") as file:
        json.dump(obj, file, indent=2, ensure_ascii=False)


exclude_metals = [
    "cádmio",
    "mercúrio",
    "chumbo",
    "alumínio",
    "arsênio",
    "prata",
    "níquel",
]


def isNaN(value):
    return value != value


def write_not_found_elements(names: list[str], path: Path):
    try:
        with open(path, "r", encoding="utf8") as file:
            data = json.load(file)

    except FileNotFoundError as error:
        data = []

    if not isinstance(data, list):
        return

    unique_elements = list(set(data))

    for name in names:
        if name not in unique_elements:
            unique_elements.append(name)

    with open(path, "w", encoding="utf8") as file:
        json.dump(unique_elements, file, ensure_ascii=False, indent=2)


def load_microorganisms(file_name: str = "nova_versao_microrganismos.json"):
    path = PROTOCOL_ASSETS_PATH / file_name
    raw_data = load_json(path)
    data = {}

    for microorganism_name, frequency_time_list in raw_data.items():
        normalized_name = microorganism_name.strip().lower()
        data[normalized_name] = {
            "frequencies": [],
            "treatment_time": [],
        }

        for pair in frequency_time_list:
            frequency = pair[0] if len(pair) > 0 else " "
            time = pair[1] if len(pair) > 1 else " "

            if frequency in [None, ""]:
                frequency = " "
            if time in [None, ""]:
                time = " "

            data[normalized_name]["frequencies"].append(frequency)
            data[normalized_name]["treatment_time"].append(time)

    return data


def load_microorganisms_frequencies():
    path = (
        Path(__file__).parent.parent / "assets/protocol/microrganismos_encontrados.csv"
    )

    df = pd.read_csv(path)
    df.columns = ["name", "frequency", "time"]
    data = {}

    for t in df.itertuples():

        if isNaN(t.frequency) or isNaN(t.time):
            continue

        microorganism_name = t.name.lower()
        freqs = t.frequency.split(",")
        treatment_time = t.time.split(",")

        data[microorganism_name] = {
            "frequencies": freqs,
            "treatment_time": treatment_time,
        }

    return data


def get_microorganism_frequency(microorganism_name: str, frequencies: dict):

    return frequencies.get(microorganism_name)


def microorganisms_frequencies(protocol_data: dict[str, list]):
    summary = {}
    frequencies = load_microorganisms()
    not_founded_to_export = []

    for microorganism_type, microorganisms in protocol_data.items():
        if not summary.get(microorganism_type):
            summary[microorganism_type] = {
                "freq": [],
                "time": [],
                "microorganism_name": [],
            }

        not_founded = []

        for microorganism in microorganisms:
            microorganism_data = get_microorganism_frequency(
                microorganism.lower(), frequencies
            )

            if microorganism_data:
                treatment_time_updated = [
                    treat_time if treat_time not in [" ", ""] else "180"
                    for treat_time in microorganism_data["treatment_time"]
                ]

                summary[microorganism_type]["freq"].extend(
                    microorganism_data["frequencies"]
                )
                summary[microorganism_type]["time"].extend(treatment_time_updated)
                summary[microorganism_type]["microorganism_name"].extend(
                    [
                        microorganism
                        for _ in range(len(microorganism_data["frequencies"]))
                    ]
                )

            else:
                not_founded_to_export.append(microorganism)
                not_founded.append(microorganism)

        unique_freq = []
        relative_time = []
        unique_microorganism_name = []

        current_frequencies = summary[microorganism_type]["freq"]
        current_treatment_time = summary[microorganism_type]["time"]
        current_names = summary[microorganism_type]["microorganism_name"]

        for i in range(0, len(summary[microorganism_type]["freq"])):
            if current_frequencies[i] not in unique_freq:
                unique_freq.append(current_frequencies[i])
                relative_time.append(current_treatment_time[i])
                unique_microorganism_name.append(current_names[i])

        summary[microorganism_type]["freq"] = unique_freq
        summary[microorganism_type]["time"] = relative_time
        summary[microorganism_type]["microorganism_name"] = unique_microorganism_name

    return (summary, not_founded_to_export)


# ================== Toxinas ================== #


def load_metals_content():
    metals = load_json(PROTOCOL_ASSETS_PATH / "toxinas_manus.json")

    return metals


def process_metals_content_from_prosync(toxins_data: list[dict]):
    metals = []

    for d in toxins_data:
        metal_name = d.get("nome")
        if not metal_name:
            continue

        if metal_name.lower() in exclude_metals:
            continue

        metals.append(metal_name)

    return metals


def compare_metals_to_table_frequencies(metals_name: list[str]):
    toxins_metadata = load_metals_content()
    toxins_metadata_keys = [k.lower().strip() for k in list(toxins_metadata.keys())]
    toxins_metadata_oberon_names = [
        v.get("oberon_name").lower() for v in toxins_metadata.values()
    ]

    not_founded = []
    founded = []

    for metal in metals_name:
        if (
            metal.lower() not in toxins_metadata_keys
            and metal.lower() not in toxins_metadata_oberon_names
        ):
            not_founded.append(metal.lower())
            continue

        elif toxins_metadata.get(metal.lower()):
            toxin_content = toxins_metadata.get(metal.lower(), {})
            founded.append(
                {
                    "display_name": metal.lower(),
                    "freq": toxin_content.get("frequency"),
                    "time": toxin_content.get("time"),
                }
            )

        else:
            for k, v in toxins_metadata.items():
                if v.get("oberon_name").lower() == metal.lower():
                    founded.append(
                        {
                            "display_name": metal.lower(),
                            "freq": v.get("frequency"),
                            "time": v.get("time"),
                        }
                    )
                    break

    return founded, not_founded


def metals_docx_format(treatment_content: list[list]):
    docx_sessions = []

    for session_treatment in treatment_content:
        sessions_by_toxin_name = {}

        for treatment in session_treatment:
            if treatment[0] not in sessions_by_toxin_name:
                sessions_by_toxin_name[treatment[0]] = []

            sessions_by_toxin_name[treatment[0]].append(", ".join(treatment[1:]))

        docx_sessions.append(
            "\n".join(
                [
                    f"#{first_char_uppercase(k)}\n{"\n".join(v)}"
                    for k, v in sessions_by_toxin_name.items()
                ]
            )
        )

    return docx_sessions


def format_metals_content_to_docx(founded: list[dict], tol_time: int = TOL_TIME):
    sessions: list[list] = []
    current_session = []
    current_session_time = 0

    for toxin_treatment_content in founded:
        toxin_name = toxin_treatment_content.get("display_name")
        frequencies = toxin_treatment_content.get("freq", [])
        times = toxin_treatment_content.get("time", [])

        for freq, time in zip(frequencies, times):
            if current_session_time >= tol_time:
                sessions.append(current_session)
                current_session = []
                current_session_time = 0

            current_session_time += float(time)
            current_session.append([toxin_name, freq, time])

    sessions.append(current_session)
    return metals_docx_format(sessions)


def metals_treatment_block(toxins_data: list[dict]):
    metals = process_metals_content_from_prosync(toxins_data)
    founded, not_founded = compare_metals_to_table_frequencies(metals)
    content_for_docx = format_metals_content_to_docx(founded)

    return content_for_docx, not_founded


# Arrumar esta parte, adicionar para cada sessão o nome do microorganismo
def microorganisms_sessions(frequencies: dict[str, list]):
    # receber frequências
    # quebrar em blocos por tipo
    # quebrar em sessões de 1 hora
    """
    {
        nome: ex: "RPD - Vírus",
        sessões: {
            0: [[frequência, tempo]]
        }
    }
    """
    sessions_data = []

    for microorganism_type, freq_time in frequencies.items():
        microorganism_sessions = {
            "name": f"RPD - {microorganism_type.title()}",
            "sessions": {0: []},
        }

        session_time = 0
        current_session_idx = 0
        for frequency, treatment_time, microorganism_name in zip(
            freq_time["freq"], freq_time["time"], freq_time["microorganism_name"]
        ):
            if session_time > TOL_TIME:
                current_session_idx += 1
                microorganism_sessions["sessions"][current_session_idx] = []
                session_time = 0

            microorganism_sessions["sessions"][current_session_idx].append(
                [frequency, treatment_time, microorganism_name]
            )
            session_time += float(treatment_time) if len(treatment_time) > 0 else 0

        sessions_data.append(microorganism_sessions)

    return sessions_data


def format_microorganism_content_sessions(data: list[dict]):
    all_sessions = []

    for microorganism_type in data:
        name = microorganism_type.get("name", "")
        type_ = name.split("-")[-1].strip()
        for sessions in microorganism_type.get("sessions", {}).values():
            for session in sessions:
                s = session.copy()
                s.append(type_)
                all_sessions.append(s)

    return all_sessions


def build_sessions(data: list[dict], tol_time: int = TOL_TIME) -> list[list]:
    sessions_complete_content = []
    frequencies = format_microorganism_content_sessions(data)
    session_content = []
    session_total_time = 0

    for list_ in frequencies:
        f_time = list_[1]
        if not len(f_time) > 0:
            continue

        session_content.append(list_)
        session_total_time += float(f_time)

        if float(session_total_time) >= tol_time:
            sessions_complete_content.append(session_content)
            session_content = []
            session_total_time = 0

    if len(session_content) > 0:
        sessions_complete_content.append(session_content)

    return sessions_complete_content


def microorganisms_content_docx(frequencies: list[list]):
    docx_content = []

    for session in frequencies:
        session_data = {}

        for row in session:
            microorganism = row[2].lower()
            row_freq_time_content = ",".join([row[0], row[1]])

            if session_data.get(microorganism):
                session_data[microorganism].append(row_freq_time_content)
            else:
                session_data[microorganism] = [row_freq_time_content]

        session_for_docx = "\n".join(
            ["\n".join([f"#{k}", "\n".join(v)]) for k, v in session_data.items()]
        )

        docx_content.append(session_for_docx)

    return docx_content


def format_microorganisms_to_docx(data: list[dict]):
    frequencies = build_sessions(data)
    content_for_docx = microorganisms_content_docx(frequencies)
    return content_for_docx


def add_midterm_analysis_sessions(docx_content, sessions_for_analysis: int = 9):
    output_content = []

    for idx, content in enumerate(docx_content):
        if ((idx + 1) % sessions_for_analysis) == 0:
            output_content.append("sessão de alinhamento")
        output_content.append(content)

    return output_content


def microorganisms_treatment_block(
    microrganisms_informations_oberon, microrganisms_informations_prosync
):
    protocol_data = format_microorganism_content(
        microrganisms_informations_oberon, microrganisms_informations_prosync
    )
    frequencies, not_founded = microorganisms_frequencies(protocol_data)
    sessions = microorganisms_sessions(frequencies)
    formated_docx = format_microorganisms_to_docx(sessions)
    content_with_additional_analysis = add_midterm_analysis_sessions(formated_docx)

    return content_with_additional_analysis, not_founded


def format_microorganism_content(
    microrganisms_informations_oberon, microrganisms_informations_prosync
):
    order_treatment = ["fungo", "helminto", "protozoário", "bactéria", "vírus"]
    order_treatment = [c.title() for c in order_treatment]

    relevance = [microrganisms_informations_oberon]

    if microrganisms_informations_prosync:
        relevance.insert(0, microrganisms_informations_prosync)

    protocol_data = {treatment: {} for treatment in order_treatment}

    for treatment_type in order_treatment:
        data_for_treatment = []

        for method in relevance:
            data_for_treatment.extend(
                [
                    data.get("nome").lower()
                    for data in method
                    if data.get("tipo") == treatment_type
                ]
            )

        protocol_data[treatment_type] = list(Counter(data_for_treatment))

    return protocol_data


# ? Análise término
# ================================================================== #

# ========================== Bloco vírus ========================== #

# ? Análise término
# ================================================================== #


# Implementação do protocolo
def generate_protocol(protocol_content):
    microorganisms_prosync = protocol_content.get("table_prosync", {})
    microorganisms_oberon = protocol_content.get("table_microorganism", {})
    toxins = protocol_content.get("table_toxins", {})

    t_t_b, not_founded_metals = metals_treatment_block(toxins)
    m_t_b, not_founded_microorganisms = microorganisms_treatment_block(
        microorganisms_prosync, microorganisms_oberon
    )

    if not PROTOCOL_TEMPLATE_PATH.exists():
        print(f"Template not found at {PROTOCOL_TEMPLATE_PATH}")
        return

    content = {
        "name": "Nome teste",
        "microorganisms_protocol": m_t_b,
        "microorganisms_not_founded": not_founded_microorganisms,
        "metals_protocol": t_t_b,
        "metals_not_founded": not_founded_metals,
    }

    doc = DocxTemplate(PROTOCOL_TEMPLATE_PATH)
    doc.render(content)

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    return buffer
