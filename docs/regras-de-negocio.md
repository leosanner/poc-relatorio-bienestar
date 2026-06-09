# Regras de negocio

Este documento consolida as regras que a POC aplica hoje. Ao reconstruir a aplicacao, estas regras devem ser tratadas como comportamento de dominio e nao como detalhes da interface.

## Normalizacao geral

- Espacos duplicados sao normalizados.
- Comparacoes de nomes geralmente ignoram diferencas de maiusculas/minusculas.
- Nomes de saida sao formatados para exibicao humana.
- Duplicatas sao removidas apos normalizacao.
- Itens sem correspondencia podem permanecer nos resultados com metadados de "nao encontrado", quando a categoria permite.

## Prosync

Regras:

- O PDF e lido como tabelas.
- Celas vazias e tokens iniciados por ponto sao ignorados.
- A linha `Teste Controle` define o valor de controle.
- Apenas itens presentes no catalogo de parasitas/microrganismos reconhecidos entram como achados Prosync.
- O valor extraido vem do numerador antes da barra no campo de resultado.
- O processamento reaproveita a logica de matching de microrganismos para enriquecer nome, tipo e sintomas.

## Filtro Prosync Std

O parametro Prosync Std define uma faixa de tolerancia em torno do controle.

Regra atual:

1. Calcular `desvio = controle * Prosync Std`.
2. Calcular faixa inferior e superior.
3. Manter o controle.
4. Manter achados cujo valor esteja fora da faixa.

Com valor padrao `0.1`, a tolerancia e de 10% para baixo e para cima do controle.

## Oberon

Regras de extracao:

- Cada linha relevante deve conter `D=`.
- O nome fica antes de `D=`.
- O valor D fica depois de `D=`.
- Caracteres nao numericos sao removidos do valor, preservando ponto decimal.
- A leitura deve tolerar diferentes encodings de TXT.

Categorias:

- Toxinas.
- Emocoes.
- Microrganismos.
- Cristais.
- Alimentos.
- Patologias.

## Matching Oberon

Regras comuns:

- Remover elementos excluidos da categoria.
- Aplicar correspondencia para chegar ao nome oficial.
- Enriquecer com informacoes da categoria quando houver catalogo de informacoes.
- Ordenar resultados por valor D.
- Remover duplicatas.

Regras especificas:

- Toxinas: enriquecem efeitos/fontes quando encontrados.
- Microrganismos: enriquecem tipo e sintomas; alguns nomes especiais preservam grafia, como hepatites e Influenza A.
- Cristais: enriquecem beneficios fisicos e emocionais.
- Alimentos: sao distribuidos em quatro grupos por valor D: `0 a 0.300`,
  `0.300 a 0.700`, `0.700 a 1.000` e `> 1.000`.
- Emocoes: aplicam correspondencia e removem termos excluidos.
- Patologias: aplicam correspondencia antes de retornar; termos novos nao excluidos podem aparecer no resultado.

## Thresholds por valor D

Cada categoria Oberon enviada possui faixa minima e maxima configuravel.

Aplicacao:

- Toxinas, cristais, alimentos, emocoes e patologias entram no relatorio apenas se estiverem dentro da faixa.
- Microrganismos Oberon tambem usam faixa, mas possuem excecoes.

Excecoes de microrganismos:

- Microrganismos considerados importantes entram mesmo fora da faixa configurada.
- Valores entre `0.35` e `0.45` sao destacados em laranja no relatorio.

## Selecao manual

A POC permite que o usuario selecione quais linhas entram nos documentos.

Selecoes explicitas:

- Achados Prosync.
- Toxinas Oberon.
- Microrganismos Oberon.
- Campos processados de anamnese, separados por dados pessoais e indicadores
  do historico de saude.

Na nova aplicacao, selecoes devem ser persistidas como decisoes do atendimento, com origem e data.

## Relatorio

O relatorio consolida:

- Data.
- Nome do paciente.
- Achados Prosync selecionados.
- Toxinas, microrganismos, cristais, alimentos, emocoes e patologias filtrados.
- Anamnese selecionada, quando houver.

Regras:

- O controle Prosync e usado como denominador, mas nao entra como achado do relatorio.
- Linhas Prosync exibem a relacao `D/Controle`.
- O template de relatorio varia por clinica.

## Protocolo

O protocolo usa principalmente:

- Microrganismos Prosync selecionados.
- Microrganismos Oberon selecionados.
- Toxinas selecionadas, tratadas como metais/toxinas para protocolo.
- Sessoes extras.

Microrganismos:

- Prosync tem prioridade de relevancia sobre Oberon quando ambos existem.
- Itens sao agrupados por tipo terapeutico.
- Ordem atual de tipos: fungo, helminto, protozoario, bacteria, virus.
- Frequencias e tempos sao buscados em catalogo de protocolo.
- Tempo vazio assume `180`.
- Frequencias duplicadas dentro do mesmo tipo sao removidas.
- Itens sem frequencia entram em lista de nao encontrados.

Metais/toxinas:

- Algumas toxinas/metais sao excluidas explicitamente: cadmio, mercurio, chumbo, aluminio, arsenio, prata e niquel.
- Matching ocorre por nome direto ou nome alternativo do Oberon.
- Itens sem frequencia entram em lista de nao encontrados.

Sessoes:

- O limite de uma sessao e `70 * 60`, ou 4200 segundos.
- Blocos de tratamento sao agrupados respeitando esse limite.
- A cada 9 sessoes, o sistema insere uma "Sessao intermediaria".
- A contagem considera sessoes de metais/toxinas antes das sessoes de microrganismos.
- Sessoes extras entram diretamente no protocolo.

## Orcamento

O orcamento usa as sessoes derivadas do protocolo.

Regras:

- Sessoes de microrganismos e metais/toxinas usam o preco padrao `RPD`.
- Sessoes extras usam preco por clinica vindo do catalogo de sessoes extras.
- Se uma sessao extra nao tiver preco, deve aparecer como "Nao encontrado" e nao somar no total.
- Quantidades de sessoes extras sao representadas como repeticoes da sessao.
- Totais sao calculados separadamente para PIX e cartao.
- Quando nao ha itens sem frequencia, a mensagem exibida e "Todos foram encontrados".

## Anamnese

Regras:

- Consulta protegida por secret.
- Sem secret configurado, sem secret informado ou secret invalido, a consulta fica bloqueada.
- A busca e parcial, ignora caixa e normaliza espacos.
- A coluna de nome pode ser configurada; se nao for, o sistema tenta aliases conhecidos.
- Multiplos candidatos devem ser apresentados para escolha manual.
- Erros tecnicos devem ser sanitizados para nao vazar credenciais.
- Clinicas sem suporte nao devem acionar consulta externa.

## Catalogo de sessoes extras

Regras:

- Tentar carregar Google Sheets primeiro.
- Se falhar, carregar catalogo local de contingencia.
- Se ambos falharem, a funcionalidade fica indisponivel.
- Cabecalhos sao normalizados por caixa e espacos.
- Precos aceitam numeros, `R$`, virgula decimal, ponto decimal e separadores de milhar.
- Nome de tratamento duplicado invalida o catalogo.
- Tratamentos sem preco PIX ou cartao para a clinica nao aparecem como selecionaveis.
