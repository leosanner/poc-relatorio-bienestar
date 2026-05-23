# Arquitetura alvo

Este documento propoe uma arquitetura agnostica para reconstruir a POC como uma aplicacao com frontend + API. A proposta separa responsabilidades que hoje estao acopladas no fluxo da POC.

## Visao geral

Componentes recomendados:

- Frontend operacional.
- API de atendimentos.
- Motor de processamento de arquivos.
- Servico de catalogos.
- Servico de anamnese.
- Servico de protocolo/orcamento/relatorio.
- Persistencia.
- Armazenamento de arquivos.
- Observabilidade e auditoria.

## Frontend operacional

Responsabilidades:

- Criar e abrir atendimentos.
- Capturar clinica e nome do paciente.
- Fazer upload de Prosync e Oberon.
- Exibir status de processamento.
- Permitir revisao e selecao manual de achados.
- Consultar e selecionar anamnese.
- Selecionar sessoes extras e quantidades.
- Solicitar geracao de documentos.
- Baixar documentos gerados.
- Consultar catalogos do sistema em modo leitura.

O frontend nao deve conter regras de matching, protocolo ou precificacao. Ele deve consumir resultados estruturados da API e enviar decisoes do usuario.

## API de atendimentos

Responsabilidades:

- Gerenciar ciclo de vida do atendimento.
- Receber uploads e parametros.
- Persistir selecoes manuais.
- Expor resultados processados.
- Orquestrar geracao de documentos.
- Registrar erros e eventos.

Entidades sugeridas:

- Atendimento.
- Arquivo de entrada.
- Resultado Prosync.
- Resultado Oberon.
- Selecao manual.
- Anamnese vinculada.
- Sessao extra selecionada.
- Documento gerado.
- Versao de catalogo usada.

## Motor de processamento

Responsabilidades:

- Extrair dados de PDF Prosync.
- Extrair dados de TXT Oberon.
- Aplicar normalizacoes.
- Aplicar correspondencias e exclusoes.
- Enriquecer achados com catalogos.
- Aplicar thresholds.
- Retornar resultados estruturados e auditaveis.

O motor deve ser deterministico: os mesmos arquivos, parametros e versoes de catalogo devem produzir os mesmos resultados.

## Servico de catalogos

Responsabilidades:

- Gerenciar catalogos de correspondencia.
- Gerenciar informacoes por categoria.
- Gerenciar elementos excluidos.
- Gerenciar frequencias e tempos de protocolo.
- Gerenciar precos.
- Expor versoes e historico.

Na nova aplicacao, catalogos podem comecar como arquivos versionados, mas devem ter contrato claro para migracao futura para banco ou painel administrativo.

## Servico de anamnese

Responsabilidades:

- Validar acesso a anamnese.
- Consultar fonte externa por clinica.
- Resolver coluna de nome.
- Buscar candidatos.
- Sanitizar erros.
- Retornar perguntas/respostas estruturadas.

O acesso a credenciais e secrets deve ficar somente no backend.

## Geracao de documentos

Responsabilidades:

- Montar contexto de relatorio.
- Montar contexto de protocolo.
- Montar contexto de orcamento.
- Renderizar templates.
- Persistir documentos gerados.
- Disponibilizar download.

Templates devem ter contrato de variaveis esperado. A aplicacao deve registrar qual template e qual versao foram usados em cada documento.

## Persistencia

Dados que devem ser persistidos:

- Atendimento e dados do paciente.
- Arquivos enviados ou referencias a eles.
- Parametros usados.
- Resultados brutos e normalizados.
- Selecoes manuais.
- Fonte e versao dos catalogos.
- Anamnese escolhida e perguntas selecionadas.
- Sessoes extras e precos usados.
- Documentos gerados.
- Logs de processamento e erros.

Persistir esses dados reduz retrabalho operacional e permite auditoria quando um documento precisa ser explicado ou reemitido.

## Fluxo backend sugerido

1. Criar atendimento.
2. Enviar arquivos.
3. Processar arquivos de forma sincrona ou assincrona.
4. Retornar resultados normalizados para revisao.
5. Receber selecoes manuais.
6. Consultar anamnese sob demanda.
7. Receber sessoes extras.
8. Gerar documentos a partir do estado persistido.
9. Salvar documentos e expor links de download.

## Contratos de API sugeridos

Endpoints conceituais:

- Criar atendimento.
- Atualizar dados do atendimento.
- Enviar arquivo Prosync.
- Enviar arquivo Oberon por categoria.
- Processar ou reprocessar atendimento.
- Listar resultados processados.
- Salvar selecoes.
- Buscar anamnese.
- Listar sessoes extras por clinica.
- Gerar documentos.
- Baixar documentos.
- Consultar catalogos.

Esses endpoints sao orientativos. O desenho final pode agrupar ou dividir responsabilidades, desde que preserve isolamento de regras e rastreabilidade.

## Observabilidade e auditoria

A nova aplicacao deve registrar:

- Quem criou ou alterou atendimento.
- Quando arquivos foram enviados.
- Quais parametros foram usados.
- Quais selecoes manuais foram feitas.
- Qual fonte de catalogo foi usada.
- Quando houve fallback de Google Sheets.
- Erros de processamento e geracao.
- Versoes dos templates e catalogos.

Esses eventos sao essenciais para confianca operacional e suporte.
