---
name: replicacao-experimento-agente
description: Protocolo de replicação e disciplina experimental para agentes com LLM (7 disciplinas, com citação formal — AI Agents That Matter, Holistic Agent Leaderboard, Rollout Cards) — os três artefatos obrigatórios (código, trace, relatório), record-replay de chamadas externas (gravando a decisão do LLM, não a chamada HTTP), pin de versão, custo como métrica primária, ablação sempre por flag de configuração, baseline de agente único a custo normalizado antes de aceitar ganho multiagente, manifesto de omissões, e variância entre execuções. Use quando o usuário for replicar um paper/benchmark de agente, comparar duas versões de um agente, ou perguntar "como reportar um experimento de agente de forma que seja ciência e não só software".
---

# Protocolo de replicação de experimento com agente

## O que separa ciência de "só rodou e funcionou"

Sete disciplinas (cinco originais + duas adicionadas na revisão de 2026-09, ver fontes ao
final), citadas na literatura de pesquisa em agentes como o que decide se um resultado é
comparável e reprodutível, ou só uma anedota de uma execução:

1. **Record-replay** de chamadas externas (LLM, tools, banco de dados) — **com a técnica
   correta** (ver seção dedicada abaixo: gravar em nível HTTP quebra agentes).
2. **Pin de versão** exata do modelo em todo trace — nunca "gpt-4" ou "llama3", sempre a tag
   exata usada naquela execução.
3. **Custo** (tokens de entrada/saída, latência) tratado como métrica desde o primeiro
   experimento — não telemetria opcional adicionada depois. Embasado por
   *AI Agents That Matter* (Kapoor et al., Princeton, arXiv:2407.01502): foco estreito em
   acurácia sem atenção a custo torna agentes SOTA "desnecessariamente complexos e caros"; a
   avaliação correta é **cost-controlled**, otimizando acurácia×custo em conjunto — o achado
   central do paper é que **baselines simples alcançam eficiência de Pareto sobre agentes SOTA
   complexos** quando o custo entra na conta.
4. **Ablação sempre por flag de configuração**, nunca por branch de código — um experimento
   ligar/desligar uma camada deve ser uma linha de configuração, não uma edição de arquivo.
5. **Baseline justo**: a regra mais importante e mais frequentemente pulada — **um experimento
   multiagente sem baseline de agente único a custo normalizado não é uma conclusão válida**.
   Ver seção dedicada abaixo — essa disciplina tem hoje apoio empírico e teórico forte, não é
   só cautela metodológica.
6. **Manifesto de omissões (drops manifest)** *(nova)* — registrar explicitamente quais
   campos/linhas cada análise leu ou descartou antes de calcular a métrica final reportada.
7. **Reportar variância, não só média** *(nova)* — um score de agente sem número de rollouts e
   sem dispersão entre execuções não é reportável (ver seção dedicada abaixo).

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

**Correção importante (revisão 2026-09): NÃO grave em nível HTTP.** Ferramentas de
record-replay genéricas (VCR.py, `responses`, `pytest-recording`) mockam a camada de rede
inteira — e isso **quebra agentes especificamente**: as tools nunca executam de verdade (o
mock intercepta a chamada HTTP antes dela chegar em qualquer lugar), então o loop do agente
trava sobre um resultado de tool congelado/fake, mesmo quando a tool deveria ter rodado de
novo com um input ligeiramente diferente. A técnica correta para agente é **gravar só a decisão
do LLM (qual tool chamar, com que argumento) e deixar as tools executarem de verdade** — assim
o custo de API zera, o replay é determinístico na parte que interessa (decisão do modelo), e o
efeito colateral real da tool (escrever um arquivo, consultar um banco) continua acontecendo
como em produção. Nenhuma lib se consolidou como "VCR.py para agentes" ainda — opções
nomeáveis: `langchain-replay` (implementa exatamente essa abordagem — grava decisão do LLM,
executa tool no filesystem real) e `vcr-langchain` (abordagem HTTP clássica, com a limitação
acima). Recomendação: adotar a PROPRIEDADE (gravar decisão do LLM, não a chamada HTTP), não
amarrar numa lib específica ainda.

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

**Esta regra deixou de ser só cautela do autor — tem apoio empírico e teórico direto (revisão
2026-09)**:

- *Rethinking the Value of Multi-Agent Workflow: A Strong Single Agent Baseline*
  (arXiv:2601.12307) — mostra, com AFlow, que um baseline de LLM único **iguala** alternativas
  multiagente heterogêneas descobertas automaticamente, com MENOS custo computacional. Em
  workflows homogêneos, um único LLM pode fazer role-play de vários "agentes" via conversa
  multi-turno, reusando KV cache compartilhado — iguala ou supera o multiagente de fato, a
  custo substancialmente menor.
- *Why Do Multi-Agent LLM Systems Fail?* (Cemri et al., arXiv:2503.13657) — atribui grande
  parte das falhas em sistemas multiagente a problemas de COORDENAÇÃO e ESPECIFICAÇÃO entre
  agentes, não a fraqueza de um agente individual. Publica o MAST-Data: 1.600+ traces anotados
  em 7 frameworks MAS populares — primeiro dataset a mapear a dinâmica de falha multiagente
  (útil também como referência de formato de trace anotado, ver skill `esquema-de-trace-agentes`).
- *Single-Agent LLMs Outperform Multi-Agent Systems on Multi-Hop Reasoning Under Equal Thinking
  Token Budgets* (2026) — argumento teórico via Data Processing Inequality, com avaliação sob
  orçamento de compute pareado (o total de tokens do MAS distribuído entre agentes paralelos é
  igual ao do agente único): os trade-offs de coordenação de um MAS são **estruturais**, não
  específicos de um modelo ou implementação particular.

**Enquadramento correto ao aplicar esta disciplina**: não é "multiagente não presta" — é "o que
torna a alegação de que multiagente ajudou, defensável". Uma proposta de sistema multiagente que
já chega com esse controle feito é mais forte, não mais fraca, num grupo de pesquisa.

## Verificação programática bate LLM-as-judge, quando disponível

Princípio 2026 relevante para a fase de "avaliar se a execução teve sucesso": **"verifiable
beats judgeable"** — quando existe uma checagem programática possível (string match exato,
execução de código com resultado determinístico, validação de schema), ela é mais rápida, mais
barata e mais consistente entre execuções do que pedir a outro LLM para julgar se a resposta
está certa. LLM-as-judge introduz sua própria variância e seu próprio viés — usar como último
recurso, não como padrão default quando uma checagem determinística é possível.

## Manifesto de omissões (drops manifest)

Nenhuma das disciplinas acima cobre, por padrão, o que foi DESCARTADO da análise antes do
número final ser calculado — linhas filtradas por erro de execução, amostras excluídas por
timeout, casos ambíguos removidos manualmente. Registrar isso explicitamente (quantas
linhas/campos, por que critério, em que etapa) é barato de implementar e é a diferença entre um
número auditável e um número que parece preciso mas esconde decisões silenciosas. Formaliza-se
como parte do Rollout Card (ver skill `esquema-de-trace-agentes`), mas vale aplicar mesmo antes
de gerar o relatório final — registrar no momento em que a omissão acontece, não reconstruir
depois de memória.

## Reportar variância, não só média

Um único número de "taxa de sucesso" sem contexto de quantas execuções geraram esse número, e
sem alguma medida de dispersão entre execuções repetidas da mesma configuração, não é um
resultado reportável — é um ponto de amostra único apresentado como se fosse estável. Medido em
escala pelo *Holistic Agent Leaderboard* (HAL, arXiv:2510.11977, Kapoor et al.): 21.730 rollouts
de agente, 9 modelos × 9 benchmarks, ~2,5 bilhões de tokens, ~US$ 40 mil de custo total — infra
padronizada que reduziu o tempo de rodar uma avaliação "de semanas para horas". Dois achados do
HAL relevantes além do argumento de variância: (1) **maior esforço de raciocínio do modelo
REDUZIU a acurácia na maioria das execuções testadas** — contraintuitivo, reforça não assumir
que "pensar mais" sempre ajuda sem medir; (2) inspeção de logs assistida por LLM revelou má
conduta do próprio agente (buscar o dataset do benchmark em vez de resolver a tarefa, explorar
vazamento de informação) — argumento direto para por que trace é obrigatório e score sozinho não
basta (reforça a Regra permanente dos três artefatos, acima).

## Como aplicar

1. Defina o esquema de trace antes de rodar qualquer experimento (skill
   `esquema-de-trace-agentes`).
2. Pin de versão do modelo em todo trace desde a primeira execução — não adicionar depois.
3. Capture tokens/latência desde o primeiro experimento, mesmo que a análise de custo não seja
   o foco imediato — retrofitar isso depois é retrabalho evitável.
4. Toda camada opcional (self-repair, segunda opinião, memória, rerank) como flag booleana.
5. Antes de comparar duas versões de um agente, grave a decisão do LLM (não a chamada HTTP
   inteira) na primeira execução real e reexecute a segunda versão em modo replay, deixando as
   tools executarem de verdade.
6. Nunca reporte ganho de uma camada multiagente sem o baseline de agente único a custo
   normalizado.
7. Prefira checagem programática a LLM-as-judge sempre que uma checagem determinística for
   possível.
8. Registre o que foi descartado da análise (drops manifest) no momento em que descarta, não
   depois de memória.
9. Reporte quantas execuções geraram cada número e alguma medida de dispersão entre elas — não
   só a média de uma rodada.
10. Entregue os três artefatos (código, trace, relatório) — nunca menos.

## Não fazer

- Não pule o baseline de agente único "porque obviamente múltiplos agentes ajudam" — essa
  suposição é exatamente o que a regra existe para testar, não para presumir.
- Não implemente ablação como comentário de código — vira ciência não reproduzível por outra
  pessoa sem reler o diff exato que você rodou.
- Não meça sucesso/custo em execuções sem controle de chamadas externas e chame isso de
  comparação — sem record-replay (ou repetição estatística suficiente), a variância do próprio
  LLM pode ser maior que o efeito que você está tentando medir.
- Não use record-replay genérico em nível HTTP (VCR.py, `responses`) para testar um agente —
  quebra a execução real de tools; grave a decisão do LLM, não a chamada de rede.
- Não reporte um único número de sucesso sem dizer quantas execuções o geraram nem alguma
  medida de dispersão entre elas.

## Ver também

`esquema-de-trace-agentes` — o formato de trace que este protocolo assume como pré-requisito.
`padrao-react-raciocinio-acao` — o padrão de agente mais comum a que esta disciplina se aplica.
`padrao-gerador-validador` — quando a "camada extra" do baseline justo é especificamente um
segundo agente crítico/validador.

## Fontes (pesquisa de estado da arte, 2026-09)

- [AI Agents That Matter (arXiv:2407.01502)](https://arxiv.org/abs/2407.01502)
- [Holistic Agent Leaderboard (arXiv:2510.11977)](https://arxiv.org/abs/2510.11977)
- [Rollout Cards: A Reproducibility Standard for Agent Research (arXiv:2605.12131)](https://arxiv.org/html/2605.12131v1)
- [Rethinking the Value of Multi-Agent Workflow: A Strong Single Agent Baseline (arXiv:2601.12307)](https://arxiv.org/html/2601.12307v1)
- [Why Do Multi-Agent LLM Systems Fail? (arXiv:2503.13657)](https://arxiv.org/abs/2503.13657)
- [Scaling Behavior of Single LLM-Driven Multi-Agent Systems (arXiv:2606.00655)](https://arxiv.org/pdf/2606.00655)
- [langchain-replay (sixty-north)](https://github.com/sixty-north/langchain-replay) / [Deterministic Testing for LangChain Agents](https://blog.sixty-north.com/deterministic-testing-for-langchain-agents.html)
- [vcr-langchain](https://github.com/amosjyng/vcr-langchain)
- [Get Experience from Practice: LLM Agents with Record & Replay (arXiv:2505.17716)](https://arxiv.org/html/2505.17716v1)
