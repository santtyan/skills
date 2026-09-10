---
name: esquema-de-trace-agentes
description: Padrão-ouro e estado da arte (2026) para desenhar o esquema de trace de um agente com LLM — composição de três padrões citáveis (vocabulário OTel GenAI, estrutura de log de avaliação Inspect AI/EvalLog, publicação via Rollout Card) mais a camada semântica de proveniência (7 relações tipadas, survey arXiv:2606.04990), incluindo os renames recentes de campo OTel (gen_ai.system→gen_ai.provider.name, prompt_tokens→input_tokens) e o status real (Development, sem release versionado no novo repo). Use quando o usuário for instrumentar um agente, perguntar "como registrar uma execução de agente", "o que é um trace de agente", ou avaliar se vale adotar OpenTelemetry/Inspect AI para isso.
---

# Esquema de trace para agentes com LLM

## Por que o trace vem antes do resto

Um agente acopla modelo, prompt, tools, lógica de retry e ambiente — mudar qualquer peça muda o
comportamento medido. Sem um registro estruturado de CADA execução (não só o resultado final),
é impossível saber se uma mudança melhorou algo, piorou, ou só mudou por acaso. O esquema de
como registrar uma execução deve ser definido **antes** de instrumentar custo, ablação por
flag, ou qualquer outra disciplina experimental — os outros itens dependem de ter onde gravar.

## OpenTelemetry GenAI: o padrão de indústria, mas não suficiente sozinho

A convenção **OpenTelemetry GenAI Semantic Conventions** é o padrão de instrumentação adotado
por ferramentas de observability de produção (Datadog, MLflow, Langfuse). Define nomes de span
e atributos padronizados:

- **Spans**: `chat {model}` (kind CLIENT, invocação de modelo), `execute_tool {tool_name}`
  (kind INTERNAL, chamada de tool), `invoke_agent` (execução de agente).
- **Atributos principais**: `gen_ai.operation.name`, `gen_ai.provider.name`,
  `gen_ai.request.model`, `gen_ai.response.model`, `gen_ai.usage.input_tokens`,
  `gen_ai.usage.output_tokens`, `gen_ai.tool.call.arguments`, `gen_ai.tool.call.result`.
- Conteúdo (`gen_ai.input.messages`/`gen_ai.output.messages`) é opt-in e vai em **eventos**, não
  em atributos — permite filtrar/dropar conteúdo sensível no nível do coletor sem tocar código.

Status em 2026 (verificado 2026-09): **as convenções GenAI permanecem em Development** — nenhum
span, evento, métrica ou atributo GenAI está marcado como Stable no repositório oficial. Vários
backends de observability já suportam o vocabulário mesmo assim (é o de fato-padrão de mercado),
mas não tratar como spec congelada.

**Mudança estrutural a registrar**: as convenções GenAI **saíram** do repositório
`open-telemetry/semantic-conventions` para um repositório dedicado,
`open-telemetry/semantic-conventions-genai` — o repo antigo depreciou todo o conteúdo `gen_ai.*`
na v1.42.0. Complicação prática: **o repositório novo ainda não tem releases versionados** —
hoje não dá para "pinar" uma versão exata da convenção GenAI como se pina uma versão de pacote.

**Renomeações de campo** (um esquema escrito contra docs antigos vai divergir):

| Campo antigo (depreciado) | Campo atual | Desde |
|---|---|---|
| `gen_ai.system` | `gen_ai.provider.name` | v1.37.0 |
| `gen_ai.usage.prompt_tokens` | `gen_ai.usage.input_tokens` | v1.27.0 |
| `gen_ai.usage.completion_tokens` | `gen_ai.usage.output_tokens` | v1.27.0 |
| `gen_ai.prompt` / `gen_ai.completion` | `gen_ai.input.messages` / `gen_ai.output.messages` / `gen_ai.system_instructions` | — |

Esta skill já recomendava `gen_ai.usage.input_tokens`/`output_tokens` (nomes atuais, correto).
Ao consumir trace de terceiros durante a transição, frameworks costumam emitir os dois
conjuntos simultaneamente — **coalescer com precedência para o nome novo**, não confiar só num
dos dois. O span `invoke_agent` também foi refinado na v1.41.0 (dividido em spans client/internal,
mais campos de reasoning tokens) — checar a versão exata da convenção antes de comparar dois
traces gerados em datas muito diferentes.

**O que falta**: um survey dedicado a proveniência de agentes ("From Agent Traces to Trust: A
Survey of Evidence Tracing and Execution Provenance in LLM Agents", arXiv:2606.04990) argumenta
que instrumentação OTel pura **não é suficiente para pesquisa em agentes** — falta a camada
semântica: evidência recuperada, claim gerado, rationale de tool-call, itens de memória,
observações em linguagem natural, e principalmente **relações de proveniência entre passos**.
O survey define uma taxonomia de **sete relações tipadas** (esta skill já cobria cinco — as
duas que faltavam estão marcadas):

- **SUPPORT** — evidência justifica um claim/ação.
- **DERIVE** — transformação/sumarização de uma evidência em outra.
- **DEPEND-ON** — dependência de execução entre passos.
- **CONTRADICT** — conflito semântico entre dois passos/evidências.
- **INVALIDATE** — informação nova torna uma premissa anterior inutilizável.
- **TRIGGER** *(adicionar)* — ativação causal: uma observação dispara uma tool call.
- **UPDATE** *(adicionar)* — mudança de estado externo (memória, linha de banco).

O modelo geral do qual essa taxonomia é uma adaptação é o **W3C PROV-DM**
(entidades/atividades/agentes/relações) — vale citar como a referência-mãe de proveniência, da
qual a taxonomia de 7 relações é a especialização para unidades semânticas de agente LLM. Sem
essa camada, dá para saber QUE uma chamada aconteceu, mas não POR QUE ela aconteceu em relação
ao passo anterior, nem se um passo contradiz outro.

**Padrão-ouro para trace especificamente de AVALIAÇÃO/BENCHMARK (não observability de
produção)**: **Inspect AI**, do UK AI Safety Institute (UK AISI) — usado em praticamente todas
as avaliações automatizadas do órgão, e adotado por Anthropic, DeepMind e outros para
publicação de resultados de benchmark. Estrutura do log (`EvalLog`):

- Nível execução: `eval` (task, model, timestamp), `plan` (solvers + config de geração),
  `results` (métricas dos scorers), `stats` (uso de tokens), `samples`, `reductions`, `error`,
  `status`.
- Nível sample (1 item do benchmark): input, target, mensagens, **transcript de eventos**,
  scores, erros.
- Tipos de evento no transcript: `ModelEvent`, `ToolEvent`, `StepEvent`, `InfoEvent`,
  `SpanBegin`/`SpanEnd`.
- Extensibilidade nativa relevante aqui: `transcript.info()` grava entradas customizadas
  (gera um `InfoEvent`) e o context manager `span()` agrupa atividade relacionada — **é
  exatamente onde a camada semântica de proveniência (relações SUPPORT/DERIVE/...) encaixaria
  sem precisar inventar um formato próprio do zero**.
- Formatos de arquivo: `.eval` (binário, ~1/8 do tamanho do `.json` equivalente, acesso
  incremental a samples individuais — ganhos de ~10:1 medidos em benchmarks agênticos pesados
  tipo SWE-Bench/Cybench) vs. `.json` (legível por humano). Mesma API Python lê os dois, podem
  coexistir no mesmo diretório de resultados.

**Como os três níveis se compõem** (não competem entre si): vocabulário de campo (OTel
`gen_ai.*`) → estrutura de log de avaliação com transcript de eventos (Inspect AI `EvalLog`) →
bundle de publicação/reprodutibilidade (Rollout Card, ver seção abaixo) → camada de
proveniência tipada (survey 2606.04990) como enriquecimento semântico por cima de qualquer um
dos anteriores. Um esquema de trace de pesquisa bem embasado hoje é essa composição, não uma
escolha única entre eles.

## Decisão recomendada: schema próprio, alinhado a OTel, mais camada semântica

Não adote OTel puro como o único esquema de trace de pesquisa, nem invente um esquema livre sem
relação com nada. O meio-termo que funciona:

1. **Espelhe os nomes de campo `gen_ai.*`** nos seus registros (mesmo sem depender do SDK
   OpenTelemetry) — migração futura para um exportador real fica direta, sem reescrever a
   captura.
2. **Adicione a camada semântica que falta**: em cada passo do trace, registre que evidências
   foram usadas (ids de documento/linha recuperados) e que relações existem entre passos
   (SUPPORT/DERIVE/DEPEND_ON/CONTRADICT/INVALIDATE) — essa é a parte que permite auditar e
   depurar um agente de verdade, não só medir latência/custo.
3. **Serialize em JSONL** (uma execução por linha) — mais fácil de versionar, de fazer diff, e
   de processar em lote do que um formato binário de spans.

Campos mínimos de um passo: índice, tipo (llm/tool/retrieval), thought/action/action_input/
observation (para ciclos ReAct), `gen_ai_request_model`, `gen_ai_response_model`,
`gen_ai_usage_input_tokens`, `gen_ai_usage_output_tokens`, duração. Campos mínimos de uma
execução: id, tarefa, entrada, timestamp, duração total, resultado final, sucesso (bool),
modelo+versão exata, lista de passos.

## Relatório de replicação (Rollout Card): trace não é relatório

Um trace registra UMA execução em detalhe técnico. Para comunicar uma SÉRIE de execuções a um
humano (ou para publicar como parte de uma replicação), use um formato de relatório separado.
**"Rollout Card" não é terminologia cunhada informalmente — é um padrão publicado**: *Rollout
Cards: A Reproducibility Standard for Agent Research* (Masters, Liu, Albrecht — arXiv:2605.12131,
2026), por analogia declarada a Model Cards/Datasheets for Datasets. Especifica quatro
componentes obrigatórios:

1. **Rollout record** — tarefa, ambiente, ações, timing, falhas de cada execução.
2. **Reporting-rule registry** — nomeia toda view/regra aplicada para computar os scores
   reportados (evita que dois papers usem "accuracy" com regras de contagem diferentes sem
   avisar).
3. **Drops manifest** — registro tipado de quais campos/linhas cada análise LEU ou OMITIU
   (transparência sobre o que foi descartado antes de calcular a métrica final).
4. **Release-scope metadata** — redações, limites de acesso, restrições de redistribuição.

Problema real que o padrão ataca: papers publicam scores agregados deixando os rollout records
brutos difíceis de inspecionar, tornando impossível distinguir se uma diferença de score vem do
comportamento real do agente ou de uma escolha silenciosa do código de avaliação. O paper cita
explicitamente OpenTelemetry e Inspect AI como exemplos de ecossistemas com convenções
divergentes de contabilidade de token e tratamento de erro — reforça por que compor os padrões
(seção acima) importa mais do que escolher um só.

Gerar esse relatório a partir dos traces brutos (nunca escrever à mão) garante que ele sempre
reflete o que de fato aconteceu.

**Nota sobre formato de serialização**: esta skill recomenda JSONL (abaixo) por ser simples,
versionável e greppable — trade-off razoável na escala de um projeto pequeno/replicação
individual. Vale registrar que o formato `.eval` do Inspect AI existe justamente porque JSON
puro escala mal em benchmark agêntico real (diferença de ~8x em tamanho de arquivo, medida pelos
mantenedores). Se o volume de execuções crescer para a escala de um benchmark completo (milhares
de rollouts), migrar de JSONL para algo com acesso incremental (como `.eval`) é o caminho —
não é preciso adotar isso desde o primeiro experimento.

## Como aplicar

1. Antes de instrumentar qualquer coisa, defina o esquema de trace (dataclass/TypedDict +
   serialização JSONL) — é o pré-requisito de custo, ablação por flag, e comparação de
   experimentos.
2. Nomeie campos espelhando `gen_ai.*` mesmo sem usar o SDK OpenTelemetry — barato agora,
   economiza reescrita depois.
3. Não pule a camada semântica (evidências, relações entre passos) achando que só custo/latência
   já bastam — é exatamente essa camada que falta em instrumentação OTel genérica para permitir
   auditoria real de um agente.
4. Gere o relatório de replicação (Rollout Card) a partir dos traces, nunca escrito à mão.

## Não fazer

- Não adote só OTel puro achando que resolve auditoria de agente — resolve observabilidade de
  latência/custo, não proveniência de raciocínio.
- Não invente um esquema de trace desconectado de qualquer padrão — perde a portabilidade que
  é o motivo de ter um esquema em primeiro lugar.
- Não confunda trace (uma execução) com relatório (uma coleção de execuções) — são artefatos
  diferentes, com propósitos diferentes.

## Para que serve a camada semântica na prática: atribuição automática de falha

Linha de pesquisa 2026 relevante para justificar o esforço de manter a camada de proveniência:
*failure attribution* — dado um trace rico, localizar automaticamente QUAL passo causou uma
falha (não só QUE a execução falhou). Benchmarks/métodos citáveis: Who&When Pro
(arXiv:2607.09996), FALAT (busca guiada por dependências tipadas), DCFA, GraphTracer (grafos de
dependência de informação). Conecta diretamente com qualquer harness de detecção de alucinação
já existente — a camada de proveniência é o que torna esse tipo de atribuição automática
possível depois, não só auditoria manual.

## Ver também

`replicacao-experimento-agente` — o protocolo completo de replicação (código + trace +
relatório), que consome o esquema definido aqui.

## Fontes (pesquisa de estado da arte, 2026-09)

- [OTel GenAI spans — doc primário, repo dedicado](https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-spans.md)
- [open-telemetry/semantic-conventions-genai](https://github.com/open-telemetry/semantic-conventions-genai)
- [OTel — página GenAI](https://opentelemetry.io/docs/specs/semconv/gen-ai/) / [registry de atributos gen-ai](https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/)
- [The state of the OpenTelemetry GenAI semantic conventions (jul/2026) — John Hodge](https://john-hodge.com/blog/opentelemetry-genai-semantic-conventions/)
- [Rollout Cards: A Reproducibility Standard for Agent Research (arXiv:2605.12131)](https://arxiv.org/html/2605.12131v1)
- [From Agent Traces to Trust: A Survey of Evidence Tracing and Execution Provenance in LLM Agents (arXiv:2606.04990)](https://arxiv.org/html/2606.04990v1)
- [Inspect AI — Log Files](https://inspect.aisi.org.uk/eval-logs.html) / [Custom Agents](https://inspect.aisi.org.uk/agent-custom.html) / [repo](https://github.com/UKGovernmentBEIS/inspect_ai)
- [Who&When Pro: Failure Attribution in AI Agents (arXiv:2607.09996)](https://www.emergentmind.com/papers/2607.09996)
