# Resumo estruturado — Advanced RAG, estado da arte 2025-2026

Complementar ao survey de Gao et al. 2023 (`resumo_survey_rag.md`) — este documento cobre o que
mudou/apareceu de novo desde então, especificamente nas técnicas de Advanced RAG (otimização
pré/pós-retrieval numa cadeia ainda linear, não Modular RAG). Reler antes de citar em
slides/relatório, não parafrasear de memória.

## 1. Query rewrite / transformation

Conjunto clássico ainda referenciado: HyDE, Step-Back Prompting, Multi-Query/RAG-Fusion,
Decomposição. [Guia de 6 arquiteturas, out/2025](https://www.dmflow.chat/en/blog/rag-query-transformation-guide-6-advanced-architectures).

**HyDE**: eficaz quando documentos são longos/narrativos e a query é curta — mas deve ser
evitado em domínios sensíveis a alucinação, porque o documento hipotético gerado pelo LLM pode
inserir detalhes falsos que desviam a busca.
[Fonte](https://medium.com/theultimateinterviewhack/hyde-query-expansion-supercharging-retrieval-in-rag-pipelines-f200955929f1).
**Risco a considerar em domínios técnicos**: conteúdo curto com terminologia precisa (limites,
thresholds, especificações) é exatamente o cenário onde um documento hipotético alucinado por um
LLM local pequeno (3B-14B, mais propenso a erro que GPT-4-class) pode puxar a busca pro lado
errado.

**Técnica nova**: MQRF-RAG (multi-strategy query rewriting) supera HyDE isolado no benchmark
AmbigQA (+1,47% EM, +3,75% F1) — combinar estratégias bate qualquer técnica isolada.
[ACM 2025](https://dl.acm.org/doi/10.1145/3728199.3728221).

**Evidência de que PODE PIORAR (não é hype só positivo)**:
- "Muitas queries são de fato prejudicadas pela reescrita" — introduz ruído semântico.
  [When Query Expansion Hurts RAG](https://medium.com/@ThinkingLoop/when-query-expansion-hurts-rag-23139f06d8d4)
- Falhas documentadas em produção: "query drift", troca de entidade, over-filtering.
  [When "Smart" Query Rewriting Breaks Your RAG](https://medium.com/@Nexumo_/when-smart-query-rewriting-breaks-your-rag-494271e751d3)
- Custo de latência: uma chamada LLM extra antes do retrieval.
  [Unstructured.io](https://unstructured.io/insights/retrieval-latency-optimization-for-production-rag-systems)
- Nota de cautela: um número citado num blog ("Step-Back reduz erro em ~21,6%") não tem
  fonte/paper rastreável — tratar como marketing, não evidência.

**Conclusão**: evidência mista, não padrão-ouro comprovado. Avaliação empírica por tipo de
pergunta é obrigatória, não adoção cega.

## 2. Context compression / seleção

**Estado do framework**: LangChain `ContextualCompressionRetriever` oferece 3 abordagens —
`LLMChainExtractor` (LLM extrai só o trecho relevante), `LLMChainFilter` (LLM inclui/exclui doc
inteiro, sem alterar conteúdo), `EmbeddingsFilter` (compara embeddings, mais barato, sem LLM).
Exemplo documentado: 3565→787 caracteres (4,53x).
[LangChain blog](https://www.langchain.com/blog/improving-document-retrieval-with-contextual-compression).

**Pesquisa recente**: foco em compressão "evidentiality-guided" — comprimir mantendo só o que é
evidência real da resposta, medido via faithfulness. Ex.: ECoRAG, 2025.
[arXiv 2506.05167](https://arxiv.org/pdf/2506.05167).

**Vale a pena para corpus pequeno?** Nenhuma fonte encontrada endossa compressão especificamente
para corpus pequeno (poucos documentos, chunks curtos) — os casos de uso citados envolvem
consistentemente 100+ documentos recuperados ou contexto muito longo. Lacuna real na literatura,
não confirmação nem negação forte — mas o padrão dos casos de uso sugere que o ganho é marginal
quando o `k` retornado já é pequeno.

**"Lost in the middle" — mitigação em 2025**: menos sobre comprimir conteúdo, mais sobre
posicionamento dinâmico (quantos documentos incluir, colocar os mais relevantes no fim do
contexto). [Dynamic Context Selection, arXiv 2512.14313](https://arxiv.org/html/2512.14313).

## 3. Metadata-aware retrieval / auto-retrieval

Filtro nativo maduro em Chroma/Qdrant/Pinecone/Weaviate. Recurso mais avançado: auto-retrieval
da LlamaIndex (`VectorIndexAutoRetriever`) — o LLM infere filtros de metadata a partir da
linguagem natural da pergunta.
[LlamaIndex docs](https://docs.llamaindex.ai/en/stable/examples/vector_stores/chroma_auto_retriever/).

**Vale a pena para corpus pequeno?** Sem fonte direta sobre esse trade-off específico. Racional
geral: auto-retrieval compensa quando há metadata rica o bastante para diferenciar E volume
grande o bastante para filtrar reduzir ruído de fato. Em corpus pequenos, o ganho tende a ser
marginal frente ao risco de o LLM inferir um filtro errado e excluir o documento certo.

## 4. Hybrid search — evolução desde 2023 (achado mais acionável desta seção)

**RRF (Reciprocal Rank Fusion) é hoje o padrão consensual**, nativo em Elasticsearch, OpenSearch,
Weaviate (fusão default), Qdrant (`Fusion.RRF`). Benchmarks 2024-2025 mostram BM25+denso fundidos
via RRF batendo qualquer um isolado, rerank cross-encoder adicionando +5-15 pontos de MRR em
sets difíceis. [RMIT-ADM+S SIGIR 2025 LiveRAG](https://arxiv.org/pdf/2506.14516).

**Técnicas além de RRF**: Weighted Alpha Fusion (`score = α·denso + (1-α)·esparso`, exige
normalização — sensível a mudança de distribuição), Learned Fusion (Weaviate Hybrid Search 2.0,
out/2025, modelo pequeno prevê pesos por padrão de query), DBSF (Distribution-Based Score
Fusion), SPLADE (embeddings esparsos aprendidos).

**Por que RRF é geralmente a escolha mais segura**: se um sistema combina busca densa e lexical
por normalização manual de score (soma/média ponderada), isso é a mesma classe de problema que
Weighted Alpha Fusion — sensível a mudança de distribuição entre queries diferentes. **RRF usa
só a posição no ranking, não o valor do score** — elimina de raiz essa classe de bug (um score
não-normalizado corretamente dominando o ranking mesmo quando irrelevante). Se seu sistema tem
um bug conhecido desse tipo, migrar a fusão para RRF resolve o problema pela raiz, não só
mitiga sintoma.

## 5. Reranking — achado crítico mais importante desta pesquisa

**Cross-encoder continua "a jogada padrão" em 2026** para produção. BGE e MxBAI citados como
líderes em BEIR/MS MARCO.
[thread-transfer.com, jun/2026](https://thread-transfer.com/blog/2026-06-17-rag-reranking-llm-colbert/).

**ACHADO DIRETO E ACIONÁVEL**: cross-encoders genéricos treinados em distribuição de busca web —
**incluindo modelos populares como `ms-marco-MiniLM`** — **degradam performance em -0,3% a
-3,1% em contextos técnicos/científicos fora de domínio**, porque a distribuição de treino não
transfere bem. [MeVer CheckThat 2026 / AIRwaves CheckThat 2025, busca consolidada].

**Implicação prática**: um rerank cross-encoder genérico pode não estar necessariamente ajudando
(ou pode até prejudicar) num corpus de domínio técnico específico. Isso é **medível sem nova
infraestrutura**: rodar o golden set de retrieval com rerank ligado vs. desligado e comparar
Recall@k/MRR — se o sistema já expõe um parâmetro assim, é só rodar com os dois valores.

**Alternativas mapeadas (só relevantes se a medição acima confirmar que o rerank atual não
ajuda ou ajuda pouco)**:
- **ColBERT / late-interaction**: até 180x menos FLOPs que cross-encoder em k=10 (23.000x em
  k=2000), "production-grade" em 2026 (JaColBERT, fork da Answer.ai). Exige reindexação
  multi-vetor — mudança de arquitetura, não só de modelo.
  [emergentmind.com](https://www.emergentmind.com/topics/colbertv2-retriever).
- **LLM-as-reranker**: RankLLM (SIGIR 2025), pacote com RankZephyr/RankVicuna 100% open-source.
  **Ressalva para sistemas rodando via Ollama**: citado como não-ideal para esse padrão de
  paralelismo — mais caro em latência sem serving otimizado (vLLM/SGLang).
  [PyPI rank-llm](https://pypi.org/project/rank-llm/).
- Cohere Rerank v3/v4: só relevante se o sistema já usa APIs pagas — irrelevante para sistemas
  100% locais.

## 6. Tabela de avaliação equilibrada (evidência a favor vs. risco)

| Técnica | Evidência de ganho real | Risco / evidência contrária |
|---|---|---|
| Query rewrite (HyDE, multi-query) | MQRF-RAG +1,47-3,75% EM/F1 (AmbigQA) | Evidência repetida de piora (query drift, ruído); número "-21,6%" do Step-Back sem fonte rastreável |
| RRF (hybrid fusion) | Adoção consensual da indústria; treino-free, robusto | Nenhuma crítica forte — é o baseline hoje, não hype |
| Cross-encoder rerank | +5-15 pontos MRR em sets difíceis (geral) | **`ms-marco-MiniLM` especificamente degrada -0,3% a -3,1% fora de domínio técnico** — medir, não assumir |
| ColBERT/late-interaction | Ganho de eficiência mensurável (FLOPs), "production-grade" 2026 | Exige reindexação multi-vetor, maior complexidade |
| LLM-as-reranker (RankLLM) | Ecossistema maduro, paper SIGIR 2025, 100% open-source | Ollama não-ideal para o paralelismo exigido — latência alta sem vLLM/SGLang |
| Context compression | Redução de contexto mensurada (4,5x, LangChain) | Sem evidência de ganho em corpus pequeno; casos citados são de 100+ documentos |
| Metadata auto-retrieval | Suportado nativamente em todos os vector stores relevantes | Sem evidência de ganho em corpus pequeno; risco de excluir o documento certo por filtro errado |

## Sobre a regra "implementar via framework, não Python puro"

Se o seu projeto já usa um framework de orquestração (LangChain/LangGraph), a decisão consistente
é usar o componente nativo correspondente para cada técnica (`EnsembleRetriever` para RRF,
`ContextualCompressionRetriever` para compressão, etc.) em vez de reimplementar em Python puro —
evita duas fontes de verdade divergentes para o mesmo conceito dentro do mesmo sistema.
