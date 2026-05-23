# Lacunas e decisoes futuras

Este documento lista pontos da POC que devem ser tratados com cuidado na nova aplicacao. Nem todos sao bugs; muitos sao decisoes que ficaram implicitas durante a prova de conceito.

## Acoplamento de responsabilidades

A POC mistura interface, processamento, estado de sessao, integracoes externas e geracao de documentos no mesmo fluxo operacional.

Decisao futura:

- Separar regras de dominio da UI.
- Criar contratos entre frontend, API e motor de processamento.
- Garantir que processamento possa ser testado sem depender da interface.

## Modelo formal de dados

A POC trabalha com listas e dicionarios moldados conforme a necessidade de cada gerador.

Decisao futura:

- Definir entidades formais para atendimento, arquivo, achado, categoria, selecao, anamnese, sessao extra e documento.
- Definir campos obrigatorios, opcionais e valores possiveis.
- Versionar contratos de entrada e saida do motor de processamento.

## Persistencia e reprocessamento

Hoje os documentos sao gerados em memoria durante a sessao. A POC nao estabelece historico persistente do atendimento.

Decisao futura:

- Persistir arquivos enviados, parametros, resultados, selecoes e documentos.
- Permitir reprocessar um atendimento com novos catalogos ou thresholds.
- Registrar qual versao de catalogo/template foi usada em cada geracao.

## Catalogos como fonte critica

Os catalogos locais determinam correspondencias, exclusoes, informacoes, frequencias e precos. Hoje eles aparecem como assets do projeto.

Decisao futura:

- Definir processo de atualizacao e aprovacao de catalogos.
- Validar duplicidades, campos obrigatorios e consistencia antes de publicar.
- Considerar uma tela administrativa ou pipeline de importacao.
- Manter historico para saber por que um documento foi gerado de certa forma.

## Regras hardcoded

Algumas regras estao fixas na POC:

- Clinicas suportadas.
- Categorias Oberon.
- Lista de microrganismos importantes.
- Ordem terapeutica de microrganismos.
- Metais/toxinas explicitamente excluidos.
- Limite de sessao de 4200 segundos.
- Sessao intermediaria a cada 9 sessoes.
- Preco padrao `RPD`.
- Nome fixo no contexto atual do protocolo.

Decisao futura:

- Identificar quais regras devem ser configuraveis por clinica.
- Identificar quais regras sao globais e devem permanecer em codigo.
- Remover valores temporarios, como nome fixo de protocolo.

## Tratamento de erros

A POC possui tratamento parcial de erros. Algumas falhas sao exibidas para o usuario, outras sao apenas impressas ou substituidas por mensagens genericas.

Decisao futura:

- Padronizar erros de validacao, processamento, integracao e geracao.
- Exibir mensagens operacionais claras.
- Registrar detalhes tecnicos em logs seguros.
- Evitar vazamento de credenciais ou dados sensiveis.

## Anamnese

A busca atual e parcial por nome e pode retornar multiplos candidatos.

Decisao futura:

- Definir criterio de identidade do paciente.
- Decidir se busca por nome basta ou se deve incluir email, telefone, data de nascimento ou outro identificador.
- Definir se o nome da anamnese sempre substitui o nome digitado quando selecionado.
- Definir politica para clinicas sem anamnese configurada.

## Google Sheets e fallback

Google Sheets e usado para anamnese e sessoes extras. Sessoes extras possuem fallback local; anamnese nao possui fallback de dados.

Decisao futura:

- Definir se Google Sheets permanece como fonte primaria.
- Definir cache, timeout e estrategia de retry.
- Definir alerta quando o sistema usa catalogo de contingencia.
- Definir como sincronizar dados para reduzir dependencia em tempo real.

## Prosync e Oberon

A POC depende de formatos especificos dos arquivos. Mudancas na estrutura de PDF ou TXT podem quebrar a extracao.

Decisao futura:

- Criar validadores de arquivo antes do processamento.
- Retornar erros explicando arquivo invalido, categoria incorreta ou ausencia de dados.
- Guardar conteudo bruto extraido para auditoria.
- Criar testes com arquivos reais anonimizados por categoria.

## Thresholds e selecao manual

Thresholds e selecoes manuais influenciam diretamente documentos finais.

Decisao futura:

- Definir valores padrao por categoria e por clinica.
- Persistir quem alterou thresholds e selecoes.
- Permitir comparar resultado bruto, filtrado e selecionado.
- Definir se selecoes devem afetar todos os documentos ou apenas alguns.

## Templates DOCX

Templates sao essenciais para a saida, mas o contrato de variaveis esperadas nao esta formalizado.

Decisao futura:

- Documentar variaveis exigidas por cada template.
- Validar template antes de publicar.
- Versionar templates por clinica.
- Criar testes de geracao com dados minimos e completos.

## Seguranca e dados sensiveis

A POC lida com dados de pacientes, respostas de anamnese e credenciais de Google Sheets.

Decisao futura:

- Definir autenticacao e autorizacao de usuarios.
- Limitar acesso por clinica.
- Criptografar secrets e proteger credenciais.
- Definir politica de retencao de arquivos e documentos.
- Registrar auditoria sem expor dados sensiveis desnecessariamente.

## Produto futuro

A POC prova o fluxo, mas a nova aplicacao precisa decidir o nivel de produto.

Decisoes futuras:

- Sera uma ferramenta interna multi-clinica ou um produto com permissoes por organizacao?
- Havera revisao/aprovacao antes da emissao de documentos?
- Havera edicao manual de conteudo final?
- Havera painel de historico do paciente?
- Havera integracao com pagamento, CRM ou prontuario?
