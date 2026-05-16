import hashlib
import base64
import html
import json
import re
import time
from pathlib import Path

from utils.oberon import toxins_info, crystal_info, microorganism_info
from utils.budget import format_currency, generate_budget
import streamlit as st
import pandas as pd
from typing import get_args
from utils.prosync import extract_prosync_content
from utils.oberon import (
    extract_oberon_content,
    food_info,
    emotions_info,
    patologies_info,
)
from utils.report import (
    generate_report,
    prosync_table_content,
    generate_content_for_report,
)
from typing import Literal
from utils.protocol import generate_protocol
from utils.extra_sessions_sheet import (
    build_catalog_options_for_clinic,
    build_selected_session_price_lookup,
    load_extra_sessions_catalog,
)
from utils.anamnesis_sheet import (
    INVALID_ANAMNESIS_ACCESS_SECRET_MESSAGE,
    LOCKED_ANAMNESIS_MESSAGE,
    MISSING_ANAMNESIS_ACCESS_SECRET_MESSAGE,
    NO_ANAMNESIS_FOUND_MESSAGE,
    build_report_anamnesis_rows,
    build_question_answer_rows,
    format_candidate_label,
    get_configured_anamnesis_access_secret,
    is_anamnesis_access_authorized,
    load_anamnesis_lookup,
    resolve_report_patient_name,
)

availableCompanies = Literal["Bienestar", "Alecrim", "VitaeFlux"]
ANAMNESIS_FORM_URLS: dict[str, str | None] = {
    "Bienestar": (
        "https://docs.google.com/forms/d/e/"
        "1FAIpQLSdF61RuGcVsBEe5ikuwVKqevD7Qtil9fwgD-E5N9nhErvDi-Q/viewform"
    ),
    "Alecrim": None,
    "VitaeFlux": None,
}

SELECTION_COLUMN = "Selecionado"
ROOT = Path(__file__).parent
OBERON_ASSETS_PATH = ROOT / "assets" / "oberon"
EXTRA_SESSIONS_CATALOG_STATE_KEY = "extra_sessions_catalog_state"
EXTRA_SESSIONS_COMPANY_STATE_KEY = "extra_sessions_catalog_company"
ANAMNESIS_LOOKUP_STATE_KEY = "anamnesis_lookup_state"
ANAMNESIS_CONTEXT_STATE_KEY = "anamnesis_lookup_context"
ANAMNESIS_SELECTED_ROWS_STATE_KEY = "anamnesis_selected_question_rows"
ANAMNESIS_ACCESS_GRANTED_STATE_KEY = "anamnesis_access_granted"
ANAMNESIS_QUESTION_TABLE_KEY = "anamnesis_questions"
ANAMNESIS_SUPPORTED_COMPANIES = {"Bienestar", "VitaeFlux"}
ANAMNESIS_SECRET_PREFIX_BY_COMPANY = {
    "Bienestar": "bienestar",
    "VitaeFlux": "vitaeflux",
}

SYSTEM_DATA_CATEGORIES = {
    "toxinas": {
        "label": "Toxinas",
        "match_file": "toxinas_atualizado.json",
        "info_file": "toxinas_atualizado.json",
        "info_columns": ["Nome", "Efeitos"],
    },
    "emocoes": {
        "label": "Emoções",
        "match_file": "emocoes.json",
        "info_file": None,
        "info_columns": [],
    },
    "microrganismos": {
        "label": "Microrganismos",
        "match_file": "microrganismos_atualizado.json",
        "info_file": "microrganismos_atualizado.json",
        "info_columns": ["Tipo", "Nome", "Sintomas"],
    },
    "cristais": {
        "label": "Cristais",
        "match_file": "cristais.json",
        "info_file": "cristais.json",
        "info_columns": [
            "Nome",
            "Benefícios físicos",
            "Benefícios emocionais",
        ],
    },
    "alimentos": {
        "label": "Alimentos",
        "match_file": "alimentos.json",
        "info_file": None,
        "info_columns": [],
    },
    "patologias": {
        "label": "Patologias",
        "match_file": "patologias.json",
        "info_file": None,
        "info_columns": [],
    },
}


def build_table_signature(records: list[dict]) -> str:
    return json.dumps(records, ensure_ascii=False, sort_keys=True, default=str)


def table_columns_to_records(table_content: dict[str, list]) -> list[dict]:
    if not table_content:
        return []

    columns = list(table_content.keys())
    row_count = max((len(values) for values in table_content.values()), default=0)
    records = []

    for row_index in range(row_count):
        records.append(
            {
                column: (
                    table_content[column][row_index]
                    if row_index < len(table_content[column])
                    else ""
                )
                for column in columns
            }
        )

    return records


def render_selectable_table(
    source_records: list[dict],
    state_key: str,
    display_records: list[dict] | None = None,
):
    display_records = source_records if display_records is None else display_records
    signature = build_table_signature(source_records)
    signature_key = f"{state_key}_signature"
    selection_key = f"{state_key}_selection"

    if st.session_state.get(signature_key) != signature:
        st.session_state[signature_key] = signature
        st.session_state[selection_key] = [True] * len(source_records)

    selected_rows = st.session_state.get(selection_key, [True] * len(source_records))
    if len(selected_rows) != len(source_records):
        selected_rows = [True] * len(source_records)
        st.session_state[selection_key] = selected_rows

    editor_df = pd.DataFrame(display_records).copy()
    editor_df.insert(0, SELECTION_COLUMN, selected_rows)

    widget_key = (
        f"{state_key}_editor_"
        f"{hashlib.md5(signature.encode('utf-8')).hexdigest()[:12]}"
    )
    edited_df = st.data_editor(
        editor_df,
        key=widget_key,
        hide_index=True,
        use_container_width=True,
        disabled=[column for column in editor_df.columns if column != SELECTION_COLUMN],
        column_config={
            SELECTION_COLUMN: st.column_config.CheckboxColumn(
                SELECTION_COLUMN,
                default=True,
            )
        },
    )

    current_selection = edited_df[SELECTION_COLUMN].fillna(False).astype(bool).tolist()
    st.session_state[selection_key] = current_selection

    return [
        row for row, is_selected in zip(source_records, current_selection) if is_selected
    ]


def load_json_file(path: str):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def normalize_lookup_key(value) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def build_information_index(category_key: str, info_data) -> dict[str, dict]:
    if category_key == "toxinas":
        return {
            normalize_lookup_key(item.get("nome")): {
                "Nome": item.get("nome", ""),
                "Efeitos": item.get("efeitos", ""),
            }
            for item in info_data
            if item.get("nome")
        }

    if category_key == "cristais":
        return {
            normalize_lookup_key(item.get("cristal")): {
                "Nome": item.get("cristal", ""),
                "Benefícios físicos": item.get("beneficios_fisicos", ""),
                "Benefícios emocionais": item.get("beneficios_emocionais", ""),
            }
            for item in info_data
            if item.get("cristal")
        }

    if category_key == "microrganismos":
        index = {}
        for microorganism_type, microorganisms in info_data.items():
            for item in microorganisms:
                name = item.get("nome")
                if not name:
                    continue

                index[normalize_lookup_key(name)] = {
                    "Tipo": microorganism_type.title(),
                    "Nome": name,
                    "Sintomas": item.get("sintomas", ""),
                }
        return index

    return {}


def build_system_data_rows(category_key: str) -> list[dict]:
    category = SYSTEM_DATA_CATEGORIES[category_key]
    match_path = OBERON_ASSETS_PATH / "correspondencia" / category["match_file"]
    match_data = load_json_file(str(match_path))

    information_index = {}
    if category["info_file"]:
        info_path = OBERON_ASSETS_PATH / "informacoes" / category["info_file"]
        info_data = load_json_file(str(info_path))
        information_index = build_information_index(category_key, info_data)

    rows = []
    for input_value, system_value in match_data.items():
        row = {
            "Dado que entra no sistema": input_value,
            "Valor correspondente no sistema": system_value,
        }
        row.update(information_index.get(normalize_lookup_key(system_value), {}))

        for column in category["info_columns"]:
            row.setdefault(column, "")

        rows.append(row)

    return sorted(
        rows,
        key=lambda row: normalize_lookup_key(row["Dado que entra no sistema"]),
    )


def filter_system_data(df: pd.DataFrame, search_term: str) -> pd.DataFrame:
    if not search_term:
        return df

    normalized_search = search_term.strip()
    if not normalized_search:
        return df

    matches = df.astype(str).apply(
        lambda column: column.str.contains(
            normalized_search, case=False, na=False, regex=False
        )
    )
    return df[matches.any(axis=1)]


def normalize_file_name_part(value: str) -> str:
    normalized = re.sub(r"\s+", "_", str(value or "").strip())
    normalized = re.sub(r"[^0-9A-Za-zÀ-ÖØ-öø-ÿ_-]+", "", normalized)
    return normalized or "sem_nome"


def build_output_file_name(
    document_type: str,
    company_name: str,
    patient_name: str,
) -> str:
    file_parts = [
        document_type,
        normalize_file_name_part(company_name),
    ]
    if patient_name:
        file_parts.append(normalize_file_name_part(patient_name))

    return f"{'_'.join(file_parts)}.docx"


def render_system_data_tab():
    st.title("Dados do Sistema")
    st.write("Consulte as correspondências usadas internamente pelo sistema.")

    category_labels = {
        key: category["label"] for key, category in SYSTEM_DATA_CATEGORIES.items()
    }
    selected_category = st.selectbox(
        "Tipo de dado",
        options=list(category_labels.keys()),
        format_func=lambda key: category_labels[key],
        key="system_data_category",
    )
    search_term = st.text_input(
        "Buscar",
        placeholder="Digite para filtrar por qualquer coluna",
        key="system_data_search",
    )

    rows = build_system_data_rows(selected_category)
    df = pd.DataFrame(rows)
    filtered_df = filter_system_data(df, search_term)

    st.caption(f"{len(filtered_df)} de {len(df)} registros exibidos")
    st.dataframe(filtered_df, hide_index=True, use_container_width=True)


def render_docx_download_link(label: str, data, file_name: str):
    if hasattr(data, "getvalue"):
        file_bytes = data.getvalue()
    else:
        file_bytes = data

    encoded_file = base64.b64encode(file_bytes).decode("utf-8")
    safe_label = html.escape(label)
    safe_file_name = html.escape(file_name, quote=True)

    st.markdown(
        (
            f'<a href="data:application/vnd.openxmlformats-officedocument.'
            f'wordprocessingml.document;base64,{encoded_file}" '
            f'download="{safe_file_name}" '
            f'style="display:inline-block;padding:0.5rem 0.75rem;'
            f'margin:0.25rem 0;border:1px solid rgba(49,51,63,0.2);'
            f'border-radius:8px;text-decoration:none;color:inherit;">'
            f"{safe_label}</a>"
        ),
        unsafe_allow_html=True,
    )


def render_anamnesis_form_link(company_name: availableCompanies):
    form_url = ANAMNESIS_FORM_URLS.get(company_name)

    if form_url:
        st.link_button("Abrir formulário de anamnese", form_url)
    else:
        st.info("Formulário de anamnese da clínica ainda não disponível.")


def read_secret_section(section_name: str) -> dict:
    try:
        section = st.secrets[section_name]
    except Exception:
        return {}

    return {key: section[key] for key in section.keys()}


def clear_anamnesis_lookup_state():
    keys_to_clear = [
        ANAMNESIS_LOOKUP_STATE_KEY,
        ANAMNESIS_SELECTED_ROWS_STATE_KEY,
        "anamnesis_candidate_index",
        f"{ANAMNESIS_QUESTION_TABLE_KEY}_signature",
        f"{ANAMNESIS_QUESTION_TABLE_KEY}_selection",
    ]
    for key in keys_to_clear:
        st.session_state.pop(key, None)


def revoke_anamnesis_access():
    clear_anamnesis_lookup_state()
    st.session_state.pop(ANAMNESIS_ACCESS_GRANTED_STATE_KEY, None)


def reset_anamnesis_lookup_on_context_change(
    company_name: str,
    patient_name: str,
):
    context = {
        "company_name": company_name,
        "patient_name": patient_name,
    }
    previous_context = st.session_state.get(ANAMNESIS_CONTEXT_STATE_KEY)

    if previous_context is None:
        st.session_state[ANAMNESIS_CONTEXT_STATE_KEY] = context
        return

    if previous_context != context:
        clear_anamnesis_lookup_state()
        st.session_state[ANAMNESIS_CONTEXT_STATE_KEY] = context


def get_anamnesis_sheet_config(company_name: str) -> dict:
    prefix = ANAMNESIS_SECRET_PREFIX_BY_COMPANY.get(company_name)
    if not prefix:
        return {}

    google_sheets_config = read_secret_section("google_sheets")
    return {
        "spreadsheet_id": google_sheets_config.get(
            f"{prefix}_anamnesis_spreadsheet_id"
        ),
        "worksheet_name": google_sheets_config.get(f"{prefix}_anamnesis_tab"),
        "name_column": google_sheets_config.get(f"{prefix}_anamnesis_name_column"),
    }


def render_anamnesis_access_gate() -> bool:
    google_sheets_config = read_secret_section("google_sheets")
    configured_secret = get_configured_anamnesis_access_secret(google_sheets_config)

    if not configured_secret:
        revoke_anamnesis_access()
        st.info(MISSING_ANAMNESIS_ACCESS_SECRET_MESSAGE)
        return False

    submitted_secret = st.text_input(
        "Secret da anamnese",
        type="password",
        key="anamnesis_access_secret_input",
    )

    if not submitted_secret:
        revoke_anamnesis_access()
        st.info(LOCKED_ANAMNESIS_MESSAGE)
        return False

    if not is_anamnesis_access_authorized(google_sheets_config, submitted_secret):
        revoke_anamnesis_access()
        st.warning(INVALID_ANAMNESIS_ACCESS_SECRET_MESSAGE)
        return False

    st.session_state[ANAMNESIS_ACCESS_GRANTED_STATE_KEY] = True
    return True


def render_anamnesis_lookup_section(
    company_name: availableCompanies,
    patient_name: str,
):
    st.markdown("### Anamnese")
    has_anamnesis_access = render_anamnesis_access_gate()
    is_supported_company = company_name in ANAMNESIS_SUPPORTED_COMPANIES

    if not is_supported_company:
        st.info("Anamnese indisponível para esta clínica nesta versão.")

    search_clicked = st.button(
        "Buscar",
        key="anamnesis_search_button",
        disabled=not has_anamnesis_access or not is_supported_company,
    )

    if not has_anamnesis_access or not is_supported_company:
        return

    reset_anamnesis_lookup_on_context_change(company_name, patient_name)

    if search_clicked:
        search_term = patient_name.strip()
        clear_anamnesis_lookup_state()

        if not search_term:
            st.session_state[ANAMNESIS_LOOKUP_STATE_KEY] = {
                "status": "validation_error",
                "message": "Informe o nome do paciente antes de buscar a anamnese.",
                "candidates": [],
            }
        else:
            config = get_anamnesis_sheet_config(company_name)
            service_account_info = read_secret_section("google_service_account")
            st.session_state[ANAMNESIS_LOOKUP_STATE_KEY] = load_anamnesis_lookup(
                clinic_name=company_name,
                search_term=search_term,
                spreadsheet_id=config.get("spreadsheet_id"),
                worksheet_name=config.get("worksheet_name"),
                configured_name_column=config.get("name_column"),
                service_account_info=service_account_info or None,
            )

    lookup_state = st.session_state.get(ANAMNESIS_LOOKUP_STATE_KEY)
    if not lookup_state:
        st.info("Use o nome do paciente acima e clique em Buscar para consultar a anamnese.")
        return

    status = lookup_state.get("status")
    message = lookup_state.get("message")

    if status == "validation_error":
        st.warning(message)
        return

    if status == "not_found":
        st.warning(message or NO_ANAMNESIS_FOUND_MESSAGE)
        return

    if status in {"error", "unavailable"}:
        st.error(message)
        return

    candidates = lookup_state.get("candidates", [])
    if not candidates:
        st.warning(NO_ANAMNESIS_FOUND_MESSAGE)
        return

    if len(candidates) == 1:
        selected_candidate_index = 0
        st.caption(format_candidate_label(candidates[0]))
    else:
        selected_candidate_index = st.selectbox(
            "Resposta encontrada",
            options=list(range(len(candidates))),
            format_func=lambda index: format_candidate_label(candidates[index]),
            key="anamnesis_candidate_index",
        )

    selected_candidate = candidates[selected_candidate_index]
    question_answer_rows = build_question_answer_rows(selected_candidate["record"])
    selected_rows = render_selectable_table(
        question_answer_rows,
        ANAMNESIS_QUESTION_TABLE_KEY,
    )
    st.session_state[ANAMNESIS_SELECTED_ROWS_STATE_KEY] = selected_rows


def get_extra_sessions_catalog_state() -> dict:
    if EXTRA_SESSIONS_CATALOG_STATE_KEY not in st.session_state:
        google_sheets_config = read_secret_section("google_sheets")
        service_account_info = read_secret_section("google_service_account")
        catalog_state = load_extra_sessions_catalog(
            spreadsheet_id=google_sheets_config.get("spreadsheet_id"),
            worksheet_name=google_sheets_config.get("extra_sessions_tab"),
            service_account_info=service_account_info or None,
        )
        catalog_state["loaded_at"] = time.time()
        st.session_state[EXTRA_SESSIONS_CATALOG_STATE_KEY] = catalog_state

    return st.session_state[EXTRA_SESSIONS_CATALOG_STATE_KEY]


def invalidate_extra_sessions_cache_on_company_change(company_name: str):
    previous_company = st.session_state.get(EXTRA_SESSIONS_COMPANY_STATE_KEY)

    if previous_company == company_name:
        return

    st.session_state[EXTRA_SESSIONS_COMPANY_STATE_KEY] = company_name
    st.session_state.pop(EXTRA_SESSIONS_CATALOG_STATE_KEY, None)


def format_extra_session_option_label(option: dict) -> str:
    prices = option["prices"]
    return (
        f"{option['treatment_name']} - PIX {format_currency(prices['pix'])} "
        f"| Cartão {format_currency(prices['cartao'])}"
    )


def sync_selected_extra_sessions(available_options: list[dict]):
    available_names = {option["treatment_name"] for option in available_options}
    current_selected = st.session_state.get("selected_extra_sessions", [])
    valid_selected = [name for name in current_selected if name in available_names]

    if current_selected != valid_selected:
        removed_sessions = set(current_selected) - set(valid_selected)
        st.session_state["selected_extra_sessions"] = valid_selected
        for session_name in removed_sessions:
            st.session_state.pop(f"extra_session_quantity_{session_name}", None)


st.set_page_config(page_title="Bienestar POC", layout="wide")

st.title("Bienestar POC")
processing_tab, system_data_tab = st.tabs(["Processamento", "Dados do Sistema"])

with processing_tab:
    st.title("Processamento de Arquivos")

    st.markdown("### Informações do Atendimento")
    clinic_column, patient_column = st.columns(2)
    with clinic_column:
        selected_company = st.selectbox(
            "Clínica",
            options=get_args(availableCompanies),
            index=0,
            key="selected_company",
        )
    with patient_column:
        patient_name = st.text_input("Nome do Paciente", key="patient_name")

    render_anamnesis_lookup_section(selected_company, patient_name)

    st.markdown("### Prosync (PDF)")
    prosync_file = st.file_uploader("Upload Prosync PDF", type=["pdf"], key="prosync")

    st.markdown("### Oberon (TXT)")

    oberon_categories = {
        "toxinas": "Toxinas",
        "emocoes": "Emoções",
        "microrganismos": "Microrganismos",
        "cristais": "Cristais",
        "alimentos": "Alimentos",
        "patologias": "Patologias",
    }

    oberon_files = {}
    oberon_thresholds = {}

    for key, label in oberon_categories.items():
        st.markdown(f"#### {label}")
        file = st.file_uploader(f"Upload {label} TXT", type=["txt"], key=f"oberon_{key}")

        if file:
            oberon_files[key] = file

            c1, c2 = st.columns(2)
            with c1:
                f_min = st.number_input(
                    f"Min D ({label})", value=0.0, step=0.1, key=f"min_d_{key}"
                )
            with c2:
                f_max = st.number_input(
                    f"Max D ({label})", value=1.0, step=0.1, key=f"max_d_{key}"
                )

            oberon_thresholds[key] = [f_min, f_max]

    st.markdown("### Parâmetros de Configuração")
    prosync_std = st.number_input("Prosync Std", value=0.1, step=0.01, key="prosync_std")

    st.markdown("### Sessões Extras")
    invalidate_extra_sessions_cache_on_company_change(selected_company)
    extra_sessions_catalog_state = get_extra_sessions_catalog_state()
    available_extra_session_options = build_catalog_options_for_clinic(
        extra_sessions_catalog_state["catalog"],
        selected_company,
    )
    sync_selected_extra_sessions(available_extra_session_options)

    if extra_sessions_catalog_state["status"] == "warning":
        st.warning(extra_sessions_catalog_state["message"])
    elif extra_sessions_catalog_state["status"] == "error":
        st.error(extra_sessions_catalog_state["message"])

    available_extra_session_names = [
        option["treatment_name"] for option in available_extra_session_options
    ]
    option_labels = {
        option["treatment_name"]: format_extra_session_option_label(option)
        for option in available_extra_session_options
    }

    selected_extra_sessions = st.multiselect(
        "Selecione as sessões extras do protocolo",
        options=available_extra_session_names,
        format_func=lambda name: option_labels.get(name, name),
        key="selected_extra_sessions",
        disabled=not available_extra_session_names,
    )

    if not available_extra_session_names:
        st.info(
            f"Nenhuma sessão extra com preço válido disponível para {selected_company}."
        )

    extra_sessions = []
    for session_name in selected_extra_sessions:
        quantity = st.number_input(
            f"Quantidade de {session_name}",
            min_value=1,
            step=1,
            value=1,
            key=f"extra_session_quantity_{session_name}",
        )
        extra_sessions.extend([session_name] * int(quantity))
    extra_session_prices = build_selected_session_price_lookup(
        extra_sessions_catalog_state["catalog"],
        selected_company,
        selected_extra_sessions,
    )

    prosync_data = {}
    selected_prosync_list = []
    oberon_data_full = {}
    selected_oberon_data_full = {}

    if prosync_file:
        try:
            st.subheader("Resultado Prosync")
            prosync_data = extract_prosync_content(prosync_file, prosync_std=prosync_std)
            prosync_table, prosync_list = prosync_table_content(
                prosync_data, gen_report=True
            )
            selected_prosync_list = render_selectable_table(
                prosync_list,
                "prosync",
                display_records=table_columns_to_records(prosync_table),
            )

        except Exception as e:
            st.error(f"Erro ao processar Prosync: {e}")
    else:
        st.info("Nenhum arquivo Prosync enviado.")


    if oberon_files:
        st.subheader("Resultados Oberon")

        for key, file in oberon_files.items():
            try:
                st.markdown(f"**Categoria: {oberon_categories[key]}**")
                available_enc = ["cp1252", "utf-8", "latin1", "iso-8859-1", "utf-8-sig"]

                for enc in available_enc:
                    try:
                        if hasattr(file, "seek"):
                            file.seek(0)

                        raw_content = extract_oberon_content(file, enc=enc)
                        if len(raw_content) > 0:
                            break

                    except Exception as e:
                        print(f"Problema na leitura: com {enc}")

                # Process based on category
                processed_data = []

                if key == "toxinas":
                    # toxins_info expects dict, returns list of dicts
                    processed_data = toxins_info(raw_content)
                elif key == "microrganismos":
                    processed_data = microorganism_info(raw_content)
                elif key == "cristais":
                    processed_data = crystal_info(raw_content)
                elif key == "alimentos":
                    processed_data = food_info(raw_content)
                elif key == "emocoes":
                    processed_data = emotions_info(raw_content)
                elif key == "patologias":
                    processed_data = patologies_info(raw_content)
                else:
                    processed_data = raw_content

                oberon_data_full[key] = processed_data
                selected_oberon_data_full[key] = processed_data

                if key in {"toxinas", "microrganismos"} and isinstance(processed_data, list):
                    selected_oberon_data_full[key] = render_selectable_table(
                        processed_data,
                        f"oberon_{key}",
                    )
                elif isinstance(processed_data, list):
                    st.dataframe(pd.DataFrame(processed_data), use_container_width=True)
                else:
                    st.dataframe(pd.DataFrame([processed_data]), use_container_width=True)

            except Exception as e:
                st.error(f"Erro ao processar Oberon ({oberon_categories[key]}): {e}")
    else:
        st.info("Nenhum arquivo Oberon enviado.")

    # Generate Report Button
    if st.button("Gerar Relatório"):
        if prosync_data or oberon_data_full:
            st.markdown("---")
            st.subheader("Relatório")
            try:
                report_patient_name = resolve_report_patient_name(
                    patient_name,
                    st.session_state.get(ANAMNESIS_ACCESS_GRANTED_STATE_KEY) is True,
                    st.session_state.get(ANAMNESIS_LOOKUP_STATE_KEY),
                    st.session_state.get("anamnesis_candidate_index"),
                )
                protocol_and_report_content = generate_content_for_report(
                    selected_prosync_list,
                    selected_oberon_data_full,
                    oberon_thresholds,
                    report_patient_name,
                )
                protocol_and_report_content["extra_sessions"] = extra_sessions
                protocol_and_report_content["extra_session_prices"] = (
                    extra_session_prices
                )
                protocol_and_report_content["anamnesis_rows"] = (
                    build_report_anamnesis_rows(
                        st.session_state.get(ANAMNESIS_ACCESS_GRANTED_STATE_KEY)
                        is True,
                        st.session_state.get(ANAMNESIS_SELECTED_ROWS_STATE_KEY),
                    )
                )

                docx_buffer = None
                protocol_buffer = None
                budget_buffer = None

                try:
                    if not selected_company:
                        selected_company = "Bienestar"
                    docx_buffer = generate_report(
                        protocol_and_report_content, company_name=selected_company
                    )
                    protocol_buffer = generate_protocol(protocol_and_report_content)
                    budget_buffer = generate_budget(protocol_and_report_content)

                except Exception as e:
                    print(f"Erro ao gerar conteúdo: {e}")

                if protocol_buffer:
                    render_docx_download_link(
                        "Baixar Protocolo (DOCX)",
                        protocol_buffer,
                        build_output_file_name(
                            "protocolo",
                            selected_company,
                            report_patient_name,
                        ),
                    )
                else:
                    st.error("Erro ao gerar o protocolo (Template não encontrado?).")

                if budget_buffer:
                    render_docx_download_link(
                        "Baixar Orçamento (DOCX)",
                        budget_buffer,
                        build_output_file_name(
                            "orcamento",
                            selected_company,
                            report_patient_name,
                        ),
                    )
                else:
                    st.error("Erro ao gerar o relatório (Template não encontrado?).")

                if docx_buffer:
                    render_docx_download_link(
                        "Baixar Relatório (DOCX)",
                        docx_buffer,
                        build_output_file_name(
                            "relatorio",
                            selected_company,
                            report_patient_name,
                        ),
                    )
                else:
                    st.error("Erro ao gerar o relatório (Template não encontrado?).")

            except Exception as e:
                st.error(f"Erro ao gerar relatório: {e}")
        else:
            st.warning(
                "Sem dados para gerar relatório. Por favor, faça upload dos arquivos."
            )

with system_data_tab:
    render_system_data_tab()
