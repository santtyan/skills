---
name: padrao-react-raciocinio-acao
description: O paradigma ReAct (raciocínio e ação intercalados) para reduzir alucinação e melhorar tarefas de decisão em agentes com LLM, com evidência quantitativa do paper original. Use quando o usuário estiver desenhando um agente que precisa buscar informação externa antes de responder, avaliando se vale intercalar "pensamento" com chamadas de tool, ou tentando entender a base teórica de um "critic node"/self-repair já planejado.
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

## Conexão com outros padrões já documentados

ReAct é o nome acadêmico original e a evidência empírica fundacional por trás do padrão
"self-repair"/"critic node" (avaliar e corrigir uma ação anterior via um novo ciclo de
raciocínio+ação) já coberto por outras skills deste repositório sobre migração para frameworks de
orquestração de agente (LangGraph e equivalentes) e sobre separação gerador/validador. Se você já
está implementando um desses padrões, ReAct é a referência teórica e a fonte da evidência
quantitativa que sustenta a decisão de design.
