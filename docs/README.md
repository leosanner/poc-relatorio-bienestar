# Documentacao base da POC Bienestar

Esta documentacao descreve a POC Bienestar de forma agnostica de linguagem e framework. O objetivo e preservar o entendimento de negocio, fluxo de dados, regras e componentes para orientar a construcao de uma nova aplicacao com frontend + API.

A POC atual atua como uma ferramenta interna de apoio ao atendimento. Ela recebe exames Prosync e Oberon, consulta dados complementares de anamnese, permite curadoria manual dos achados e gera tres documentos finais: relatorio, protocolo e orcamento.

## Proposta do produto

A proposta e centralizar o processamento de dados de atendimento em um fluxo unico:

1. Identificar clinica e paciente.
2. Consultar anamnese quando disponivel.
3. Processar PDF Prosync.
4. Processar TXTs Oberon por categoria.
5. Aplicar catalogos, filtros e regras terapeuticas.
6. Permitir selecao manual dos achados relevantes.
7. Incluir sessoes extras e seus precos.
8. Gerar relatorio, protocolo e orcamento em DOCX.

O usuario principal e a equipe operacional da clinica, que precisa transformar dados tecnicos dos exames em documentos compreensiveis e acionaveis para atendimento e venda de tratamento.

## Clinicas e documentos

Clinicas suportadas pela POC:

- Bienestar.
- Alecrim.
- VitaeFlux.

Documentos gerados:

- Relatorio DOCX: consolida achados, informacoes do paciente e, quando selecionada, anamnese.
- Protocolo DOCX: organiza sessoes de tratamento para microrganismos, metais/toxinas e sessoes extras.
- Orcamento DOCX: precifica sessoes de tratamento e sessoes extras, separando valores PIX e cartao.

## Entradas principais

- Clinica.
- Nome do paciente.
- PDF Prosync.
- Arquivos TXT Oberon por categoria.
- Faixas minima/maxima de valor D por categoria Oberon.
- Parametro Prosync Std.
- Respostas de anamnese via Google Sheets.
- Sessoes extras e quantidades.
- Catalogos internos de correspondencia, informacao, exclusao, frequencias, precos e templates.

## Mapa da documentacao

- [Fluxo operacional](./fluxo-operacional.md): jornada ponta a ponta do atendimento.
- [Modelo de dados e catalogos](./modelo-de-dados-e-catalogos.md): formatos conceituais das entradas, saidas e assets configuraveis.
- [Regras de negocio](./regras-de-negocio.md): regras de normalizacao, matching, filtros, protocolo, orcamento e anamnese.
- [Arquitetura alvo](./arquitetura-alvo.md): proposta para uma nova aplicacao com frontend + API.
- [Lacunas e decisoes futuras](./lacunas-e-decisoes-futuras.md): fragilidades da POC e decisoes que a nova aplicacao deve fechar.

## Principios para a nova aplicacao

- Separar interface, API, motor de processamento, persistencia e geracao de documentos.
- Tratar catalogos como dados versionaveis e auditaveis, nao como detalhes escondidos da UI.
- Persistir atendimentos, arquivos enviados, selecoes manuais, documentos gerados e erros relevantes.
- Permitir reprocessamento rastreavel quando catalogos, thresholds ou arquivos forem alterados.
- Manter as regras de negocio documentadas como contrato, independentemente da tecnologia escolhida.
