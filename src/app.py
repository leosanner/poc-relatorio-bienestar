import streamlit as st
import pandas as pd
from utils.prosync import extract_prosync_content
from utils.oberon import extract_oberon_content, format_file_name
from utils.report import generate_report, prosync_table_content, oberon_table_content

st.set_page_config(page_title="Bienestar POC", layout="wide")

st.title("Bienestar POC - Processamento de Arquivos")

st.markdown("### Prosync (PDF)")
prosync_file = st.file_uploader("Upload Prosync PDF", type=["pdf"], key="prosync")

st.markdown("### Oberon (TXT)")
oberon_files = st.file_uploader("Upload Oberon TXT", type=["txt"], accept_multiple_files=True, key="oberon")

st.markdown("### Informações do Relatório")
patient_name = st.text_input("Nome do Paciente", key="patient_name")

st.markdown("### Parâmetros de Configuração")
col1, col2, col3 = st.columns(3)
with col1:
    min_d = st.number_input("Min D", value=0.0, step=0.1, key="min_d")
with col2:
    max_d = st.number_input("Max D", value=1.0, step=0.1, key="max_d")
with col3:
    prosync_std = st.number_input("Desvio padrão Prosync", value=0.1, step=0.01, key="prosync_std")

if st.button("Processar Arquivos"):
    prosync_data = {}
    oberon_data_full = {}

    if prosync_file:
        try:
            st.subheader("Resultado Prosync")
            # extract_prosync_content returns a dict
            prosync_data = extract_prosync_content(prosync_file)
            df_prosync = pd.DataFrame([prosync_data])
            st.dataframe(df_prosync)
        except Exception as e:
            st.error(f"Erro ao processar Prosync: {e}")
    else:
        st.info("Nenhum arquivo Prosync enviado.")

    if oberon_files:
        st.subheader("Resultados Oberon")
        for i, file in enumerate(oberon_files):
            try:
                file_name = format_file_name(file.name)
                st.markdown(f"**Arquivo: {file_name}**")
                # extract_oberon_content returns a dict
                oberon_data = extract_oberon_content(file, enc='cp1252')
                oberon_data_full[file_name] = oberon_data
                df_oberon = pd.DataFrame([oberon_data])
                st.dataframe(df_oberon)
            except Exception as e:
                st.error(f"Erro ao processar Oberon ({file.name}): {e}")
    else:
        st.info("Nenhum arquivo Oberon enviado.")

    # Generate Report if data is available
    if prosync_data or oberon_data_full:
        st.markdown("---")
        st.subheader("Relatório")
        try:
            # Prepare data for report
            # We need to handle the case where one of them might be empty, 
            # but the report template likely expects both or handles empty lists.
            # Based on report.py logic:
            
            prosync_table = prosync_table_content(prosync_data, std=float(prosync_std))['content']
            oberon_table = oberon_table_content(oberon_data_full, thershold_range=[min_d, max_d])['content']
            
            docx_buffer = generate_report(prosync_table, oberon_table, patient_name)
            
            if docx_buffer:
                st.download_button(
                    label="Baixar Relatório (DOCX)",
                    data=docx_buffer,
                    file_name=f"relatorio_bienestar_{patient_name.replace(' ', '_')}.docx" if patient_name else "relatorio_bienestar.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            else:
                st.error("Erro ao gerar o relatório (Template não encontrado?).")
                
        except Exception as e:
            st.error(f"Erro ao gerar relatório: {e}")
