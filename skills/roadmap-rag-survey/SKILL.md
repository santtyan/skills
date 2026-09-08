---
name: roadmap-rag-survey
description: Guia baseado no survey "Retrieval-Augmented Generation for Large Language Models" (Gao et al., arXiv:2312.10997) — autodiagnóstico da taxonomia Naive/Advanced/Modular RAG para o seu projeto, template de tabela de gap para preencher, e uma lista priorizada de técnicas com evidência 2025-2026 (a favor e contra). Use quando o usuário perguntar "que estágio de RAG esse projeto está", pedir para avaliar um RAG contra a literatura, ou querer um roadmap priorizado de técnicas de RAG para implementar.
---

# Autodiagnóstico e roadmap de RAG (baseado no survey de Gao et al., 2312.10997)

## A referência

"Retrieval-Augmented Generation for Large Language Models: A Survey" (Gao, Xiong, Gao, Jia, Pan,
Bi, Dai, Sun, Wang, Wang — Tongji/Fudan, arXiv:2312.10997, revisado mar/2024). Survey de ~100
estudos de RAG, organizado em 3 partes: **Retrieval**, **Generation**, **Augmentation**.
Referência completa em `references/resumo_survey_rag.md` (terminologia, tabelas-chave, citações)
— reler antes de usar como fonte em slides/relatório, não citar de memória.

**Complemento 2025-2026**: `references/resumo_advanced_rag_2025_2026.md` traz pesquisa mais
recente especificamente sobre Advanced RAG (query rewrite, hybrid fusion, reranking, context
compression), com achados que o survey de 2023 não cobre — reler junto com o resumo principal
antes de decidir o que implementar.

## As 3 gerações de RAG do artigo

- **Naive RAG**: indexação → retrieval → geração, pipeline fixo ("Retrieve-Read").
- **Advanced RAG**: adiciona otimização pré-retrieval (indexação melhor, reescrita de query) e
  pós-retrieval (rerank, compressão de contexto) — ainda uma cadeia linear.
- **Modular RAG**: módulos substituíveis/reconfiguráveis, retrieval iterativo/recursivo/
  adaptativo, roteamento entre fontes, memória, mais integração com fine-tuning.

## Passo 1 — Diagnosticar o estágio do seu projeto

Antes de planejar qualquer coisa, classifique seu sistema atual:
- Se o pipeline é indexação → busca única → geração, sem nenhuma otimização de query nem
  pós-processamento do resultado: **Naive RAG**.
- Se já tem chunking cuidadoso (não char fixo), busca híbrida (denso + lexical), ou reranking
  pós-retrieval, mas ainda numa cadeia sequencial fixa (sem branching/decisão condicional): já é
  **Advanced RAG**.
- Se tem roteamento entre múltiplas fontes de dado, retrieval que decide sozinho se precisa
  buscar de novo, ou módulos substituíveis dinamicamente: já entrou em **Modular RAG**, mesmo
  que parcialmente.

É comum um sistema estar em Advanced RAG no motor de busca em si, mas já ter uma peça isolada de
Modular RAG em outro lugar (ex.: um roteador que decide entre fontes de dado diferentes) sem que
o retrieval interno seja modular. Diagnostique cada peça separadamente, não o sistema como um
bloco único.

## Passo 2 — Preencher a tabela de gap

Use esta tabela como template — para cada técnica, marque se o seu projeto tem (✅), tem
parcialmente (🔶) ou não tem (❌), e anote onde/por quê:

| Técnica do survey | Seção do artigo | Tem? | Onde / observação |
|---|---|---|---|
| Chunking por estrutura (não char fixo) | III-B-1 Indexing | | |
| Metadata attachment (timestamp, filtro) | III-B-2 | | |
| Hierarchical/Knowledge Graph index | III-B-3 | | |
| Query expansion/rewrite (multi-query, HyDE) | III-C-1/2 | | |
| Query routing | III-C-3 | | |
| Hybrid retrieval (sparse+dense) | III-D-1 | | |
| Fine-tuning do embedding model | III-D-2 | | |
| Reranking | IV-A-1 | | |
| Context compression/seleção | IV-A-2 | | |
| Fine-tuning do LLM gerador | IV-B | | |
| Retrieval iterativo | V-A | | |
| Retrieval recursivo | V-B | | |
| Retrieval adaptativo (decidir SE precisa buscar) | V-C | | |

## Passo 3 — Priorizar o que implementar, com evidência 2025-2026

Não implemente uma técnica só porque o survey a lista — cada uma tem evidência real de ganho ou
risco documentado desde 2023. Achados diretamente acionáveis, sem exigir infraestrutura nova:

**Medir o reranker atual antes de assumir que ajuda** — cross-encoders genéricos treinados em
distribuição de busca web (ex.: `ms-marco-MiniLM`, um dos mais usados em produção) degradam
performance em -0,3% a -3,1% em domínio técnico/científico fora da distribuição de treino. Se o
seu sistema usa um cross-encoder genérico, teste com rerank ligado vs. desligado no seu golden
set antes de assumir que está ajudando — é o item de maior retorno por menor esforço porque não
exige escrever código novo, só medir com o parâmetro que provavelmente já existe.

**Hybrid search / RRF** — Reciprocal Rank Fusion é hoje o padrão consensual da indústria (nativo
em Elasticsearch, OpenSearch, Weaviate, Qdrant). Se seu sistema combina busca densa e lexical por
normalização manual de score, isso é uma fonte conhecida de bug (score não normalizado corretamente
dominando o ranking) — RRF usa só a posição no ranking, não o valor do score, eliminando essa
classe de bug de raiz. Trocar por `EnsembleRetriever` (LangChain) é geralmente baixo risco.

**Query rewrite (HyDE, multi-query, step-back)** — evidência é **mista**, não padrão-ouro
comprovado. Existe literatura recente documentando reescrita *piorando* recall ("query drift"),
e HyDE especificamente arrisca alucinar conteúdo com LLM local pequeno (3B-14B), o que é
particularmente arriscado em domínios técnicos com terminologia precisa. Testar Recall@k/MRR
antes/depois é obrigatório aqui, mais que em qualquer outro item — não adotar sem medir.

**Context compression** — sem evidência específica de ganho em corpus PEQUENO (poucos documentos,
chunks curtos). Os casos de uso citados na literatura são consistentemente de escala maior (100+
documentos recuperados, contexto longo). Provavelmente baixo retorno em projetos pequenos; medir
antes de investir tempo.

**Retrieval adaptativo (padrão Self-RAG/FLARE)** — um nó que avalia o score do primeiro resultado
e decide se refina a query e busca de novo. Se o sistema também planeja um "self-repair"/segunda
opinião em outro módulo, implementar o padrão de critic node UMA VEZ e reaproveitar — é a mesma
peça de arquitetura servindo dois propósitos.

**Metadata auto-retrieval, fine-tuning de embedding, hierarchical/KG index** — baixo retorno em
corpus pequeno; sem evidência de que compensam o esforço/risco de complexidade adicional (risco
de o LLM inferir filtro errado e excluir o documento certo, no caso de auto-retrieval). Reavaliar
se o corpus crescer significativamente.

**RAGAS/ARES como camada de avaliação complementar** (Seção VI-D do survey) — LLM-as-judge
(delegam o julgamento a outro LLM, introduzindo sua própria fonte de erro) vs. um harness
determinístico próprio. Não é substituto automático de um harness já existente, é complementar:
escala mais perguntas mais rápido, mas o harness próprio continua sendo o mais auditável. Só
avaliar se o volume de casos de teste virar um gargalo de escala.

## Como usar esta skill

- Se o usuário perguntar "em que estágio de RAG esse projeto está", usar a seção "As 3 gerações"
  para responder — não repesquisar do zero.
- Se pedir uma citação/resumo do survey original, usar `references/resumo_survey_rag.md`; se for
  sobre achados 2025-2026 (query rewrite, RRF, reranking fora de domínio), usar
  `references/resumo_advanced_rag_2025_2026.md` — não citar nenhum dos dois de memória, reler
  antes.
- Ao implementar qualquer item, medir o impacto real (Recall@k/MRR, ou a métrica central do
  projeto) antes/depois — não aceitar "deveria melhorar" sem medir.
