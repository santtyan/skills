---
name: migrar-para-langchain
description: Guia para avaliar e conduzir a migração de um sistema de IA existente (RAG, roteamento, geração de SQL, pipelines de decisão) para LangChain/LangGraph, em ordem de risco crescente por tipo de módulo, preservando garantias determinísticas já validadas (checagens de segurança, precedência de regra sobre LLM). Use quando o usuário pedir para "migrar para LangChain", "vale usar LangGraph aqui", "traduzir esse módulo pra LangChain", ou perguntar por onde começar uma migração desse tipo.
---

# Migrar um sistema de IA para LangChain/LangGraph

## Pré-requisito de setup (rodar uma vez por projeto)

As skills oficiais da LangChain (`langchain-ai/langchain-skills`) já ensinam o "como" genérico
de `create_agent()`, LangGraph e Deep Agents — não duplicar esse conteúdo aqui. Antes de começar
a primeira migração, instalar localmente ao projeto:

```
npx skills add langchain-ai/langchain-skills --skill '*' --yes
```

Esta skill assume essas skills disponíveis e só referencia os padrões delas (`RunnableBranch`,
`EnsembleRetriever`, LangGraph conditional edges, etc.) — o foco aqui é o que muda de projeto
para projeto: em que ordem migrar e o que não pode regredir.

## Tabela de risco por tipo de módulo (não repesquisar do zero)

A ordem certa de migração raramente é "de cima para baixo no código" — é por quanto o framework
já resolve versus quanto é lógica de domínio que você vai ter que reescrever de qualquer forma.
Classifique cada módulo do seu sistema num destes tipos antes de decidir a ordem:

1. **Retrieval / busca (RAG)** — **menor risco**. `EnsembleRetriever` (fusão sparse+dense via
   RRF) e `ContextualCompressionRetriever` + `CrossEncoderReranker` mapeiam quase 1:1 no que a
   maioria dos sistemas de RAG já tem na mão (embedding denso + busca lexical + rerank sobre um
   vector store). Se o seu sistema hoje combina os dois sinais por normalização manual de score,
   documente a diferença (RRF funde por posição no ranking, não por valor de score) — não assuma
   que RRF é estritamente melhor sem medir Recall@k/MRR antes e depois no seu próprio golden set.

2. **Self-repair / segunda opinião** — **baixo-médio risco**. Se o sistema já tem um passo de
   "gerar, depois validar com outra chamada", os padrões CRAG/Self-RAG têm cookbook oficial em
   LangGraph, e "critic node" mapeia conceitualmente nisso. Bom segundo passo porque valida o
   padrão de branching condicional do LangGraph antes de aplicá-lo num módulo mais crítico
   (o roteamento, item 3).

3. **Roteamento com regra de negócio custom** — **médio risco, esforço alto**. Existe padrão
   nomeado ("Adaptive RAG" / query router, `RunnableBranch` / conditional edges do LangGraph)
   para o encaixe do roteamento em si, mas cada regra específica de negócio (gates
   determinísticos, filtros de domínio) continua sendo lógica 100% custom — o framework só
   padroniza ONDE a decisão acontece, não fornece a regra em si. Se o sistema tem várias regras
   desse tipo, contar quantas existem antes de estimar o esforço — migrar sem perder cobertura
   de nenhuma delas é o trabalho real, não a integração com o framework.

4. **Pipeline de decisão em camadas (regra determinística → modelo → LLM)** — **baixo risco,
   baixo retorno**. Não existe integração nomeada do LangGraph para pipelines de ML tabular
   clássico (scikit-learn etc.); se hoje já é um if/elif simples e funcional, avaliar se vale a
   pena migrar antes de investir tempo aqui — frequentemente não vale.

5. **Geração de código/consulta com validação de segurança (ex.: NL-to-SQL)** — **maior risco**.
   Componentes nativos de checagem de query em frameworks como o LangChain costumam ser
   **LLM-assistidos** (pedem ao próprio LLM para revisar a saída antes de executar), não uma
   validação determinística em código. Se o seu sistema hoje valida com uma regra determinística
   (ex.: checagem de que a query é só `SELECT`), migrar sem manter essa camada de validação
   própria em paralelo é uma regressão de segurança silenciosa — não aceitar essa troca sem
   perceber que ela aconteceu.

### Outros achados relevantes (contexto ao decidir)

- LCEL perdeu o posto de "default" para LangGraph em fluxos com estado/branching desde a v1.0;
  `AgentExecutor` e `LangServe` estão formalmente deprecated — não migrar para LCEL puro, ir
  direto para LangGraph nos módulos com branching (roteamento, self-repair).
- `with_structured_output` com modelos locais pequenos (ex.: via Ollama) tem falha documentada
  de taxa de erro em JSON schema (1-5% em modelos na faixa de 3B parâmetros). Se o sistema
  oferece seleção entre modelo "rápido"/pequeno e "qualidade"/grande, testar explicitamente o
  modelo pequeno antes de considerar qualquer módulo migrado como pronto — não validar só com o
  modelo maior.
- Críticas equilibradas e reais existem contra adotar frameworks de orquestração de LLM em
  produção sem medir primeiro (churn de versão entre releases, overhead de abstração sobre algo
  que os SDKs de modelo já resolvem sozinhos). Medir antes de assumir que migrar é estritamente
  melhor — construir e medir bate mais pesquisa de blog.
- LangSmith funciona com modelos locais sem exigir LLM pago (alternativa open-source: Langfuse),
  mas é aditivo — avaliar separadamente do framework de orquestração em si, não é pré-requisito.

## Quando migrar mesmo sem ganho isolado de qualidade

Nem toda migração se justifica por um número melhorando. Se a medição de um módulo (ex.:
Recall@k/MRR do retrieval) sair empatada entre a implementação atual e a versão no framework, e
o ganho real vier de um algoritmo específico (ex.: RRF) que também dá para aplicar sem o
framework — a decisão de migrar mesmo assim só é legítima quando há uma razão declarada
explicitamente, não assumida por padrão. A razão mais comum e válida: **consistência
arquitetural com módulos futuros** — se você já sabe que vai migrar módulos com branching
(roteamento, self-repair) para LangGraph, ter o retrieval já em LangChain evita uma segunda
migração/mistura de paradigmas quando esses módulos precisarem consumir o retriever dentro de um
grafo único. Registre essa razão explicitamente onde quer que você documente decisões de
arquitetura — "medimos, não ganhou isoladamente, migramos mesmo assim por causa de X" é uma
decisão defensável; "migramos porque sim" não é.

## Regra inegociável por módulo migrado

Nenhuma migração é aceita se regredir o que já funcionava:
- O harness/golden set de avaliação do projeto (roteamento, faithfulness, ou o que for a métrica
  central) não pode cair em relação ao baseline pré-migração daquele módulo específico.
- Toda pergunta/caso de teste que hoje passa continua passando.

Isso é o motivo do módulo migrado nunca poder virar uma cópia paralela da lógica antiga vivendo
ao lado dela — uma cópia manual desatualizada de lógica de roteamento/decisão é uma fonte clássica
de regressão fantasma (o número cai porque a cópia ficou para trás, não porque algo quebrou de
verdade). Ao migrar um módulo, o código no framework novo SUBSTITUI o antigo como fonte de
verdade — não convive como "versão B" que ninguém mantém atualizada.

## Checklist de progresso

Marcar `[x]` conforme cada módulo for migrado, com uma linha de resultado (fato + data) — o que
foi medido, se regrediu ou não, e a razão da decisão se não houve ganho isolado.

- [ ] **1. Retrieval/RAG → `EnsembleRetriever`**
- [ ] **2. Self-repair/segunda opinião → LangGraph critic node (padrão CRAG/Self-RAG)**
- [ ] **3. Roteamento + regras de negócio → LangGraph conditional edges, regras portadas 1:1**
- [ ] **4. Pipeline de decisão em camadas → avaliar se vale migrar (pode ficar como está)**
- [ ] **5. Geração com validação de segurança → LangGraph + validação determinística própria
      mantida em paralelo ao componente nativo do framework**

## Como usar esta skill

- Ao ser invocada, reler a tabela de risco antes de sugerir por onde começar — a resposta para
  "por onde eu começo?" é sempre "próximo item não marcado na ordem 1→5 acima", salvo pedido
  explícito de pular a ordem.
- Antes de migrar qualquer módulo, rodar o harness/avaliação do projeto para capturar o baseline
  atual — é contra esse número que a migração será comparada.
- Depois de migrar um módulo, rodar a avaliação de novo, comparar contra o baseline, marcar `[x]`
  aqui só se não houver regressão, e anotar o resultado.
- Se o usuário perguntar sobre um módulo fora da lista, esse é território novo — parar e discutir
  antes de assumir que o mesmo raciocínio de risco se aplica sem verificar.
