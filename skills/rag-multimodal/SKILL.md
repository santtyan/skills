---
name: rag-multimodal
description: Guia e checklist para adicionar RAG multimodal (texto + imagem) a um projeto — decisão de arquitetura entre caption-then-embed e embeddings compartilhados (CLIP), modelos VLM locais viáveis por faixa de hardware, e pegadinhas conhecidas de ambiente (Ollama + PyTorch no mesmo processo). Use quando o usuário pedir para "adicionar imagem ao RAG", "RAG multimodal", "indexar diagramas/gráficos", ou avançar num checklist de implementação multimodal.
---

# RAG multimodal (texto + imagem)

## Decisão de arquitetura

Duas famílias competem para RAG multimodal: **embeddings compartilhados** (CLIP/SigLIP — imagem
e texto no mesmo espaço vetorial) e **caption-then-embed** (um VLM gera uma legenda textual da
imagem, que entra no pipeline de RAG textual já existente). Resumo de pesquisa completo em
`references/resumo_rag_multimodal_2025_2026.md` — reler antes de citar ou revisar a decisão.

**Recomendação padrão: caption-then-embed**, não CLIP, pelas seguintes razões:
- CLIP é comprovadamente fraco em ler texto/rótulo embutido em imagem ("modality gap" e falha de
  "attribute binding") — problema direto para diagrama técnico com múltiplos componentes
  rotulados (ex.: vários sensores/componentes identificados na mesma imagem).
- Integrações CLIP em frameworks como LangChain costumam viver em pacotes experimentais
  (`langchain_experimental`), com API menos estável que os componentes de produção do resto do
  pipeline.
- Caption-then-embed é a via mais madura em produção e a que menos briga com uma arquitetura de
  RAG textual já existente — o objeto indexado continua sendo texto, sem trocar vector store.
- ColPali/ColQwen2 (page-as-image) e GraphRAG-sobre-estrutura (ex. DEXPI para diagramas de
  engenharia formais tipo P&ID) ficam como vias secundárias de roadmap — mais pesadas/menos
  maduras hoje, e a segunda só faz sentido se houver diagrama em formato estruturado formal.

**Modelo VLM**: um modelo na faixa 7B (ex.: Qwen2.5-VL) via Ollama costuma performar
sensivelmente melhor que modelos menores para conteúdo visual estruturado (gráficos, tabelas,
OCR). **Risco de compatibilidade conhecido**: algumas versões do Ollama podem não conectar
corretamente o projetor multimodal (`mmproj`) de certos modelos — testar o pull e confirmar que
a via de imagem realmente funciona ANTES de comprometer a arquitetura em cima dele. Ter um
fallback mais leve documentado (ex.: `llava` ou `moondream`, <4GB, mas com entendimento mais
limitado de cena complexa) para não travar o smoke test se o modelo principal falhar.

## Regra: usar o framework de orquestração já em uso, não reimplementar

Se o projeto já usa um framework (ex.: LangChain), o captioning deve passar pelo cliente de
chat multimodal desse framework quando ele suportar imagem de forma estável na versão instalada,
e a indexação deve reusar o mesmo pipeline de retrieval textual já em produção — evita manter
duas implementações paralelas do mesmo conceito.

## Checklist de implementação

Escopo de uma primeira rodada é um **smoke test end-to-end**, não o roadmap inteiro — confirmar
que o pipeline funciona com poucas imagens antes de expandir.

1. **Gerar/obter imagens técnicas de teste** — se não houver imagens reais disponíveis ainda,
   gerar gráficos técnicos programaticamente (ex.: via matplotlib, a partir de dados numéricos
   que o projeto já produz) em vez de usar geração de imagem por IA generativa — mais barato,
   controlável, e você sabe exatamente o conteúdo de cada imagem para validar o captioning
   depois.
2. **Confirmar que o VLM local funciona antes de automatizar** — testar o pull do modelo e uma
   chamada de captioning isolada numa única imagem. Documentar qualquer fallback usado e por quê
   (não silenciar o problema) — isso evita que a próxima tentativa repita o mesmo erro.
3. **Gerar legendas e indexar** — captioning de cada imagem, empacotar como documento de texto
   (com metadata apontando para o arquivo de imagem original, para devolver a imagem na resposta
   depois — não só o texto da legenda), indexar no pipeline de retrieval do projeto, de
   preferência numa coleção separada da produção até medir a qualidade.
4. **Smoke test manual** — algumas perguntas de teste confirmando que o retrieval acha a imagem
   certa. Não é harness formal ainda — é validação mínima antes de investir em mais.

## Pegadinhas conhecidas de ambiente

**Ollama pode falhar ao carregar o projetor multimodal (`mmproj`) de certos modelos** — o erro
típico é algo como "Failed to load CLIP model ... llama-server process has terminated". Se isso
acontecer, não é necessariamente um bug do seu código — testar um modelo alternativo antes de
assumir que a arquitetura está errada.

**Combinar um cliente Ollama (ex.: `ChatOllama` do LangChain) com bibliotecas de tensor pesadas
(sentence-transformers/PyTorch) no MESMO PROCESSO Python pode causar segmentation fault**, mesmo
sem nenhuma chamada de rede real — só com os imports presentes juntos. Isso já foi reproduzido de
forma isolada em pelo menos um ambiente real. Se o pipeline combina captioning via Ollama com
embeddings/reranking via sentence-transformers, rodar as duas etapas como **processos Python
separados** (ex.: uma etapa gera e salva as legendas num arquivo intermediário, outro processo lê
esse arquivo e faz a indexação) evita o problema — e mover todos os imports relevantes para
dentro das funções que os usam (nunca no topo do módulo) ajuda a isolar qual combinação está
causando o crash, se precisar depurar.

## Itens de roadmap (depois do smoke test funcionar)

- **Melhorar o VLM se a qualidade do captioning for insuficiente** — um VLM pequeno (<2B) tende
  a gerar legendas genéricas ("gráfico de barras") sem capturar o conteúdo semântico real da
  imagem (qual categoria/componente teve o valor mais alto, por exemplo) — se isso acontecer no
  smoke test, o próximo passo é trocar de modelo, não assumir que a arquitetura caption-then-embed
  está errada.
- **Harness formal para retrieval multimodal** — um golden set de perguntas sobre as imagens,
  medindo Recall@k/MRR como já se faz para retrieval de texto.
- **Integrar à produção só depois do harness confirmar que não regride nada** — mesma regra de
  não aceitar regressão que vale para qualquer outra migração/adição ao sistema.
- **ColPali/ColQwen2 como via secundária** — avaliar se compensa quando o volume de imagens
  crescer o suficiente para a legenda perder informação demais na prática (mensurável, não
  decidir por achismo).
- **GraphRAG-sobre-estrutura** (ex. formato DEXPI para diagramas P&ID) — só relevante se houver
  diagrama real em formato estruturado formal disponível, não para imagens sintéticas de teste.

## Como usar esta skill

- Ao ser invocada, reler a decisão de arquitetura acima antes de sugerir abordagem — não
  redecidir CLIP vs. captioning do zero a cada vez.
- Seguir o checklist 1→4 em ordem na primeira implementação; os itens de roadmap não bloqueiam
  a entrega inicial.
- Se o VLM principal falhar, documentar o fallback usado antes de prosseguir — é informação que
  a próxima invocação da skill precisa saber para não repetir a mesma tentativa falha.
- Medir antes de apontar produção para o pipeline multimodal — mesma disciplina de qualquer
  migração ou adição de funcionalidade nova ao sistema.
