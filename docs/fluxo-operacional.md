# Fluxo operacional

Este documento descreve a jornada operacional que a POC executa hoje. A nova aplicacao deve preservar a intencao do fluxo, mesmo que implemente telas, endpoints e jobs de forma diferente.

## 1. Inicio do atendimento

O usuario informa:

- Clinica: Bienestar, Alecrim ou VitaeFlux.
- Nome do paciente.

Essas informacoes afetam os templates de documento, configuracoes de anamnese, precos de sessoes extras e nomes dos arquivos finais.

## 2. Consulta de anamnese

A anamnese é opcional e depende da clinica.

- Bienestar e VitaeFlux possuem fluxo de consulta.
- Alecrim aparece como indisponivel nesta versao da POC.

Fluxo esperado:

1. Usuario informa um secret de acesso.
2. Sistema valida o secret configurado.
3. Usuario busca a anamnese usando o nome do paciente.
4. Sistema consulta uma planilha Google Sheets da clinica.
5. Se houver uma resposta, ela e selecionada automaticamente.
6. Se houver multiplas respostas, o usuario escolhe uma.
7. Sistema processa a linha escolhida e gera duas tabelas selecionaveis:
   dados pessoais e indicadores do historico de saude.
8. Apenas as linhas selecionadas entram no relatorio, separadas por secao.

Quando a anamnese esta autorizada e uma resposta valida foi selecionada, o nome do paciente no relatorio pode ser substituido pelo nome vindo da planilha.

## 3. Upload e processamento Prosync

O usuario envia um PDF Prosync.

O sistema extrai tabelas do PDF, identifica o valor de controle e localiza parasitas/microrganismos conhecidos. O resultado e enriquecido com informacoes do catalogo de microrganismos e exibido para curadoria.

O usuario pode marcar ou desmarcar linhas antes da geracao dos documentos. O controle e usado como referencia, mas nao deve ser tratado como achado do relatorio.

## 4. Upload e processamento Oberon

O usuario pode enviar arquivos TXT Oberon por categoria:

- Toxinas.
- Emocoes.
- Microrganismos.
- Cristais.
- Alimentos.
- Patologias.

Para cada categoria enviada, o usuario configura uma faixa minima e maxima de valor D. O sistema extrai pares de nome e valor D, aplica correspondencias, remove elementos excluidos e enriquece os dados quando existe catalogo de informacoes.

Toxinas e microrganismos passam por uma etapa explicita de selecao manual. As demais categorias sao exibidas para conferencia e filtradas por threshold durante a composicao do relatorio.

## 5. Parametros de processamento

O parametro Prosync Std define a tolerancia em torno do controle do Prosync. O comportamento atual mantem o controle e os achados fora da faixa calculada a partir desse controle.

Cada categoria Oberon enviada possui seu proprio intervalo de valor D. Esses intervalos controlam o que entra no relatorio, com excecoes documentadas nas regras de negocio.

## 6. Sessoes extras

O sistema carrega um catalogo de sessoes extras por clinica.

Fluxo esperado:

1. Buscar catalogo remoto no Google Sheets.
2. Se a busca falhar, usar catalogo local de contingencia.
3. Filtrar opcoes com preco valido para a clinica selecionada.
4. Exibir nome da sessao e precos PIX/cartao.
5. Usuario seleciona uma ou mais sessoes.
6. Usuario informa quantidade de cada sessao.
7. Sistema expande quantidades em linhas repetidas para protocolo e orcamento.

Exemplo: se o usuario seleciona "Calatonia" com quantidade 2, o protocolo e o orcamento recebem duas ocorrencias de "Calatonia".

## 7. Geracao dos documentos

Ao acionar a geracao, o sistema consolida:

- Dados selecionados do Prosync.
- Dados processados e selecionados do Oberon.
- Thresholds de cada categoria.
- Nome final do paciente.
- Clinica.
- Anamnese selecionada.
- Sessoes extras e precos.

Com esse contexto unico, o sistema gera:

- Protocolo DOCX.
- Orcamento DOCX.
- Relatorio DOCX.

Os arquivos finais seguem a ideia de nome:

- `protocolo_<clinica>_<paciente>.docx`
- `orcamento_<clinica>_<paciente>.docx`
- `relatorio_<clinica>_<paciente>.docx`

O nome deve ser sanitizado para evitar caracteres invalidos ou problematicos em downloads.

## 8. Consulta de dados do sistema

A POC tambem possui uma area de consulta dos dados internos do sistema. Ela permite visualizar correspondencias usadas no processamento:

- Dado que entra no sistema.
- Valor correspondente padronizado.
- Informacoes adicionais quando existirem.

Essa area e importante para auditoria operacional e deve ser considerada na nova aplicacao como uma tela administrativa ou de consulta tecnica.
