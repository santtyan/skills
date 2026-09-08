---
name: observability-llm-opentelemetry
description: Guia de quando/como instrumentar um pipeline de LLM (chamadas de modelo, vector DBs, frameworks de agente) com OpenTelemetry, como alternativa vendor-neutral e self-hosted a plataformas proprietárias de observability tipo LangSmith. Use quando o usuário perguntar como rastrear/depurar chamadas de LLM em produção, avaliar opções de observability para um pipeline de agente, ou decidir entre uma plataforma proprietária e uma solução open-source.
---

# Observability de LLM via OpenTelemetry

## O que resolve

Um pipeline de LLM em produção (chamadas de modelo, buscas em vector DB, execução de tools,
orquestração multi-step) é difícil de depurar sem visibilidade estruturada — "por que essa
resposta saiu assim" exige ver a cadeia completa de prompt→retrieval→tool call→resposta, não só
logs soltos. Instrumentação de observability resolve isso gerando **traces** (a árvore completa
de uma execução) em vez de só logs de linha única.

## OpenTelemetry como base vendor-neutral

OpenTelemetry é o padrão aberto de instrumentação de observability (não específico de LLM). Um
projeto de extensões sobre ele (ex.: OpenLLMetry/Traceloop) adiciona instrumentação pronta
especificamente para o ecossistema de LLM, mantendo a saída como dados OpenTelemetry padrão —
ou seja, os dados podem ser roteados para qualquer backend compatível (Grafana, Datadog,
Honeycomb, SigNoz, Sentry, um OpenTelemetry Collector próprio, entre outros), sem prender o
projeto a uma plataforma específica.

**O que costuma vir instrumentado pronto** (verificar a lista atual da ferramenta escolhida, isso
muda com frequência):
- Providers de modelo: OpenAI/Azure OpenAI, Anthropic, Bedrock, Vertex AI, Gemini, Ollama, Groq,
  Cohere, Mistral, HuggingFace, entre outros.
- Vector DBs: Chroma, Pinecone, Qdrant, Weaviate, Milvus, LanceDB, entre outros.
- Frameworks de orquestração: LangChain, LangGraph, LlamaIndex, CrewAI, Haystack, Agno, OpenAI
  Agents, entre outros.
- Protocolo MCP.

## Instalação típica (padrão do tipo de ferramenta, não específico de um pacote)

```python
pip install <pacote-de-instrumentação>
```

```python
from <pacote> import <ClasseDeInicializacao>

<ClasseDeInicializacao>.init()
```

Uma única linha de inicialização já instrumenta automaticamente qualquer chamada suportada feita
depois dela — não é necessário anotar cada chamada de modelo manualmente. Em desenvolvimento
local, desabilitar o envio em lote (batch) para ver traces imediatamente em vez de esperar o
buffer encher.

## Trade-off vs. plataforma proprietária (ex.: LangSmith)

| | OpenTelemetry (self-hosted/vendor-neutral) | Plataforma proprietária integrada |
|---|---|---|
| Portabilidade | Alta — troca de backend sem reinstrumentar | Baixa — dados presos ao produto |
| Custo | Pode rodar 100% self-hosted, sem custo de licença | Geralmente modelo pago acima de um limite grátis |
| Integração com o framework | Genérica, cobre múltiplos frameworks igualmente | Mais profunda com o ecossistema do próprio fornecedor (ex.: sugestão automática de correção de trace, quando disponível) |
| Setup | Uma linha de inicialização + escolha de backend | Geralmente já vem com dashboard pronto, sem precisar escolher/configurar backend |

**Quando escolher qual**: se o projeto já usa um único framework de orquestração de forma
profunda e quer a integração mais rica possível com aquele ecossistema específico (ex.: sugestões
automáticas de correção de trace), a plataforma proprietária do próprio fornecedor tende a ter
mais recursos verticais. Se o objetivo é observability portátil, sem lock-in, ou rodando sobre
infraestrutura já existente (ex.: um Grafana ou Datadog que o time já usa para outras coisas),
OpenTelemetry entrega isso sem duplicar ferramentas de monitoramento.

## Antes de adotar

- **Confirme a política de telemetria da ferramenta escolhida** — alguns pacotes de instrumentação
  coletam telemetria anônima própria sobre o uso do próprio pacote (não os dados do seu pipeline),
  geralmente configurável/opt-out. Verifique a versão mínima que já traz esse comportamento
  desligado por padrão, se aplicável.
- **Decida o destino antes de instrumentar** — a instrumentação em si é a mesma independente do
  backend escolhido, mas vale já ter decidido para onde os traces vão (self-hosted vs. SaaS
  gratuito vs. pago) para não gerar dados que ninguém vai olhar.
- **Não é substituto de um harness de avaliação determinístico** — observability mostra O QUE
  aconteceu numa execução real; não substitui medir sistematicamente contra um golden set. As
  duas coisas são complementares: observability ajuda a diagnosticar por que um caso específico
  falhou depois que o harness já apontou que algo regrediu.
