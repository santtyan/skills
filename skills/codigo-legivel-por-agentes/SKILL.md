---
name: codigo-legivel-por-agentes
description: Reordena e aplica as práticas de Clean Code priorizando o leitor primário de código em 2026 — o agente de IA, não mais só o humano — com critério objetivo e mensurável (tamanho de arquivo/função, densidade de comentário útil vs. ruído, grepabilidade de nomes) em vez de opinião de estilo. Use quando o usuário pedir para "deixar o código melhor pra IA trabalhar", "revisar legibilidade pra agente", "por que o agente tá gastando muito token nesse arquivo", "organizar pra Claude Code entender melhor", ou ao escrever/revisar um CLAUDE.md/AGENTS.md novo. Baseado no artigo "Clean Code pra Agentes de IA" (Fabio Akita, 2026-04-20).
---

# Código legível por agentes

Uncle Bob escreveu Clean Code (2008) para um leitor humano sentado no editor. Em 2026, o leitor
primário de boa parte do código passou a ser um agente de IA navegando, editando e estendendo via
tool calls. A maioria das práticas do livro continua valendo — algumas ficaram **mais** críticas,
porque agora têm métrica objetiva (custo de token, taxa de truncamento, precisão de retrieval por
grep) em vez de só opinião de estilo. Esta skill reordena essas práticas por relevância para
agente e dá o critério mensurável de cada uma, não uma lista de bons conselhos.

## Por que a ordem muda: as restrições reais do agente

Antes de aplicar qualquer critério, tenha em mente o que de fato limita um agente trabalhando em
um repositório — isso é a justificativa de cada item abaixo, não decoração:

- **Truncamento de leitura**: a maioria das CLIs de agente lê arquivo em faixas (ex. 2000 linhas
  por vez). Arquivo grande não entra inteiro numa única tool call.
- **Atenção degrada com contexto**: mesmo em janelas de 200k-1M tokens, a precisão de recuperação
  de detalhe cai bem antes do limite declarado, e o contexto do agente já está disputado por
  system prompt, CLAUDE.md, histórico, saída de tool e log de erro.
- **Grep é mais barato que read**: agentes preferem buscar por nome a carregar arquivo inteiro —
  isso não é atalho, é arquitetura madura (busca lexical + leitor inteligente bate retriever
  denso + top-k na maioria dos benchmarks de código real). Nomes grepáveis são a API primária de
  navegação do agente, não só estética para humano.
- **Cada tool call custa token e latência**: arquivo curto, output de teste enxuto e log
  estruturado mantêm o agente produtivo e a sessão barata.

## Ordem de prioridade (da mais crítica pra menos)

Não é que os itens de baixo deixaram de importar — é que os de cima passaram a importar muito
mais, com métrica objetiva por trás.

### 1. Funções e arquivos pequenos

Critério mensurável, não opinião: função de 4-20 linhas cabe numa tool call sem truncamento;
arquivo abaixo de 500 linhas (idealmente 200-300) cabe numa leitura única. Se o agente pega a
unidade inteira de sentido numa chamada, ele raciocina com atenção cheia; se precisa paginar, o
modelo mental dele fica fragmentado e cada fragmento custa atenção.

### 2. Single Responsibility Principle

Módulo com responsabilidades embaralhadas força o agente a carregar muito mais contexto para
qualquer mudança simples. Uma classe de 800 linhas fazendo três coisas é pior para o agente do
que três classes de 250 linhas com o mesmo total — porque o agente consegue isolar, testar e
editar cada responsabilidade sem carregar o resto do sistema.

### 3. Nomes significativos e grepáveis

"Pesquisável" é a propriedade mais importante da lista clássica de Uncle Bob no contexto de
agente. Regra prática, aplicável em qualquer revisão: **grep o nome candidato antes de aceitar**.
Nome genérico (`data`, `handler`, `Manager`, `process`) retorna dezenas de matches irrelevantes e
obriga o agente a ler cada um; nome distintivo (`UserRegistrationValidator`,
`ClaudeCodeSessionTracker`) retorna só o que importa. Se o grep vem sujo, o nome está ruim para
agente, mesmo que pareça claro para humano.

### 4. Comentários com contexto e proveniência — a maior inversão da lista

Em 2008, comentário em excesso era code smell — código bem nomeado não precisaria dele. Em 2026,
o agente lê fluentemente sintaxe (não precisa de legenda óbvia — isso continua ruim, ver item 13)
mas **não sabe por que** uma abordagem não-óbvia foi escolhida, qual bug de produção motivou uma
lógica estranha, qual constraint de negócio força uma ordem específica, ou qual workaround existe
por causa de um bug conhecido numa lib. Essa informação — proveniência da decisão — só existe na
cabeça do humano, na mensagem de commit, ou num comentário bem colocado; para o agente, o
comentário é a fonte mais acessível durante uma tool call.

**Regra prática de revisão de PR/commit**: nunca remova um comentário que documenta o *porquê* de
uma decisão só por parecer verboso — isso é contexto que o próprio agente (ou o próximo) vai
precisar ler. O único tipo de comentário a cortar é o que descreve o óbvio (item 13).

### 5. Tipos explícitos

Não estava no livro de 2008 porque a indústria ainda não tinha convertido em massa. Em 2026,
código dinâmico sem anotação de tipo obriga o agente a inferir tipo por uso (custa raciocínio,
erra com frequência); assinatura tipada é gabarito imediato de entrada/saída/estados válidos. Se
o projeto está em Python sem type hints, JS sem TS, ou Ruby sem RBS, essa é geralmente a
transição de maior retorno de produtividade de agente — maior que qualquer refactor de lógica.

### 6. DRY

Duplicação é pior para agente do que para humano por uma razão específica: a janela de atenção
do agente não tem "gravidade" natural que lembre "tem mais duas cópias disso em outro arquivo" —
ele só acha cada cópia via grep, e se houver variação sutil entre elas, o resultado de uma edição
fica inconsistente. Fatorar em função/módulo reutilizável é segurança de refactor automatizado,
não estética.

### 7. Testes que o agente consegue rodar sem setup humano

F.I.R.S.T continua valendo (Fast, Independent, Repeatable, Self-Validating, Timely), com um
adendo: comando de teste documentado (README/CLAUDE.md/Makefile/package.json), output em formato
parseável, sem dependência de seed manual de banco ou credencial fora do repo. Esse é o ciclo
básico do agente: escreve código → roda teste → lê output → ajusta → roda de novo. Se o teste não
roda headless, o agente fica cego e não consegue validar a própria mudança.

### 8. Estrutura de diretório previsível

Convenção forte de framework (ou pelo menos interna e consistente) deixa o agente antecipar paths
sem listar diretório. Projeto sem convenção faz o agente gastar tokens explorando com `find`/`ls`
repetidamente.

### 9. Dependency Injection e testabilidade

Dependência injetada (não hardcoded) permite o agente substituir por fake/mock em teste sem tocar
a lógica. Código que instancia suas próprias dependências internamente obriga o agente a
gambiarra de monkey-patch, lento e frágil.

### 10. Evitar aninhamento profundo

Cada nível de indentação é atenção adicional que o modelo gasta rastreando estado. `if` dentro de
`for` dentro de `if` dentro de `try` é caro para agente rastrear; early return e guard clause
achatam a lógica.

### 11. Mensagem de erro com contexto

`raise ValueError("invalid input")` não ajuda o agente lendo o stack trace; incluir o valor
recebido e o formato esperado sim — mensagem vaga custa uma rodada extra de investigação.

### 12. Formatação automática

Não perca tempo discutindo estilo — use o formatador padrão da linguagem (`black`/`ruff`,
`prettier`, `gofmt`, `cargo fmt`, `rubocop -A`) via pre-commit/hook de save. Diff limpo entre
commits importa mais para o agente que preferência pessoal de chaves/indentação.

## O que o Uncle Bob de 2008 não podia antever

- **Arquivos de meta-instrução para agente** (`CLAUDE.md`, `AGENTS.md`, `.cursor/rules`): lidos
  antes de qualquer tool call, então densidade importa — bulletpoint direto e imperativo, não
  prosa. Um bloco de ~100 linhas custa ~500 tokens por iteração; a economia em qualidade de
  código e ausência de retrabalho compensa isso facilmente.
- **README com arquitetura de alto nível** (diagrama simples, ASCII ou Mermaid) encurta o caminho
  do agente para entender o formato do projeto.
- **Logging estruturado** (JSON com campos nomeados) é parseável trivialmente pelo agente para
  filtrar erro relevante e correlacionar entre serviços; texto livre exige parsing heurístico.
- **Scripts de setup idempotentes** (`bin/setup`, `scripts/bootstrap.sh`) que rodam numa máquina
  limpa até um estado utilizável — se o onboarding depende de instrução na cabeça de um humano, o
  agente fica de fora.

## Não fazer

- Não assuma que o agente vai aplicar essas práticas por conta própria sem instrução explícita no
  CLAUDE.md/AGENTS.md — nenhum LLM faz DI, DRY rigoroso, tipos explícitos em todo lugar ou nomes
  agressivamente únicos por default; ele implementa o caminho médio a menos que seja instruído.
- Não remova comentários de proveniência (item 4) durante refactor só por parecerem longos —
  confirme primeiro se documentam um *porquê*, não um *o quê* óbvio, antes de cortar.
- Não trate "arquivo grande" como problema estético — meça: se passa de ~500 linhas ou obriga o
  agente a paginar a leitura, é candidato real a split, não questão de gosto.
- Não discuta formatação/estilo manualmente — delegue ao formatador automático da linguagem.
- Não escreva CLAUDE.md/AGENTS.md em prosa longa — cada linha é lida (e paga em token) a cada
  iteração; prefira bulletpoint imperativo.

## Checklist final de aceitação

- Arquivos e funções revisados contra os limites objetivos (função 4-20 linhas, arquivo <500
  linhas) — não só "parece grande", mas medido.
- Nomes candidatos passaram pelo teste de grep (poucos hits relevantes, não dezenas de ruído).
- Comentários de proveniência ("por que essa decisão", não "o que essa linha faz") preservados;
  comentários redundantes com o código removidos.
- Tipos explícitos presentes em assinaturas públicas, se a linguagem suportar.
- Comando de teste documentado e executável sem setup manual.
- CLAUDE.md/AGENTS.md (se existir) está em formato imperativo/bulletpoint, não prosa.
