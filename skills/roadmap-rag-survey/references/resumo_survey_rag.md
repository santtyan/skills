# Resumo estruturado — "Retrieval-Augmented Generation for Large Language Models: A Survey"

**Citação completa**: Gao, Y., Xiong, Y., Gao, X., Jia, K., Pan, J., Bi, Y., Dai, Y., Sun, J.,
Wang, M., & Wang, H. (2024). *Retrieval-Augmented Generation for Large Language Models: A
Survey*. arXiv:2312.10997v5 [cs.CL]. Shanghai Research Institute for Intelligent Autonomous
Systems (Tongji University), Shanghai Key Laboratory of Data Science (Fudan University),
College of Design and Innovation (Tongji University). Repositório de recursos:
https://github.com/Tongji-KGLLM/RAG-Survey

Usar esta citação (não parafrasear de memória) em slides/relatórios que mencionem o artigo.

## Motivação (Introdução)

LLMs sofrem de alucinação, conhecimento desatualizado, e raciocínio não-transparente/não-
rastreável. RAG resolve incorporando conhecimento de bases externas via similaridade semântica,
reduzindo conteúdo factualmente incorreto sem precisar retreinar o modelo.

## As 3 gerações de RAG (Seção II) — taxonomia central do artigo

1. **Naive RAG**: pipeline "Retrieve-Read" fixo — indexação (limpeza/chunking/embedding) →
   retrieval (top-k por similaridade) → geração (query + chunks no prompt). Limitações
   documentadas: retrieval impreciso (chunks irrelevantes/informação faltando), geração com
   alucinação/irrelevância, dificuldade de integrar múltiplas fontes sem redundância.
2. **Advanced RAG**: adiciona otimização **pré-retrieval** (indexação com sliding window,
   segmentação fina, metadata) e **pós-retrieval** (rerank, compressão de contexto) — ainda uma
   cadeia linear (chain-like), só com mais etapas de qualidade.
3. **Modular RAG**: módulos substituíveis/reconfiguráveis — novos módulos (Search, RAG-Fusion,
   Memory, Routing, Predict, Task Adapter) e novos padrões de orquestração (iterativo,
   recursivo, adaptativo) em vez de sequência fixa. Frameworks como LangChain/LlamaIndex/
   Haystack são citados explicitamente como implementações desse padrão (nota de rodapé 2-3 do
   artigo, seção II-B).

## RAG vs. Fine-tuning (Seção II-D)

Quadrante de 2 eixos: exigência de conhecimento externo x exigência de adaptação do modelo.
Prompt engineering = baixo em ambos. RAG = alto conhecimento externo, baixa adaptação de
modelo (like "dar um livro-texto sob medida"). Fine-tuning = baixo conhecimento externo, alta
adaptação (like "aluno internalizando conhecimento"). Achado citado (ref. [28] do artigo):
RAG supera fine-tuning não-supervisionado tanto para conhecimento já visto no treino quanto
para conhecimento totalmente novo — LLMs têm dificuldade de aprender fatos novos só via
fine-tuning não-supervisionado. RAG e FT não são mutuamente exclusivos; podem ser combinados.

## III. Retrieval

### III-A. Fonte e granularidade de retrieval
- Estruturas de dado: **não-estruturado** (texto, o caso mais comum), **semi-estruturado**
  (PDF com tabelas — desafio: chunking corta tabelas, dificulta busca semântica), **estruturado**
  (Knowledge Graphs — mais preciso mas exige construção/manutenção), **gerado por LLM**
  (SKR classifica pergunta como conhecida/desconhecida antes de decidir buscar; GenRead usa
  LLM como gerador em vez de retriever).
- Granularidade: Token → Phrase → Sentence → Proposition → Chunk → Document (texto);
  Entity → Triplet → sub-Graph (KG). Trade-off: granularidade grossa = mais contexto mas mais
  ruído; granularidade fina = mais carga de retrieval, sem garantir integridade semântica.

### III-B. Otimização de indexação
- **Chunking**: tamanho fixo de tokens é o mais comum, mas gera truncamento no meio de frases
  — motiva recursive split / sliding window / "Small2Big" (sentença como unidade de busca,
  contexto vizinho anexado depois). Chunking estrutural (por seção/cabeçalho do documento, em
  vez de char fixo) não é coberto literalmente pelo artigo, mas está alinhado ao princípio geral
  de evitar corte no meio de uma unidade semântica.
- **Metadata attachment**: page/file/author/category/timestamp anexados aos chunks, permitindo
  filtro na busca e "time-aware RAG" (pesar por data). Metadata também pode ser artificial:
  resumos de parágrafo, perguntas hipotéticas geradas por LLM ("Reverse HyDE").
- **Structural/Knowledge Graph index**: hierarquia pai-filho de documentos com resumos por nó
  (acelera navegação, mitiga alucinação por chunk isolado); KG index reduz alucinação ao
  explicitar relações entre conceitos (ex.: KGP constrói grafo entre múltiplos documentos).

### III-C. Otimização de query
- **Query expansion**: Multi-Query (LLM gera variações, busca paralela), Sub-Query
  (decompor pergunta complexa via least-to-most prompting), Chain-of-Verification (valida
  queries expandidas via LLM para reduzir alucinação).
- **Query transformation**: Query Rewrite (LLM ou modelo pequeno especializado reescreve a
  pergunta — ex. RRR/Rewrite-Retrieve-Read, caso real citado: BEQUE no Taobao aumentou recall
  em long-tail queries e GMV), HyDE (gera documento hipotético/resposta assumida e busca por
  similaridade resposta↔resposta em vez de pergunta↔documento), Step-back Prompting (abstrai a
  pergunta original para um conceito de nível mais alto, busca com as duas).
- **Query routing**: roteamento por metadata/keyword (filtro determinístico) ou roteamento
  semântico (embedding da pergunta decide o pipeline) — pode ser híbrido.

### III-D. Embedding
- **Hybrid/mix retrieval**: sparse (BM25) + dense (BERT-family) capturam sinais de relevância
  complementares — sparse ajuda dense em zero-shot e em queries com entidades raras. Modelos
  citados: AngIE, Voyage, BGE. Leaderboard de referência: MTEB (Hugging Face, 8 tarefas/58
  datasets) e C-MTEB (chinês).
- **Fine-tuning do embedding model**: necessário quando o domínio diverge muito do corpus de
  pré-treino (ex.: saúde, jurídico, industrial). Também usado para alinhar retriever↔gerador
  (LSR — LM-supervised Retriever), usando o LLM como sinal de supervisão (ex.: REPLUG minimiza
  divergência KL entre distribuições do retriever e do LLM).

### III-E. Adapter
Quando fine-tuning direto é inviável (API fechada, recursos locais limitados), usar um adapter
externo treinável entre retriever e LLM (ex.: PRCA — reward-driven contextual adapter; BGM —
modelo ponte Seq2Seq que reformata o que foi recuperado para o LLM consumir melhor).

## IV. Generation

### IV-A. Context Curation
- **Reranking** (IV-A-1): reordena chunks para colocar os mais relevantes nas bordas do prompt
  (mitiga "lost in the middle" — LLMs prestam mais atenção ao início/fim de contextos longos).
  Métodos: baseados em regra (Diversity/Relevance/MRR) ou em modelo (Cross-Encoder tipo
  SpanBERT, Cohere rerank, bge-reranker-large, ou até um LLM genérico).
- **Context selection/compression** (IV-A-2): concatenar o máximo de chunks nem sempre ajuda —
  aumenta ruído. LLMLingua usa modelos pequenos para remover tokens pouco importantes;
  RECOMP/PRCA treinam um "condensador" de informação; "Filter-Reranker" usa SLM como filtro e
  LLM como reordenador; ou o próprio LLM avalia/descarta chunks pouco relevantes antes de
  responder (ex.: Chatlaw pede ao LLM "auto-sugestão" sobre relevância de dispositivos legais
  citados).

### IV-B. Fine-tuning do LLM gerador
Adapta o modelo a formato/estilo específico de saída, ou alinha via RLHF/destilação de modelo
maior (ex.: GPT-4) quando não há acesso a modelos proprietários maiores. Pode ser coordenado
com fine-tuning do retriever para alinhar as duas peças (ex.: RA-DIT usa divergência KL entre
scoring functions de retriever e gerador).

## V. Augmentation Process (como e quando retrieval e geração se alternam)

- **Iterativo** (V-A): busca repetida com base na query original + texto já gerado — dá
  contexto mais rico para raciocínio multi-step, mas custa mais chamadas.
- **Recursivo** (V-B): refina a query progressivamente / decompõe o problema em sub-problemas,
  resolvendo cada um via retrieval+geração (ex.: IRCoT, ToC).
- **Adaptativo** (V-C): o próprio sistema decide SE precisa buscar e QUANDO parar, geralmente
  via tokens especiais gerados pelo LLM (ex.: **FLARE**, **Self-RAG**). Este é o mesmo conceito
  de "self-repair/critic node" usado na skill `migrar-para-langchain` — nomes diferentes, ideia
  igual.

## VI-D. Evaluation Benchmarks and Tools

Citação direta do artigo (Seção VI-D): "A series of benchmark tests and tools have been
proposed to facilitate the evaluation of RAG. These instruments furnish quantitative metrics
that not only gauge RAG model performance but also enhance comprehension of the model's
capabilities across various evaluation aspects." O artigo separa dois tipos de instrumento:

**Benchmarks de capacidade** (medem habilidades essenciais de um modelo RAG, dataset fixo +
métrica fixa, análogo a "golden set" mas padronizado publicamente):
- **RGB** [167] — Retrieval-Augmented Generation Benchmark.
- **RECALL** [168] — benchmark de avaliação de RAG.
- **CRUD** [169] — benchmark de avaliação de RAG (Create/Read/Update/Delete, cobrindo
  diferentes tipos de operação sobre conhecimento).

**Ferramentas automatizadas de avaliação** (usam um LLM como juiz — "LLM-as-judge" — para
pontuar qualidade da resposta, não exigem golden set fixo do mesmo jeito que um benchmark):
- **RAGAS** [164] — métricas de faithfulness, answer relevance, context precision/recall.
- **ARES** [165] — Automated RAG Evaluation System, também LLM-as-judge.
- **TruLens** — framework de observability/avaliação, citado no artigo com nota de rodapé 8
  (não tem referência numerada como os demais).

**Como comparar contra um harness próprio**: se o seu projeto já tem um harness próprio (golden
set + métrica calculada com lógica determinística, não delegada a um LLM), ele é conceitualmente
mais próximo de um "benchmark de capacidade" (RGB/RECALL/CRUD) que das ferramentas LLM-as-judge.
Isso é uma diferença real, não só de nome: LLM-as-judge introduz sua própria fonte de erro (o
juiz também pode alucinar/discordar), enquanto um harness determinístico é mais controlável.
Trade-off: "mais rápido de escalar para muitas perguntas" (LLM-as-judge) vs. "mais
controlável/auditável" (harness próprio) — as duas abordagens são complementares, não
mutuamente exclusivas. RAGAS em particular roda com modelos locais sem exigir LLM pago, o que
facilita adoção incremental sem custo de API.

O restante do artigo (26 tasks, ~50 datasets, desafios futuros — contexto longo, robustez a
ruído, integração com dados estruturados, escalabilidade, RAG multimodal) segue não detalhado
aqui — expandir lendo a Seção VI/VII do artigo original ao desenhar um benchmark formal mais
amplo.

## Termos do artigo que valem manter em inglês (nomes próprios)

- "Naive/Advanced/Modular RAG" — nome próprio da taxonomia.
- "Retrieve-Read" — nome do framework citado (referência [7] do artigo).
- "Lost in the middle" — nome do fenômeno citado (referência [98]).
