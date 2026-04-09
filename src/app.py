import hashlib
import json

from utils.oberon import toxins_info, crystal_info, microorganism_info
from utils.budget import generate_budget
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

availableCompanies = Literal["Bienestar", "Alecrim", "VitaeFlux"]
EXTRA_SESSION_OPTIONS = [
    "Acupuntura",
    "Auriculo terapia",
    "Alinhamento vibracional",
    "Alinhamento dos chacras",
    "Barras de access",
    "Bemer essencial",
    "Bemer + colorGen + reflexologia ou calatonia",
    "Bemer + biofóton",
    "Brain machine",
    "Câmara de regeneração e reequilíbrio",
    "ColorGen + uzapper",
    "Calatonia",
    "Constelação individual ou com representantes",
    "Drenagem facial + reflexologia",
    "Drenagem linfática",
    "Harmonizer",
    "Hidrogênio molecular medicinal",
    "Hidrovitalis +",
    "Intravascular laser irradiation ILIB",
    "Hidrogênio molecular medicinal intensivo",
    "Liberação miofascial",
    "Manta térmica Biomat + uzapper+ colorgen",
    "Massagem relaxante",
    "Massagem com pedras quentes",
    "Massagem Ayurvédica abyanga",
    "Metaterapia",
    "Neurospa",
    "Radiant Plasma Device (RPD)",
    "Reiki",
    "Relax dos pés + reflexologia podal",
    "Scan e meta 3D",
    "Shiatsu",
    "Tens",
    "Terapias da medicina chinesa + cone hindu",
    "Terapia de hidratação! dos tecidos conjuntivos + Colorgen",
    "uZapper",
    "Spa dos pés + calatonia",
    "Spa dos pés + reflexologia podal + massagem facial",
    "Spa dos pés + brain machine",
    "Spa dos pés + neurospa",
    "Spa dos pés + harmonizer",
]

SELECTION_COLUMN = "Selecionado"


def build_table_signature(records: list[dict]) -> str:
    return json.dumps(records, ensure_ascii=False, sort_keys=True, default=str)


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

st.set_page_config(page_title="Bienestar POC", layout="wide")

st.title("Processamento de Arquivos")

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

st.markdown("### Informações do Relatório")
patient_name = st.text_input("Nome do Paciente", key="patient_name")
selected_company = st.selectbox(
    "Clínica",
    options=get_args(availableCompanies),
    index=0,
    key="selected_company",
)

st.markdown("### Parâmetros de Configuração")
prosync_std = st.number_input("Prosync Std", value=0.1, step=0.01, key="prosync_std")

st.markdown("### Sessões Extras")
selected_extra_sessions = st.multiselect(
    "Selecione as sessões extras do protocolo",
    options=EXTRA_SESSION_OPTIONS,
    key="selected_extra_sessions",
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
            display_records=pd.DataFrame(prosync_table).to_dict("records"),
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
            protocol_and_report_content = generate_content_for_report(
                selected_prosync_list,
                selected_oberon_data_full,
                oberon_thresholds,
                patient_name,
            )
            protocol_and_report_content["extra_sessions"] = extra_sessions

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
                st.download_button(
                    label="Baixar Protocolo (DOCX)",
                    data=protocol_buffer,
                    file_name=(
                        f"protocolo_bienestar_{patient_name.replace(' ', '_')}.docx"
                        if patient_name
                        else "protocolo_bienestar.docx"
                    ),
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            else:
                st.error("Erro ao gerar o protocolo (Template não encontrado?).")

            if budget_buffer:
                st.download_button(
                    label="Baixar Orçamento (DOCX)",
                    data=budget_buffer,
                    file_name=(
                        f"orcamento_bienestar_{patient_name.replace(' ', '_')}.docx"
                        if patient_name
                        else "orcamento_bienestar.docx"
                    ),
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            else:
                st.error("Erro ao gerar o relatório (Template não encontrado?).")

            if docx_buffer:
                st.download_button(
                    label="Baixar Relatório (DOCX)",
                    data=docx_buffer,
                    file_name=(
                        f"relatorio_{selected_company}_{patient_name.replace(' ', '_')}.docx"
                        if patient_name
                        else f"relatorio_{selected_company}.docx"
                    ),
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            else:
                st.error("Erro ao gerar o relatório (Template não encontrado?).")

        except Exception as e:
            st.error(f"Erro ao gerar relatório: {e}")
    else:
        st.warning(
            "Sem dados para gerar relatório. Por favor, faça upload dos arquivos."
        )
