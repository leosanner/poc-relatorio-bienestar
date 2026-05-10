# F-01 - Sessoes Extras Dinamicas via Google Sheets

## Objetivo

Trocar a lista fixa de sessoes extras por um catalogo dinamico vindo de uma planilha do Google Sheets, usando a clinica selecionada para definir o preco de PIX e cartao. A carga deve acontecer uma unica vez por sessao da pagina no Streamlit.

## Contexto atual

- A tela de `Sessoes Extras` usa uma lista hardcoded em `src/app.py`.
- O orcamento resolve os precos extras via `src/assets/budget/prices.json`.
- O projeto ainda nao possui integracao Google nem configuracao de secrets no padrao do Streamlit.

## Escopo

**Incluido**
- Leitura da planilha via service account do Google em modo somente leitura.
- Cache por sessao usando `st.session_state`.
- Fallback para um arquivo JSON local versionado quando a leitura remota falhar.
- Exibicao do preco na UI conforme a clinica selecionada.
- Reaproveitamento dos precos resolvidos na geracao do orcamento DOCX.
- Documentacao da configuracao esperada em `.streamlit/secrets.toml.example`.

**Fora de escopo**
- Escrita de dados no Google Drive ou Google Sheets.
- Migracao dos precos-base do tratamento principal para a planilha.
- Tela administrativa para editar ou validar o catalogo.

## Fluxo esperado

1. A pagina inicia e tenta carregar o catalogo remoto usando `spreadsheet_id`, `extra_sessions_tab` e credenciais lidas de `st.secrets`.
2. Se a leitura remota for bem-sucedida, o catalogo normalizado e salvo em `st.session_state`.
3. Se a leitura remota falhar, o sistema usa o arquivo local de contingencia e informa isso ao usuario com uma mensagem sanitizada.
4. Se o Google e o fallback falharem, apenas a secao de sessoes extras fica indisponivel; o restante da pagina continua funcionando.
5. A UI filtra as sessoes que possuem `pix` e `cartao` validos para a clinica selecionada.
6. Ao gerar o orcamento, o app envia ao modulo de budget os precos resolvidos das sessoes extras selecionadas, sem nova consulta remota.

## Contrato da planilha

Colunas obrigatorias:

- `nome tratamento`
- `bienestar pix`
- `bienestar cartao`
- `vitaeflux pix`
- `vitaeflux cartao`
- `alecrim pix`
- `alecrim cartao`

Regras:

- O nome do tratamento e obrigatorio para a linha ser considerada.
- Espacos extras e diferencas de caixa nos headers devem ser tolerados.
- Nomes duplicados apos normalizacao invalidam a fonte remota.
- Campos de preco vazios sao aceitos, mas a sessao nao pode aparecer como selecionavel para a clinica afetada.

## Seguranca

- Credenciais Google nunca devem ser commitadas no repositorio.
- O codigo deve usar `st.secrets`, com secrets locais em `.streamlit/secrets.toml`.
- Mensagens de erro mostradas na UI nao podem incluir `private_key`, payload completo de secrets nem detalhes internos da SDK do Google.
- O app nao deve persistir credenciais em `st.session_state`; apenas o catalogo normalizado.

## Fallback local

- O arquivo local versionado deve morar em `src/assets/budget/extra_sessions_catalog_fallback.json`.
- O formato dele deve espelhar semanticamente a planilha.
- Esse arquivo e um espelho manual de contingencia e precisa ser mantido sincronizado com a planilha quando os precos reais mudarem.

## Criterios de aceite

1. O catalogo e lido no maximo uma vez por sessao de pagina.
2. Um refresh completo da pagina cria uma nova sessao e recarrega o catalogo.
3. A troca de clinica atualiza os precos exibidos e os precos usados no orcamento.
4. O orcamento continua usando `prices.json` apenas para os precos-base existentes.
5. Em falha do Google Sheets, o usuario ve um aviso claro e o app usa o JSON local.
6. Em falha dupla, somente `Sessoes Extras` fica indisponivel.
7. O repositorio passa a ter um `secrets.toml.example`, mas nunca um `secrets.toml` real.

## Estrategia de validacao

- Testes unitarios para normalizacao e fallback do loader.
- Teste unitario para garantir que o budget usa os precos extras injetados.
- Validacao manual da UI com troca de clinica, selecao de sessoes e geracao do DOCX.
