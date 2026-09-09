---
name: esquema-de-trace-agentes
description: Padrão-ouro e estado da arte (2026) para desenhar o esquema de trace de um agente com LLM — quando OpenTelemetry GenAI puro basta e quando falta uma camada semântica de proveniência, e como estruturar um trace serializável (JSONL) que sobrevive a troca de modelo/framework. Use quando o usuário for instrumentar um agente, perguntar "como registrar uma execução de agente", "o que é um trace de agente", ou avaliar se vale adotar OpenTelemetry para isso.
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

Status em 2026: ainda em *Development*, mas já suficientemente estável para adoção — vários
backends de observability o suportam nativamente.

**O que falta**: um survey dedicado a proveniência de agentes ("From Agent Traces to Trust",
levantamento de 2026) argumenta que instrumentação OTel pura **não é suficiente para pesquisa em
agentes** — falta a camada semântica: evidência recuperada, claim gerado, rationale de
tool-call, itens de memória, observações em linguagem natural, e principalmente **relações de
proveniência entre passos** (o survey propõe SUPPORT, DERIVE, DEPEND_ON, CONTRADICT, INVALIDATE,
TRIGGER, UPDATE). Sem essa camada, dá para saber QUE uma chamada aconteceu, mas não POR QUE ela
aconteceu em relação ao passo anterior, nem se um passo contradiz outro.

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
humano (ou para publicar como parte de uma replicação), use um formato de relatório separado —
por analogia a Model Cards, um "Rollout Card": modelo+versão, prompt usado, tools disponíveis,
dependências com versão, custo total e por execução, taxa de sucesso, distribuição de modos de
falha. Gerar esse relatório a partir dos traces brutos (nunca escrever à mão) garante que ele
sempre reflete o que de fato aconteceu.

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

## Ver também

`replicacao-experimento-agente` — o protocolo completo de replicação (código + trace +
relatório), que consome o esquema definido aqui.
