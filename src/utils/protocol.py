from utils.sort_elements import sort_by_d, remove_duplicates

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
    "arsênico",
    "prata",
    "níquel",
]


def metals_treatment_block(toxins_data: list[dict]):
    metals = []

    for d in toxins_data:
        metal_name = d.get("nome")
        if not metal_name:
            continue

        if metal_name.lower() in exclude_metals:
            continue

        metals.append([metal_name, d.get("D")])

    sorted_metals = sort_by_d(metals)
    metals = remove_duplicates(sorted_metals)

    return metals


def microorganisms_treatment_block(
    microrganisms_informations_oberon, microrganisms_informations_prosync
):
    # Remover valores repetidos
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
                [data for data in method if data.get("tipo") == treatment_type]
            )

        protocol_data[treatment_type] = data_for_treatment

    return protocol_data


# ? Análise término
# ================================================================== #

# ========================== Bloco vírus ========================== #

# ? Análise término
# ================================================================== #
