# Bienestar POC

Este projeto é uma Prova de Conceito (POC) desenvolvida com Streamlit para processar e extrair informações de arquivos Prosync (PDF) e Oberon (TXT).

## Funcionalidades

- **Upload de Arquivos**: Suporte para upload de arquivos PDF (Prosync) e TXT (Oberon).
- **Processamento Automático**: Extração de dados dos arquivos utilizando lógica personalizada.
- **Visualização de Dados**: Exibição dos dados extraídos em tabelas (DataFrames).
- **Geração de Relatórios**: Geração de um relatório em formato DOCX consolidando as informações extraídas, com suporte para inclusão do nome do paciente.

## Instalação

Este projeto utiliza `uv` para gerenciamento de dependências, mas também pode ser instalado via `pip`.

### Pré-requisitos

- Python 3.11 ou superior.

### Passos

1.  Clone o repositório.
2.  Instale as dependências:

    Com `uv`:
    ```bash
    uv sync
    ```

    Ou com `pip`:
    ```bash
    pip install -r requirements.txt
    ```
    *(Nota: Se não houver `requirements.txt`, use `pyproject.toml`)*

## Como Usar

Para iniciar a aplicação, execute o seguinte comando na raiz do projeto:

```bash
streamlit run src/app.py
```
ou com `uv`:
```bash
uv run streamlit run src/app.py
```

### Fluxo de Uso

1.  **Upload Prosync**: Carregue o arquivo PDF do relatório Prosync.
2.  **Upload Oberon**: Carregue um ou mais arquivos TXT do relatório Oberon.
3.  **Nome do Paciente**: Insira o nome do paciente no campo correspondente.
4.  **Processar**: Clique no botão "Processar Arquivos".
5.  **Visualizar**: Veja os dados extraídos nas tabelas apresentadas.
6.  **Baixar Relatório**: Role até o final da página e clique em "Baixar Relatório (DOCX)" para obter o documento gerado.

## Estrutura do Projeto

- `src/app.py`: Aplicação principal Streamlit.
- `src/utils/`: Scripts de utilidade para extração de dados (`prosync.py`, `oberon.py`) e geração de relatórios (`report.py`).
- `src/assets/`: Arquivos de exemplo e templates.
