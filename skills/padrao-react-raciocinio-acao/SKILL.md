---
name: padrao-react-raciocinio-acao
description: O paradigma ReAct (raciocínio e ação intercalados) para reduzir alucinação e melhorar tarefas de decisão em agentes com LLM, com evidência quantitativa do paper original e das extensões diretas (Reflexion, SWE-agent/ACI, LATS), mais orientação de 2026 sobre framework (create_agent do LangChain v1, não o create_react_agent depreciado) e escolha de benchmark (evitar HotpotQA, preferir τ²-bench/ALFWorld/GAIA). Use quando o usuário estiver desenhando um agente que precisa buscar informação externa antes de responder, replicando um agente ReAct simples sobre uma tarefa de benchmark, avaliando se vale intercalar "pensamento" com chamadas de tool, ou tentando entender a base teórica de um "critic node"/self-repair já planejado.
---

# Padrão ReAct — raciocínio e ação intercalados

## O paradigma

Do paper "ReAct: Synergizing Reasoning and Acting in Language Models" (Yao, Zhao, Yu, Du,
Shafran, Narasimhan, Cao — Princeton/Google, ICLR 2023, arXiv:2210.03629). A ideia central: em
vez de o modelo só "pensar" (chain-of-thought puro, sem tocar o mundo externo) ou só "agir" (gerar
ações sem raciocínio explícito entre elas), intercale os dois — um "thought" (texto livre que não
afeta o ambiente) seguido de uma "action" (que afeta o ambiente e gera uma "observation").

O ciclo: **Thought → Action → Observation → Thought → Action → Observation → ...** até a tarefa
terminar. O thought usa o contexto acumulado (incluindo observações reais do ambiente) para
decidir a próxima ação, decompor a tarefa, lidar com uma exceção, ou perceber que precisa buscar
mais informação — e cada action devolve uma observation real, não uma suposição do modelo.

## Por que isso reduz alucinação (evidência do paper)

Comparando as 4 abordagens (Standard, Chain-of-Thought puro, Act-only, ReAct) em tarefas de
pergunta-resposta com múltiplos saltos (HotpotQA): chain-of-thought puro tem **56% dos seus
casos de falha causados por alucinação** de fatos que o modelo "lembrou" errado do próprio
treinamento — porque ele nunca checa contra nada externo. ReAct, ao intercalar busca real (via
uma API simples de busca) com o raciocínio, **zera esse modo de falha** (0% de alucinação nos
casos de erro analisados) — o preço é um tipo diferente de erro (buscar a informação errada), mas
esse é mais fácil de diagnosticar e corrigir do que uma alucinação silenciosa.

**Contexto necessário sobre esse número (revisão 2026-09)**: é uma análise de erro do estudo
original — amostra pequena de trajetórias sobre HotpotQA, com GPT-3/PaLM de 2022. Não é uma taxa
universal de alucinação de "ReAct" como método; é evidência qualitativa forte do MECANISMO
(fundamentar raciocínio em observação externa reduz um tipo específico de erro), não um número
que se replica automaticamente em qualquer modelo/benchmark novo.

**Contraponto igualmente importante, de literatura mais recente**: ReAct "ingênuo" (sem cuidado
de implementação) tem acurácia consistentemente MENOR que function calling paralelo e
LLMCompiler em comparações diretas (arXiv:2312.04511), por dois modos de falha nomeados e
recorrentes:
- **regeneração redundante** — o agente re-emite uma chamada de tool já feita antes, gastando
  passos e tokens sem necessidade;
- **parada prematura** — o agente conclui a partir de uma observação intermediária incompleta,
  antes de reunir toda a evidência necessária.

Esses dois bugs são os que mais aparecem na primeira implementação de um ReAct do zero — vale
testar explicitamente para os dois no golden set de qualquer replicação.

**Aprendizado central, generalizável além do paper**: fundamentar o raciocínio de um modelo em
ações que trazem observação real do mundo externo é uma forma direta de reduzir a taxa de
alucinação — mais eficaz do que só pedir para o modelo "ter cuidado" ou "verificar" dentro do
próprio raciocínio isolado.

## Por que thought esparso, não denso, em tarefas de decisão longa

Em tarefas de decisão com muitas ações possíveis (ex.: navegar um ambiente simulado, ALFWorld),
o paper mostra que thoughts não precisam aparecer entre TODA ação — só nos pontos mais relevantes
da trajetória (decompor o objetivo, decidir o próximo subobjetivo, notar que algo deu errado).
Deixar o próprio modelo decidir quando pensar (em vez de forçar thought em cada passo) funciona
melhor e é mais barato. **ReAct supera "Act-only" (sem nenhum thought) por margem ampla** —
ganho relativo médio de 62% em success rate no benchmark testado — e também supera uma variante
que só reage passivamente a feedback do ambiente sem "pensamento" de verdade (comparação com
"Inner Monologue"-style prompting): reagir a observação não é o mesmo que raciocinar sobre ela.

## Como aplicar

1. **Não peça só ação, e não peça só raciocínio isolado** — se a tarefa exige informação que o
   modelo não tem de forma confiável (fatos específicos, estado atual de um sistema externo),
   dê a ele uma ação real de busca/consulta e deixe o raciocínio intercalar com o resultado real
   dessa busca.
2. **Thought esparso é aceitável e às vezes melhor** — não force um passo de "pensamento" a cada
   ação em tarefas com muitos passos; deixe o modelo decidir quando o raciocínio explícito ajuda.
3. **Combine com self-consistency quando o raciocínio isolado (sem ação) também é uma opção
   válida** — o paper mostra que o melhor resultado geral vem de uma estratégia híbrida: usar
   ReAct como padrão e recorrer a chain-of-thought com múltiplas amostras (self-consistency)
   quando ReAct não retorna resposta dentro de um número razoável de passos, ou vice-versa
   quando o conhecimento interno do modelo já é suficientemente confiante.
4. **Ações que não retornam informação útil derailam o raciocínio** — no paper, 23% dos casos de
   falha de ReAct vieram de buscas que não retornaram nada relevante, não de raciocínio ruim.
   Isso significa que a qualidade da ferramenta de busca/ação disponível ao modelo importa tanto
   quanto o padrão de raciocínio em si — um ReAct com retrieval ruim ainda falha.

   **Isso deixou de ser só uma dica prática — virou princípio de primeira ordem, com nome e
   evidência quantitativa (revisão 2026-09)**: o paper do SWE-agent (NeurIPS 2024,
   arXiv:2405.15793) formaliza esse achado como tese da **ACI (Agent-Computer Interface)** —
   desenhar a interface entre agente e ambiente (comandos de busca/navegação sob medida,
   formato de observação, guardrails) é parte do problema, não um detalhe de implementação.
   Resultado medido: o MESMO modelo (GPT-4), com o MESMO enunciado de tarefa, roda ~2× melhor
   no SWE-Bench só trocando `bash` cru por uma ACI desenhada para o agente — sem tocar nos
   pesos do modelo. Ao implementar qualquer ReAct, investir tempo na interface das tools
   (mensagens de erro claras, truncar output verboso, validar formato antes de devolver
   observação) tende a valer mais do que ajustar o prompt de raciocínio.

## Conexão com outros padrões já documentados

ReAct é o nome acadêmico original e a evidência empírica fundacional por trás do padrão
"self-repair"/"critic node" (avaliar e corrigir uma ação anterior via um novo ciclo de
raciocínio+ação) já coberto por outras skills deste repositório sobre migração para frameworks de
orquestração de agente (LangGraph e equivalentes) e sobre separação gerador/validador. Se você já
está implementando um desses padrões, ReAct é a referência teórica e a fonte da evidência
quantitativa que sustenta a decisão de design.

## Regra permanente: toda replicação entrega três artefatos

Ao replicar um agente ReAct (ou qualquer variante) sobre uma tarefa de benchmark, o resultado
esperado nunca é só "rodou e funcionou" — são sempre **três artefatos, nunca menos**:

1. **Código** — a implementação do agente em si (o laço Thought/Action/Observation, as tools).
2. **Trace** — um registro estruturado por execução (não texto livre): cada passo com
   thought/action/observation, modelo+versão usados, tokens/latência, e — se possível — as
   relações entre passos (o que dependeu do quê). Formato sugerido: JSON/JSONL com campos
   espelhando a convenção OpenTelemetry GenAI (`gen_ai.request.model`,
   `gen_ai.usage.input_tokens` etc) mais uma camada semântica de proveniência
   (SUPPORT/DERIVE/DEPEND_ON/CONTRADICT/INVALIDATE entre passos) — OTel puro não é suficiente
   para pesquisa em agentes, falta exatamente essa camada.
3. **Relatório de replicação** — um resumo legível por humano da coleção de execuções: modelo
   e versão, prompt usado, tools disponíveis, dependências com versão, custo total/por execução,
   taxa de sucesso, distribuição de modos de falha. Um formato de referência é o "Rollout Card"
   (por analogia a Model Cards): resolve o problema de que um agente acopla modelo + prompt +
   tools + retry logic + ambiente, e mudar qualquer peça muda o resultado medido sem que isso
   fique registrado em lugar nenhum.

**Por quê**: um resultado sem trace não é resultado — não dá para saber SE ou POR QUE algo
funcionou. Um trace sem relatório não é comunicável — ninguém lê JSONL bruto para entender o
que aconteceu. Os três juntos são o que torna uma replicação auditável e comparável contra uma
tentativa futura (mesmo modelo? mesmo prompt? o que mudou?).

## Extensões diretas de ReAct, com números (revisão 2026-09)

**Reflexion** (Shinn et al., NeurIPS 2023, arXiv:2303.11366) — adiciona um loop EXTERNO de
"reforço verbal": o agente tenta, falha, escreve uma autocrítica em linguagem natural sobre o
que deu errado, guarda essa crítica numa memória episódica, e tenta de novo levando essa memória
no próximo prompt. Não é fine-tuning — o "reforço" é texto, não gradiente. Números medidos:
**+22% em ALFWorld, +20% em HotpotQA, +11% em HumanEval** sobre baselines fortes; em ALFWorld,
130/134 tarefas resolvidas após 12 tentativas (vs. 108/134 do ReAct puro); taxa de alucinação
caiu de 32% para 3% ao longo de 10 tentativas. Custo real: exige múltiplas tentativas e um sinal
de recompensa/sucesso para acionar a autocrítica — não é gratuito, e não se aplica quando só há
1 tentativa disponível.

**SWE-agent / ACI** (NeurIPS 2024, arXiv:2405.15793) — ver a seção "Como aplicar" acima
(item 4) para os números. A contribuição não é um novo loop de raciocínio, é a tese de que
agentes LLM são "uma nova classe de usuário final" e merecem uma interface própria (não a
mesma CLI que um humano usaria).

**LATS — Language Agent Tree Search** (ICML 2024, arXiv:2310.04406) — busca em árvore (MCTS)
por cima de ReAct: o LLM atua como agente, função de valor E otimizador ao mesmo tempo,
amostrando e avaliando várias trajetórias ReAct em paralelo para escolher a melhor. Supera
ReAct, Reflexion, Chain-of-Thought, Tree-of-Thoughts e Reasoning-via-Planning nos benchmarks
testados (94,4% em HumanEval com GPT-4). **Importante para escopo**: LATS não substitui ReAct,
amplifica-o a um custo de compute muito maior (múltiplas trajetórias completas por decisão) —
não é o ponto de partida certo para uma primeira replicação simples de 2 semanas; mencionar
como "quando o orçamento permitir explorar mais", não como próximo passo natural.

## Frameworks de produção (2026) — como o padrão é implementado hoje

O loop Thought→Action→Observation continua sendo o modelo mental correto, mas raramente é
escrito manualmente como texto/prompt em 2026 — os provedores de LLM expõem tool-calling nativo
estruturado, e é isso que elimina a maior fonte de falha dos benchmarks de 2024 (erro de
formatação do prompt ReAct manual, não erro de raciocínio). **O padrão não foi absorvido pelo
modelo — o que foi absorvido foi a camada de parsing de texto livre.** O loop ainda está lá,
só que por baixo de uma API de tool-calling.

- **LangChain/LangGraph**: `create_react_agent` do LangGraph está **DEPRECIADO** — substituído
  por `create_agent` do pacote `langchain` (LangChain v1 / LangGraph v1), com um sistema de
  middleware (`@before_model`/`@after_model`) no lugar de configuração posicional. Ao escrever
  código novo: `from langchain.agents import create_agent`, não
  `from langgraph.prebuilt import create_react_agent`.
- **Claude Agent SDK**: `query()` roda o loop agêntico internamente e devolve um async
  iterator — o SDK cuida de orquestração, execução de tool, gestão de contexto e retry. Filosofia:
  "um computador para um agente" (harness dentro de um sandbox).
- **OpenAI Agents SDK**: orquestra vários agentes leves com handoffs e guardrails explícitos —
  harness separado do compute, filosofia distinta da do Claude Agent SDK.

## Benchmark para a primeira replicação — cuidado com HotpotQA

HotpotQA (o benchmark do paper ReAct original) **não é mais recomendado como primeira escolha
para avaliar agentes em 2026** — o próprio coautor do dataset, Peng Qi, publicou uma crítica
("Why You Should Stop Using HotpotQA for AI Agents Evaluation") apontando: formato extrativo
desalinhado de sistemas generativos (resposta correta na prática não recebe crédito automático),
pressuposto de que toda pergunta exige raciocínio multi-hop (nem sempre verdade), escopo restrito
a busca de conhecimento, e overfitting por reuso extensivo. Aparece em levantamentos 2026 na
categoria de benchmark **saturado**, ao lado de MMLU/HumanEval.

**Alternativas melhor embasadas para uma primeira replicação simples**:
- **τ²-bench** (`sierra-research/tau2-bench`) — domínios pequenos e bem delimitados (airline
  ~50, retail ~114, telecom ~114 exemplos), tool-calling contra um banco de dados realista,
  políticas explícitas de negócio — hoje o benchmark de referência para tool-use bem definido, e
  o candidato mais direto para "ReAct simples + trace" em 2 semanas.
- **ALFWorld** — se o objetivo for replicar fielmente o paper original (é onde Reflexion mede
  seu maior ganho sobre ReAct puro, útil como comparação histórica).
- **GAIA** — se o objetivo for algo mais moderno, mais citado, e mais difícil (menos indicado
  como primeiro exercício por causa disso).

Documentar explicitamente POR QUE o benchmark escolhido foi escolhido é parte do relatório de
replicação (ver seção abaixo) — o critério importa mais do que o benchmark em si.

## Fontes (pesquisa de estado da arte, 2026-09)

- [ReAct: Synergizing Reasoning and Acting in Language Models (arXiv:2210.03629)](https://arxiv.org/pdf/2210.03629) — paper original
- [Reflexion: Language Agents with Verbal Reinforcement Learning (arXiv:2303.11366)](https://arxiv.org/pdf/2303.11366)
- [SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering (arXiv:2405.15793)](https://arxiv.org/abs/2405.15793)
- [Language Agent Tree Search (arXiv:2310.04406)](https://arxiv.org/pdf/2310.04406)
- [An LLM Compiler for Parallel Function Calling (arXiv:2312.04511)](https://arxiv.org/pdf/2312.04511) — modos de falha do ReAct ingênuo
- [create_react_agent — aviso de depreciação (LangChain reference)](https://reference.langchain.com/python/langgraph.prebuilt/chat_agent_executor/create_react_agent)
- [Why You Should Stop Using HotpotQA for AI Agents Evaluation — Peng Qi](https://qipeng.me/blog/stop-using-hotpotqa/)
- [τ²-bench (sierra-research)](https://github.com/sierra-research/tau2-bench)
