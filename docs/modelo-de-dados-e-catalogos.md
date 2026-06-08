# Modelo de dados e catalogos

Este documento descreve os dados conceituais usados pela POC. Os nomes abaixo sao contratos de dominio, nao obrigacoes de implementacao.

## Atendimento

Representa uma execucao do fluxo para um paciente.

Campos conceituais:

- Clinica.
- Nome digitado do paciente.
- Nome final do paciente usado nos documentos.
- Data de processamento.
- Arquivos de entrada.
- Parametros de processamento.
- Achados processados.
- Selecoes manuais.
- Sessoes extras.
- Documentos gerados.
- Status e erros.

Na nova aplicacao, o atendimento deve ser persistido para permitir auditoria, reprocessamento e historico.

## Prosync

Entrada:

- Um arquivo PDF.

Dados extraidos:

- Linha de controle.
- Nome do item encontrado.
- Valor D ou valor numerico equivalente.
- Razao exibivel em relatorio no formato `valor/controle`.
- Metadados de microrganismo quando houver correspondencia.

Catalogos relacionados:

- Lista de parasitas/microrganismos reconhecidos no Prosync.
- Catalogo de correspondencia de microrganismos.
- Catalogo de informacoes de microrganismos.

## Oberon

Entrada:

- Um arquivo TXT por categoria.
- Cada linha relevante contem um nome antes de `D=` e um valor D depois de `D=`.

Categorias:

- Toxinas.
- Emocoes.
- Microrganismos.
- Cristais.
- Alimentos.
- Patologias.

Registro conceitual extraido:

- Categoria.
- Nome original.
- Nome padronizado.
- Valor D.
- Metadados enriquecidos, quando houver.
- Indicador de encontrado/nao encontrado em catalogo.
- Indicador de selecionado pelo usuario, quando aplicavel.

## Catalogos Oberon

Os catalogos Oberon se dividem em tres familias.

### Correspondencia

Mapeia nomes de entrada para nomes padronizados do sistema.

Exemplo conceitual:

```json
{
  "nome vindo do arquivo": "nome oficial no sistema"
}
```

Uso:

- Normalizar variacoes de escrita.
- Unificar nomes equivalentes.
- Permitir que informacoes e frequencias sejam encontradas por nome oficial.

### Informacoes

Descreve dados adicionais usados no relatorio ou em consultas internas.

Exemplos por categoria:

- Toxinas: nome, efeitos, fontes.
- Microrganismos: tipo, nome, sintomas.
- Cristais: beneficios fisicos e emocionais.

### Elementos excluidos

Lista termos que devem ser ignorados durante o processamento.

Uso:

- Remover itens irrelevantes.
- Evitar ruido do arquivo Oberon.
- Impedir que termos genericos entrem no relatorio.

## Anamnese

Fonte:

- Google Sheets por clinica.

Configuracoes conceituais:

- ID da planilha.
- Nome da aba.
- Coluna de nome do paciente, opcional.
- Credenciais de leitura.
- Secret de acesso.

Registro retornado:

- Nome do paciente.
- Timestamp, quando existir.
- Email, quando existir.
- Linha completa da planilha para processamento interno.

O sistema nao exibe mais todas as colunas da linha. Antes da curadoria, ele
filtra perguntas conhecidas por comparacao normalizada do texto da pergunta
e gera duas secoes:

- Dados pessoais.
- Indicadores do historico de saude.

Cada secao transforma as perguntas mapeadas em pares:

- Campo.
- Resposta.

Perguntas nao mapeadas sao ignoradas. Campos mapeados sem resposta aparecem
com `--`. Quando mais de uma pergunta alimenta o mesmo campo, as respostas
sao concatenadas com `;`. Esses pares sao selecionaveis e apenas os
selecionados entram no relatorio, separados por secao.

## Sessoes extras

Fonte principal:

- Google Sheets.

Fonte de contingencia:

- Catalogo local versionado.

Campos obrigatorios:

- Nome do tratamento.
- Preco PIX por clinica.
- Preco cartao por clinica.

Clinicas do catalogo:

- Bienestar.
- Alecrim.
- VitaeFlux.

Registro conceitual:

```json
{
  "treatment_name": "Nome da sessao",
  "prices": {
    "Bienestar": {
      "pix": 100,
      "cartao": 120
    }
  }
}
```

Precos vazios significam que aquela sessao nao esta disponivel para a clinica. Uma sessao so deve aparecer para selecao quando possuir preco PIX e cartao validos.

## Precos do orcamento

O orcamento usa:

- Preco padrao `RPD` para sessoes de tratamento geradas por microrganismos e metais/toxinas.
- Precos especificos por sessao extra e clinica.

Valores sao exibidos separadamente para PIX e cartao.

Totais conceituais:

- Total de tratamentos.
- Total de sessoes extras.
- Total geral.

## Templates de documentos

Templates esperados:

- Relatorio por clinica.
- Protocolo.
- Orcamento.

Os templates consomem um contexto estruturado com dados do paciente, tabelas filtradas, blocos de protocolo, sessoes extras e totais financeiros.

Na nova aplicacao, os templates devem ser tratados como artefatos versionados, com contrato explicito de variaveis esperadas.
