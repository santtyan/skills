---
name: memoria-longo-prazo-agentes
description: Guia de arquitetura para memória de longo prazo por usuário em agentes com LLM — distingue memória de histórico de conversa e de session state, apresenta a arquitetura memory stream → reflection → planning e a paginação hierárquica MemGPT (ambas validadas empiricamente), e as armadilhas mais comuns (falha de retrieval, memória fabricada). Use quando o usuário perguntar como fazer um agente "lembrar" preferências entre sessões, estiver desenhando um sistema de memória persistente, tiver histórico que excede a janela de contexto do modelo, ou confundir memória com histórico de chat/estado de sessão.
---

# Memória de longo prazo em agentes com LLM

## A distinção que evita a maior parte da confusão de arquitetura

Três conceitos que parecem a mesma coisa, mas têm escopo e propósito diferentes:

| Conceito | Armazena | Escopo | Serve para |
|---|---|---|---|
| **Memory** (memória de longo prazo) | Fatos extraídos sobre um usuário | por `user_id`, através de sessões | Preferências, dados de perfil, metas recorrentes |
| **Chat history** (histórico de conversa) | Mensagens e chamadas de tool de execuções anteriores | por `session_id` | Continuidade conversacional dentro de uma thread |
| **Session state** (estado de sessão) | Dados de aplicação gerenciados por código/tools | por `session_id` | Carrinho de compras, listas de tarefas, progresso de workflow, contadores |

Os três podem — e costumam — trabalhar juntos no mesmo agente: um agente de suporte pode usar
memória para a preferência de comunicação do cliente, histórico para o ticket atual em
andamento, e session state para o status desse ticket. Tratar os três como a mesma coisa é a
causa mais comum de um agente "esquecer" algo que deveria persistir, ou "lembrar" algo que
deveria ter sido descartado ao fim da sessão.

## Arquitetura de referência: memory stream → reflection → planning

Validada empiricamente no paper "Generative Agents: Interactive Simulacra of Human Behavior"
(Park, O'Brien, Cai, Morris, Liang, Bernstein — Stanford/Google/UIST 2023). Três componentes:

1. **Memory stream**: um registro cronológico abrangente, em linguagem natural, de tudo que o
   agente observou/experimentou — não estruturado como banco relacional, e sim como uma lista
   de eventos textuais com timestamp.
2. **Reflection**: síntese recursiva do memory stream em inferências de nível mais alto —
   transforma uma pilha de eventos brutos em conclusões (ex.: de "vi X três vezes esta semana"
   para "X é um padrão recorrente que preciso agir sobre"). Sem isso, o agente acumula dados mas
   nunca generaliza a partir deles.
3. **Planning**: traduz as conclusões da reflection e o ambiente atual em ações concretas —
   fecha o loop entre "lembrar/entender" e "agir".

**Achado central do paper (via estudo de ablação)**: removendo qualquer um dos três componentes,
a coerência/credibilidade do comportamento do agente degrada de forma mensurável. Não são
camadas opcionais umas em relação às outras — memória sem síntese vira um log que ninguém usa
de fato; síntese sem retrieval eficiente não tem o que sintetizar; planejamento sem os dois
anteriores é reativo demais para ter continuidade real.

Para o mecanismo de retrieval específico: o paper combina relevância (similaridade semântica),
recência (eventos recentes pesam mais) e importância (uma pontuação de quão significativo é
aquele evento) para decidir quais memórias trazer de volta ao contexto do modelo em cada
momento — não é só top-k por similaridade pura.

## Arquitetura complementar: paginação hierárquica (MemGPT)

Enquanto memory stream→reflection→planning descreve O QUE fazer com memória (síntese em níveis
crescentes de abstração), o paper "MemGPT: Towards LLMs as Operating Systems" (Packer, Wooders,
Lin, Fang, Patil, Stoica, Gonzalez — UC Berkeley, arXiv:2310.08560) descreve COMO gerenciar
fisicamente o que cabe no contexto do modelo — os dois são complementares, não concorrentes.

**A analogia central**: o contexto fixo de um LLM é tratado como "memória principal" (RAM) num
sistema operacional, e um armazenamento externo ilimitado como "disco". MemGPT usa function
calls para deixar o próprio LLM mover dados entre os dois níveis — igual a paginação de memória
virtual em SOs tradicionais.

Três componentes do contexto principal (os "prompt tokens"):
1. **System instructions** — somente leitura, explica ao modelo como usar o próprio sistema de
   memória (quais functions existem, quando usá-las).
2. **Working context** — bloco de tamanho fixo, leitura/escrita só via function call, guarda
   fatos-chave sobre o usuário/persona ativa (equivalente funcional à "Memory" da tabela acima).
3. **FIFO queue** — histórico rolante de mensagens recentes; quando o contexto se aproxima do
   limite, um "queue manager" primeiro avisa o modelo ("memory pressure") para que ele salve o
   que for importante em armazenamento externo antes que as mensagens antigas sejam removidas da
   janela (e resumidas recursivamente num sumário, não simplesmente descartadas).

Armazenamento externo (fora do contexto, acessado só via function call de busca paginada):
- **Recall storage**: histórico completo de mensagens já processadas, buscável por texto.
- **Archival storage**: base de conhecimento de longo prazo, tipicamente com busca vetorial.

**Achado quantitativo forte** (Table 2 do paper, tarefa de "deep memory retrieval" — responder
uma pergunta que só pode ser respondida com conhecimento de conversas 5 sessões atrás): GPT-4
sozinho atinge 32,1% de acurácia; GPT-4 + MemGPT atinge **92,5%** — ganho de mais de 60 pontos
percentuais. Em GPT-3.5 Turbo o ganho é de 38,7% para 66,9%. O mesmo padrão se replica numa
tarefa sintética de busca aninhada chave-valor (nested key-value retrieval): modelos sem MemGPT
caem a 0% de acurácia a partir de 2-3 níveis de aninhamento; MemGPT com GPT-4 mantém performance
estável independente do número de níveis, porque consegue fazer múltiplas buscas paginadas em
sequência via function calling em vez de depender de tudo estar simultaneamente no contexto.

**Quando essa arquitetura vale o esforço**: quando o volume de histórico/conhecimento excede
sistematicamente a janela de contexto do modelo em uso — não é necessária para agentes com poucas
sessões curtas por usuário, onde o contexto já comporta tudo sem paginação. É mais relevante
quanto menor a janela de contexto do modelo local em uso (o ganho relativo do paper é maior em
modelos com contexto menor).

## Dois modos de captura de memória

Referência de implementação prática (Agno framework, mas o padrão é framework-agnóstico):

- **Automático**: uma etapa de extração roda a cada execução, processando a entrada do usuário
  em memórias de forma consistente e previsível. Bom quando você quer controle determinístico
  sobre quando memórias são criadas.
- **Agêntico**: o próprio modelo decide, durante a execução, se algo merece virar memória
  (tipicamente via uma tool dedicada, ex. `update_user_memory`). Mais natural/flexível, mas
  menos previsível — o modelo pode deixar de salvar algo relevante ou salvar algo trivial demais.

Os dois modos não devem ser usados simultaneamente no mesmo agente — quando ambos estão
habilitados, geralmente um toma precedência e o outro é ignorado silenciosamente, o que pode
confundir debugging se não for uma escolha deliberada.

## Armadilhas empíricas documentadas

O mesmo paper de referência relatou, em duas avaliações (controlada e end-to-end), que os erros
mais comuns não vinham do LLM "alucinando" texto aleatório sem relação com nada — vinham de:

1. **Falha de retrieval** — a memória certa existia no stream, mas não foi recuperada no momento
   em que era relevante. Mesma classe de problema que retrieval impreciso em RAG sobre
   documentos, só que aplicado a eventos/fatos sobre o usuário em vez de um corpus de texto
   estático.
2. **Embelezamento fabricado** — o agente reconstruiu uma memória de um jeito que não
   correspondia exatamente ao que aconteceu, um tipo específico de alucinação que nasce da
   síntese (reflection), não da geração de texto livre.

Isso implica que testar um sistema de memória de longo prazo exige medir especificamente esses
dois modos de falha — não basta testar se o agente "lembra alguma coisa", é preciso testar se
ele recupera o fato certo, no momento certo, sem distorcê-lo.

## Como aplicar

1. **Decida o escopo antes de escolher a tecnologia**: o dado precisa sobreviver entre sessões
   do mesmo usuário (memória), só dentro da conversa atual (histórico), ou é estado de aplicação
   que não é "sobre o usuário" (session state)? Escolher a tecnologia de persistência antes de
   responder isso é uma causa comum de retrabalho.
2. **Não pule a síntese**: armazenar cada mensagem/evento bruto sem nenhuma camada de reflection
   funciona para volumes pequenos, mas degrada rápido conforme o histórico cresce — o agente
   passa a ter memória, mas não "entendimento" do que ela significa.
3. **Escolha um modo de captura, não os dois** — automático se você precisa de previsibilidade
   auditável, agêntico se a naturalidade da interação importa mais que o controle.
4. **Meça falha de retrieval e memória fabricada especificamente**, não só "o agente lembrou ou
   não" de forma binária — os dois modos de falha pedem diagnósticos diferentes (o primeiro é
   problema de busca/indexação, o segundo é problema de como a síntese está sendo feita).

## Conexão com outras skills deste repositório

Memória (curto e longo prazo) é citada como um dos benefícios centrais de frameworks de
orquestração de agentes como LangGraph — se o seu projeto já usa `migrar-para-langchain` ou
`roadmap-rag-survey` deste repositório, memória de longo prazo por usuário é uma extensão
natural do mesmo runtime, não um sistema à parte.
