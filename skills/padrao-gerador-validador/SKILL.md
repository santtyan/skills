---
name: padrao-gerador-validador
description: Guia de quando e como separar "quem gera/decide" de "quem valida/guarda" em sistemas com LLM — nunca confiar em instrução de prompt para fazer cumprir uma regra dura, preferir validação determinística ou um segundo agente crítico separado do gerador. Cita evidência real (paper AutoGen, paper AgentBench, OpenAI Agents SDK). Use quando o usuário perguntar se vale separar geração de validação em dois agentes/componentes, estiver desenhando um pipeline com LLM que precisa respeitar uma regra de segurança/negócio, ou quiser embasar essa decisão de arquitetura com fundamentação externa.
---

# Padrão gerador-validador (separar quem gera de quem valida)

## O princípio

Um LLM que gera algo (código, SQL, uma resposta, uma jogada) não deve ser o mesmo componente
que decide se esse algo é válido — mesmo quando o prompt do gerador já pede explicitamente para
"seguir a regra X". Instrução textual não é enforcement. Prefira, nessa ordem de preferência:

1. **Validação determinística em código** quando a regra é verificável objetivamente (ex.:
   "a query só pode ser SELECT", "o valor está dentro de um intervalo", "a jogada é permitida
   pelas regras do jogo").
2. **Um segundo agente/chamada de LLM separado, agindo como crítico**, quando a regra exige
   julgamento que código puro não cobre (ex.: "essa resposta é factualmente sustentada pelo
   contexto fornecido?").

O motivo de nunca confiar só na instrução do gerador: o mesmo processo que decidiu gerar algo
errado não tem motivo estrutural para reconhecer o próprio erro de forma confiável — ele já
"acreditava" que a saída estava certa quando a produziu.

## Evidência externa (não é só intuição de projeto)

**Paper AutoGen** (Wu et al., Microsoft Research, arXiv:2308.08155) traz três estudos empíricos
diretamente relevantes. Nota: o AutoGen como *framework* entrou em modo de manutenção em 2026
(sucedido pelo Microsoft Agent Framework) — a citação aqui é do paper acadêmico e dos dados que
ele reporta, que continuam válidos independente do ciclo de vida do produto; não é uma
recomendação de adotar o framework AutoGen em produção hoje.

- **Separar gerador de validador em dois agentes distintos** (em vez de um agente único fazendo
  as duas coisas) aumentou F1 de detecção de código inseguro em **+8% (GPT-4) e +35%
  (GPT-3.5-turbo)** num experimento de geração de código com checagem de segurança (estudo
  "OptiGuide"/A4 do paper). O ganho é maior justamente no modelo mais fraco — sugerindo que a
  separação compensa mais ainda quando o modelo individual é menos confiável.
- **Um "grounding agent"** (um segundo agente injetando conhecimento de senso comum/regras do
  domínio quando o sistema começa a repetir erros) trouxe **+15% de performance** num ambiente
  de tomada de decisão sequencial (estudo ALFWorld/A3 do paper) — mesmo padrão de "agente crítico
  externo corrigindo o principal".
- **Removendo um validador determinístico** (um "board agent" que checava se jogadas de xadrez
  eram legais) e substituindo por só uma instrução textual pedindo jogadas legais, o sistema
  quebrou com jogadas ilegais (estudo de xadrez conversacional/A6 do paper) — prova experimental
  direta de que instrução de prompt sozinha não é suficiente para impor uma regra dura, mesmo
  quando a regra é simples e o modelo é competente.

**Paper AgentBench** (Liu et al., Tsinghua/Ohio State/UC Berkeley, arXiv:2308.03688, ICLR 2024)
testa 29 LLMs (incluindo GPT-4 e Claude) como agentes autônomos em 8 ambientes reais distintos
(sistema operacional, banco de dados, grafo de conhecimento, jogos, navegação web). Duas das
cinco categorias de causa de falha que o paper define e mede diretamente são **"Invalid Format"**
(o agente não segue o formato de saída instruído) e **"Invalid Action"** (o agente segue o
formato, mas escolhe uma ação inválida) — mesmo em modelos de ponta. A conclusão central do
paper nomeia explicitamente **"poor instruction following"** como um dos principais obstáculos
para agentes LLM utilizáveis na prática. É uma terceira fonte independente, e a mais ampla em
escala (29 modelos, 8 ambientes reais, não um único sistema), mostrando que mesmo os modelos mais
fortes disponíveis não seguem instrução de formato/ação de forma confiável só por serem
instruídos a isso — reforça que validação externa ao gerador não é uma cautela excessiva, é
proporcional ao problema real medido.

**OpenAI Agents SDK** (docs oficiais) formaliza o mesmo padrão como "Guardrails": validação de
entrada/saída que roda em paralelo à execução do agente, "falhando rápido" quando a checagem não
passa — é a mesma ideia descrita como um recurso de primeira classe do SDK, não uma prática
improvisada.

Quatro fontes independentes (dois papers acadêmicos com dados quantitativos — um focado num
padrão de arquitetura, outro numa avaliação ampla de capacidade —, um SDK de produção, e a
observação recorrente em sistemas reais que caem nesse padrão de forma orgânica) convergem no
mesmo princípio — o que fortalece bastante o argumento a favor dele numa decisão de arquitetura
ou numa justificativa técnica escrita.

## Como aplicar

1. **Identifique as regras duras do seu sistema** — o que NUNCA pode acontecer, independente do
   que o LLM "decidir" (ex.: nunca executar uma query que não seja leitura, nunca ultrapassar um
   limite de segurança conhecido, nunca misturar dados de fontes incompatíveis).
2. **Para cada regra dura, pergunte: isso é verificável por código puro?** Se sim, implemente
   como checagem determinística ANTES de qualquer chamada cara de LLM — barato, rápido, e sem
   ambiguidade. Não delegue essa checagem a um prompt, mesmo que pareça mais simples de escrever.
3. **Para julgamentos que exigem entendimento de linguagem/contexto** (não uma regra dura
   binária), considere um segundo agente separado do gerador, cujo único trabalho é avaliar a
   saída do primeiro — não peça ao mesmo agente para gerar e se auto-avaliar na mesma chamada.
4. **Dê precedência à camada determinística sobre o veredito do LLM** quando as duas discordarem
   — se uma regra fixa diz "isso é crítico" e o LLM diz "está tudo bem", a regra fixa vence. Um
   LLM pode discordar de uma leitura obviamente correta por razões que não têm relação com a
   regra em si.

## Nota sobre o debate mais amplo de "vale a pena ter múltiplos agentes"

Existe uma tensão pública e sem árbitro definido na literatura entre uma posição cética
("Don't Build Multi-Agents" — o argumento de que a maior parte dos casos não precisa de múltiplos
agentes e a complexidade extra raramente se paga) e uma posição mais favorável, defendida
publicamente por fornecedores de frameworks de orquestração multiagente como a LangChain. Esta
skill não toma partido nesse debate mais amplo — o padrão gerador-validador aqui documentado é
um caso específico e mais restrito (separar quem gera de quem checa uma regra), não um argumento
geral a favor de arquiteturas multiagente complexas. A regra prática de `padrao-react-
raciocinio-acao` e da disciplina experimental de projetos de pesquisa em agentes se aplica aqui
também: qualquer decisão de ir para múltiplos agentes deveria vir acompanhada de comparação
contra um baseline de agente único, a custo equivalente — não assumida como melhoria automática.

## Não fazer

- Não assuma que "o prompt já pede pra fazer certo" é suficiente para uma regra que realmente
  importa — trate isso como uma sugestão ao modelo, não como enforcement.
- Não implemente o segundo agente/validador como "mais uma etapa do mesmo prompt" — precisa ser
  uma chamada/processo separado para ter o efeito de crítica independente que a evidência mostra.
- Não pule a validação determinística achando que o segundo agente (LLM) já cobre o caso — LLM
  crítico ainda pode errar; regra determinística é o piso de segurança quando a regra é
  objetivamente verificável.
