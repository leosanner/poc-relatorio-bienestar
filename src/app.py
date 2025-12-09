import streamlit as st
import pandas as pd
from utils.prosync import extract_prosync_content
from utils.oberon import extract_oberon_content, food_info
from utils.report import generate_report, prosync_table_content, oberon_table_content

st.set_page_config(page_title="Bienestar POC", layout="wide")

st.title("Bienestar POC - Processamento de Arquivos")

st.markdown("### Prosync (PDF)")
prosync_file = st.file_uploader("Upload Prosync PDF", type=["pdf"], key="prosync")

st.markdown("### Oberon (TXT)")

oberon_categories = {
    "toxinas": "Toxinas",
    "emocoes": "Emoções",
    "microrganismos": "Microrganismos",
    "cristais": "Cristais",
    "alimentos": "Alimentos",
}

oberon_files = {}
oberon_thresholds = {}

# Create uploaders and threshold inputs for each category
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

st.markdown("### Parâmetros de Configuração")
prosync_std = st.number_input("Prosync Std", value=0.1, step=0.01, key="prosync_std")


# Initialize data containers
prosync_data = {}
oberon_data_full = {}

if prosync_file:
    try:
        st.subheader("Resultado Prosync")
        # extract_prosync_content returns a dict
        prosync_data = extract_prosync_content(prosync_file)
        df_prosync = pd.DataFrame(prosync_table_content(prosync_data)[0])
        st.dataframe(df_prosync)

    except Exception as e:
        st.error(f"Erro ao processar Prosync: {e}")
else:
    st.info("Nenhum arquivo Prosync enviado.")

if oberon_files:
    st.subheader("Resultados Oberon")

    from utils.oberon import toxins_info, crystal_info, microorganism_info

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
            else:
                processed_data = raw_content

            oberon_data_full[key] = processed_data

            # Display
            if isinstance(processed_data, list):
                st.dataframe(pd.DataFrame(processed_data))
            else:
                st.dataframe(pd.DataFrame([processed_data]))

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
            from utils.report import generate_report, prosync_table_content

            # Calculate prosync table content to pass to context (reusing existing logic for consistency)
            prosync_list = []
            if prosync_data:
                prosync_list = prosync_table_content(prosync_data, gen_report=True)[1]

            docx_buffer = generate_report(
                prosync_list, oberon_data_full, oberon_thresholds, patient_name
            )

            if docx_buffer:
                st.download_button(
                    label="Baixar Relatório (DOCX)",
                    data=docx_buffer,
                    file_name=(
                        f"relatorio_bienestar_{patient_name.replace(' ', '_')}.docx"
                        if patient_name
                        else "relatorio_bienestar.docx"
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
