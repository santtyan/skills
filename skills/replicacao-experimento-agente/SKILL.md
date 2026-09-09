---
name: replicacao-experimento-agente
description: Protocolo de replicação e disciplina experimental para agentes com LLM — os três artefatos obrigatórios (código, trace, relatório), record-replay de chamadas externas, pin de versão, ablação sempre por flag de configuração, e a regra de baseline justo (multiagente vs. agente único a custo normalizado). Use quando o usuário for replicar um paper/benchmark de agente, comparar duas versões de um agente, ou perguntar "como reportar um experimento de agente de forma que seja ciência e não só software".
---

# Protocolo de replicação de experimento com agente

## O que separa ciência de "só rodou e funcionou"

Cinco disciplinas, citadas na literatura de pesquisa em agentes como o que decide se um
resultado é comparável e reprodutível, ou só uma anedota de uma execução:

1. **Record-replay** de chamadas externas (LLM, tools, banco de dados).
2. **Pin de versão** exata do modelo em todo trace — nunca "gpt-4" ou "llama3", sempre a tag
   exata usada naquela execução.
3. **Custo** (tokens de entrada/saída, latência) tratado como métrica desde o primeiro
   experimento — não telemetria opcional adicionada depois.
4. **Ablação sempre por flag de configuração**, nunca por branch de código — um experimento
   ligar/desligar uma camada deve ser uma linha de configuração, não uma edição de arquivo.
5. **Baseline justo**: a regra mais importante e mais frequentemente pulada — **um experimento
   multiagente sem baseline de agente único a custo normalizado não é uma conclusão válida**.

## Regra permanente: três artefatos, nunca menos

Toda replicação ou experimento com agente entrega:

1. **Código** — a implementação executável do agente/experimento.
2. **Trace** — ver skill `esquema-de-trace-agentes` para o formato recomendado. Sem trace, não
   dá para saber SE ou POR QUE algo funcionou, só QUE funcionou (ou não) uma vez.
3. **Relatório de replicação** (Rollout Card ou equivalente) — resumo legível por humano de
   modelo+versão, prompt, tools, dependências, custo, taxa de sucesso, distribuição de falhas.

Um resultado sem trace não é resultado. Um trace sem relatório não é comunicável.

## Record-replay: por que "rodar de novo" não basta para comparar

Reexecutar um agente para testar uma mudança (prompt diferente, teto de iteração diferente)
também muda as respostas do LLM em si, se as chamadas externas não forem controladas — fica
impossível separar "o que mudou por causa da mudança testada" de "o que mudou porque o LLM é
não-determinístico ou o ambiente mudou entre as duas execuções".

Mecanismo: gravar (modo *record*) as respostas reais de cada chamada externa, indexadas por uma
chave estável (hash do prompt+parâmetros, ou da query), a partir da primeira execução real. Ao
comparar uma segunda versão do agente, rodar em modo *replay*: qualquer chamada que bata
exatamente com uma já gravada devolve a resposta gravada, sem tocar a API/banco de novo;
qualquer chamada **nova** (o prompt mudou de fato nesse ponto) fica visível como "miss" — o
sinal de que aquele ponto do fluxo realmente mudou de comportamento, não um erro do mecanismo.

Design recomendado: fail-open no miss (executa a chamada real e segue, nunca trava o
experimento), mas reporta contagem de hits/misses no relatório — um miss não invalida a
comparação por si só, mas precisa aparecer para o pesquisador decidir se invalida.

## Ablação por flag: o padrão a copiar

Nunca implemente uma camada extra (self-repair, segunda opinião de outro agente, rerank,
memória) como algo que só existe se você comentar/descomentar código. Sempre como parâmetro
booleano explícito na função/classe que a controla (`usar_x=True/False`). Isso é o que torna um
experimento de ablação uma linha de configuração em vez de uma tarefa de engenharia.

## Baseline justo: a regra que mais se pula

Antes de reportar que "múltiplos agentes" ou "uma camada de crítica/revisão" melhorou algo,
meça e reporte também: o mesmo problema resolvido por um agente único, **ao mesmo custo total de
tokens** (não ao mesmo número de chamadas — uma chamada com prompt 5x maior não é comparável a
uma chamada simples). Se a camada extra não supera esse baseline normalizado por custo, a
conclusão correta é "não vale a pena", não "funcionou porque tem mais um agente".

## Como aplicar

1. Defina o esquema de trace antes de rodar qualquer experimento (skill
   `esquema-de-trace-agentes`).
2. Pin de versão do modelo em todo trace desde a primeira execução — não adicionar depois.
3. Capture tokens/latência desde o primeiro experimento, mesmo que a análise de custo não seja
   o foco imediato — retrofitar isso depois é retrabalho evitável.
4. Toda camada opcional (self-repair, segunda opinião, memória, rerank) como flag booleana.
5. Antes de comparar duas versões de um agente, grave uma fita de record-replay na primeira
   execução real e reexecute a segunda versão em modo replay.
6. Nunca reporte ganho de uma camada multiagente sem o baseline de agente único a custo
   normalizado.
7. Entregue os três artefatos (código, trace, relatório) — nunca menos.

## Não fazer

- Não pule o baseline de agente único "porque obviamente múltiplos agentes ajudam" — essa
  suposição é exatamente o que a regra existe para testar, não para presumir.
- Não implemente ablação como comentário de código — vira ciência não reproduzível por outra
  pessoa sem reler o diff exato que você rodou.
- Não meça sucesso/custo em execuções sem controle de chamadas externas e chame isso de
  comparação — sem record-replay (ou repetição estatística suficiente), a variância do próprio
  LLM pode ser maior que o efeito que você está tentando medir.

## Ver também

`esquema-de-trace-agentes` — o formato de trace que este protocolo assume como pré-requisito.
`padrao-react-raciocinio-acao` — o padrão de agente mais comum a que esta disciplina se aplica.
`padrao-gerador-validador` — quando a "camada extra" do baseline justo é especificamente um
segundo agente crítico/validador.
