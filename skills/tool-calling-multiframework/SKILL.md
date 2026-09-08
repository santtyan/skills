---
name: tool-calling-multiframework
description: Boas práticas de design de tool/function calling que valem através de provedores (OpenAI, Anthropic) e frameworks de agente (Agno e equivalentes) — schema, strict mode, deferred loading para catálogos grandes, client vs. server tools. Use quando o usuário estiver definindo tools/functions para um agente, decidindo entre client-side e server-side execution, ou lidando com um catálogo grande de ferramentas.
---

# Tool/function calling — boas práticas através de provedores

## O fluxo universal (mesmo em qualquer provedor/framework)

1. A aplicação manda ao modelo o contexto da conversa + a lista de tools disponíveis (schema).
2. O modelo decide se e quais tools chamar, retornando nome + argumentos (não executa nada).
3. A aplicação valida os argumentos e executa a tool correspondente.
4. O resultado da execução volta para o contexto do modelo.
5. O loop se repete até o modelo devolver uma resposta final sem mais chamadas.

Esse fluxo é idêntico em OpenAI (Responses API), Anthropic (Messages API) e frameworks como Agno
— a diferença entre eles é tática (nomenclatura, quem executa o quê), não estrutural.

## Design de schema

- **Nome específico** (`get_customer_profile`, não `handle_request`) — ajuda o modelo a escolher
  a operação certa sem ambiguidade.
- **Descrição concisa que explica quando usar** — não é documentação de referência, é a instrução
  que o modelo usa para decidir SE chama a tool. Coloque exemplos e casos de borda se algo falhar
  recorrentemente — mas cuidado: em modelos de raciocínio, exemplos demais podem prejudicar
  performance.
- **Type hints/schema JSON precisos** — cada parâmetro precisa de tipo e descrição própria; use
  enums para restringir valores válidos em vez de aceitar string livre quando o domínio é finito.
- **Torne estados inválidos irrepresentáveis** — ex.: `toggle_light(on: bool, off: bool)` permite
  uma chamada absurda (`on=true, off=true`); prefira `set_light(state: "on"|"off")`.
- **"Teste do estagiário"**: um humano sem contexto adicional, só com o que você deu ao modelo,
  consegue usar a função corretamente? Se não, o que ele perguntaria? Adicione essas respostas ao
  prompt/descrição.
- **Não peça ao modelo para preencher argumentos que a aplicação já sabe** — se você já tem
  `order_id` de uma etapa anterior, não exponha `order_id` como parâmetro; passe por código.
- **Combine tools que são sempre chamadas em sequência** — se `mark_location()` sempre roda logo
  depois de `query_location()`, uma única função que faz as duas é melhor que duas tools que o
  modelo precisa lembrar de encadear.

## Strict mode / schema rígido — trate como padrão, não opção avançada

Os três provedores oferecem uma forma de garantir conformidade estrita de schema (`strict: true`
na OpenAI e na Anthropic). Sem isso, a chamada é "melhor esforço" — o modelo pode retornar
argumentos que não batem exatamente com o schema declarado. Habilitar strict mode:
- Exige `additionalProperties: false` em cada objeto do schema.
- Exige que todo campo em `properties` seja declarado como obrigatório (campos opcionais viram
  `type: [tipo, "null"]` em vez de simplesmente ausentes do `required`).
- Reduz a superfície de erro de parsing de argumento — vale habilitar por padrão em produção,
  não só quando um bug de argumento malformado já apareceu.

## Catálogos grandes de tools: carregamento adiado (tool search)

Quando o número de tools disponíveis cresce (dezenas a milhares), carregar todos os schemas no
contexto de toda chamada é caro (tokens) e piora a precisão de seleção do modelo (mais opções =
mais chance de escolha errada). Padrão emergente em 2026: um mecanismo de busca de tools
(`tool_search` na OpenAI; conceito equivalente citado como "Tool search tool" na Anthropic) deixa
a maioria das tools "deferidas" — não carregadas no prompt — e o modelo busca/carrega só as
relevantes para a tarefa atual antes de chamá-las. Agrupar tools relacionadas por **namespace**
(ex.: `crm`, `billing`, `shipping`) ajuda o modelo a escolher o grupo certo antes de precisar ver
cada função individual.

**Regra prática**: mantenha menos de ~20 tools carregadas no início de um turno como orientação
suave; acima disso, considere namespaces + carregamento adiado em vez de simplesmente aceitar a
degradação de precisão.

## Client tools vs. server tools

Distinção formalizada explicitamente pela Anthropic, mas o conceito se aplica a qualquer provedor
com tools nativas (web search, execução de código, etc.):
- **Client tools**: executam na sua aplicação. Você recebe o pedido de chamada, roda o código, e
  devolve o resultado numa próxima requisição. É o caso padrão para qualquer função/API própria.
- **Server tools**: executam na infraestrutura do próprio provedor (ex.: busca na web, execução
  de código em sandbox). Você não escreve handler nenhum — o resultado já vem pronto na mesma
  resposta. Mais simples de usar, mas menos controle sobre o que exatamente acontece na execução.

Ao desenhar um agente, prefira server tools nativas para capacidades genéricas que o provedor já
oferece prontas (busca web, execução de código sandboxed) e reserve client tools para lógica de
negócio própria/dados internos — não reimplemente o que o provedor já resolve de forma madura.

## Custom tools com saída não-JSON (CFGs)

Quando a saída esperada de uma tool não é JSON estruturado, mas texto seguindo uma gramática
específica (ex.: uma expressão matemática, um comando de um DSL próprio), gramáticas livres de
contexto (Lark ou Regex, no caso da OpenAI) podem restringir a geração do modelo para sempre
produzir texto válido naquele formato — mais direto que pedir JSON e depois fazer parsing de uma
string dentro dele. Regra prática ao escrever a gramática: mantenha-a simples; gramáticas
complexas tendem a ser rejeitadas pela API ou levar o modelo a gerar saída "fora de distribuição"
(sintaticamente válida mas semanticamente errada) — prefira um terminal único e bem delimitado a
tentar particionar texto livre entre várias regras do parser.

## Não fazer

- Não exponha dezenas de tools "por via das dúvidas" sem medir se isso piora a seleção do modelo
  — teste com diferentes tamanhos de catálogo antes de assumir que mais opções é sempre melhor.
- Não trate "melhor esforço" (sem strict mode) como equivalente a validação garantida de schema —
  são coisas diferentes, e a diferença aparece exatamente quando o argumento é mais crítico.
- Não desenhe uma tool que o modelo só consegue usar corretamente com contexto que não está no
  schema/descrição dela — se você (humano) precisaria perguntar algo para usá-la direito, o
  modelo também vai errar.
