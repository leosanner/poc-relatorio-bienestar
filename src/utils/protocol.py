from utils.sort_elements import sort_by_d, remove_duplicates
from pathlib import Path
import pandas as pd
from pprint import pprint
from collections import Counter
from rich import print
import json

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
# ? Ordem de relevância -> (1º Prosync; 2º Oberon / Metahunter)
# * 1 Fungos
# * 2 Protozoário / Helminto
# * 3 Bactérias
# ! 3 minutos para cada frequência

# TODO: quebrar em intervalos de 1 hora (cada elemento 3 minutos)
# TODO: pegar frequências

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


def microorganisms_frequencies(protocol_data: dict[str:list]):
    summary = {}
    frequencies = load_microorganisms_frequencies()

    for microorganism_type, microorganisms in protocol_data.items():
        if not summary.get(microorganism_type):
            summary[microorganism_type] = {"freq": [], "time": []}

        not_founded = 0

        for microorganism in microorganisms:
            microorganism_data = get_microorganism_frequency(
                microorganism.lower(), frequencies
            )

            if microorganism_data:
                summary[microorganism_type]["freq"].extend(
                    microorganism_data["frequencies"]
                )
                summary[microorganism_type]["time"].extend(
                    microorganism_data["treatment_time"]
                )

            else:
                not_founded += 1

        unique_freq = []
        relative_time = []

        current_frequencies = summary[microorganism_type]["freq"]
        current_treatment_time = summary[microorganism_type]["time"]

        for i in range(0, len(summary[microorganism_type]["freq"])):
            if current_frequencies[i] not in unique_freq:
                unique_freq.append(current_frequencies[i])
                relative_time.append(current_treatment_time[i])

        print("Tamanho antigo: ", len(current_frequencies))
        print("Tamanho novo: ", len(unique_freq))

        summary[microorganism_type]["freq"] = unique_freq
        summary[microorganism_type]["time"] = relative_time

        print(
            f"Resumo microrganismos do tipo: {microorganism_type}, não encontrados: {not_founded}, quantidade total: {len(microorganisms)}\n"
        )

    return summary


def metals_treatment_block(toxins_data: list[dict]):
    metals = []
    print(f"Tamanho dos dados de entrada: {len(toxins_data)}")

    for d in toxins_data:
        metal_name = d.get("nome")
        if not metal_name:
            continue

        if metal_name.lower() in exclude_metals:
            continue

        metals.append([metal_name, d.get("D")])

    return metals


def microorganisms_sessions(frequencies: dict[str:list]):
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
    TOL_TIME = 70 * 60

    for microorganism_type, freq_time in frequencies.items():
        microorganism_sessions = {
            "name": f"RPD - {microorganism_type.title()}",
            "sessions": {0: []},
        }

        session_time = 0
        current_session_idx = 0
        for frequency, treatment_time in zip(freq_time["freq"], freq_time["time"]):
            if session_time > TOL_TIME:
                current_session_idx += 1
                microorganism_sessions["sessions"][current_session_idx] = []
                session_time = 0

            microorganism_sessions["sessions"][current_session_idx].append(
                [frequency, treatment_time]
            )
            session_time += float(treatment_time) if len(treatment_time) > 0 else 0

        sessions_data.append(microorganism_sessions)

    return sessions_data


def microorganisms_treatment_block(
    microrganisms_informations_oberon, microrganisms_informations_prosync
):
    protocol_data = format_microorganism_content(
        microrganisms_informations_oberon, microrganisms_informations_prosync
    )

    frequencies = microorganisms_frequencies(protocol_data)
    sessions = microorganisms_sessions(frequencies)
    # Formatar para docx template
    # Fazer alguns testes para apurar se está correto


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
