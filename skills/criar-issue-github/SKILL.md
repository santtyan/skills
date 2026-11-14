---
name: criar-issue-github
description: Cria e organiza issues no GitHub com hierarquia de sub-issues nativas (não checklist em markdown), labels por tipo de trabalho e redação fluida em português. Carregue esta skill sempre que o usuário pedir para criar uma issue, abrir uma issue-pai com sub-issues, dividir uma issue grande em partes, ou reorganizar/corrigir issues já existentes no GitHub.
---

# Criar Issue no GitHub

## Por que isso é uma skill e não só `gh issue create`

Issue bem escrita não é só "abrir e preencher título e corpo". O GitHub tem um recurso de **sub-issues nativas** (GA desde abril/2025) que substitui o antigo hábito de colar um checklist em markdown dentro do corpo da issue-pai. Usar o recurso certo evita duas fontes de verdade divergindo (ex.: fechar a sub-issue e esquecer de marcar o checkbox correspondente no pai).

## Passo 1 — decidir a hierarquia antes de criar qualquer issue

Pergunte: esse trabalho tem partes que precisam de dono, discussão e progresso próprios?

- **Sim** → cada parte é uma **sub-issue** (issue completa, com assignee, labels e estado dela).
- **Não**, é só uma lista de verificação sem necessidade de rastrear quem fez o quê → **checklist markdown comum** (`- [ ]`) dentro do corpo, sem criar issue para cada item.

Limites do recurso (confirmados na documentação oficial do GitHub, abril/2025):
- Até **100 sub-issues por issue-pai**.
- Até **8 níveis de aninhamento** (sub-issue pode ter suas próprias sub-issues).
- Cada sub-issue tem **um único pai** visível no cabeçalho ("Parent").
- O pai ganha automaticamente uma barra de progresso ("Sub-issue progress": X/Y issues completed) — não precisa mantê-la manualmente.

**Nunca duplique conteúdo entre pai e filhas.** Se a sub-issue já existe como issue separada, o corpo do pai não deve repetir a lista de tarefas dela em markdown — isso é exatamente o padrão que o GitHub está descontinuando (retirement de "tasklists" em favor de sub-issues, changelog de fev/2025). O corpo do pai contém só objetivo, contexto e critério de conclusão geral; a lista de sub-issues com progresso já aparece automaticamente na página da issue.

## Passo 2 — nomenclatura

- **Título da issue-pai**: descreve o resultado esperado / o objetivo maior, sem prefixo de etapa. Ex.: "Avaliação dos pipelines contra o gabarito de 54 pessoas".
- **Título de sub-issue**: comece com verbo de ação. Ex.: "Rodar e avaliar pipeline (Yan + Pedro) contra o gabarito", "Levantar bibliografia sobre X" — não "Levantamento bibliográfico" (nome de atividade, não ação). Isso facilita ver numa lista de issues o que falta fazer, de cardápio.
- Se a pesquisa/trabalho envolve mais de uma pessoa, inclua os nomes no título da sub-issue entre parênteses: "(Pessoa A + Pessoa B)".

## Passo 3 — corpo da issue, em português fluido

Evite o tom "gerado por IA": frases burocráticas demais, travessão em excesso, antítese "X, não Y" repetida, generalizações não verificadas ("quase sempre", "a maioria"). Escreva como alguém do time explicaria para outro colega: direto, com conectivos naturais, parágrafos curtos.

Estrutura recomendada (adapte, nem toda issue precisa de todas as seções):

```markdown
## Objetivo

<o que essa issue entrega e por quê, em 1-3 frases>

## Contexto

<só se houver algo não óbvio: por que isso surgiu, decisão anterior relevante>

## Responsáveis

<quem faz, e por quê — relevante quando a atribuição não é óbvia>

## Fluxo / Regras

<passos concretos ou critérios de aceite, numerados ou em lista>

## Entrega

<o que fica versionado/comentado ao final, mensurável>
```

Se a issue-pai tem sub-issues, termine com uma frase simples linkando-as por número (`#12`, `#16`), sem repetir o conteúdo delas.

## Passo 4 — labels

Labels organizam **tipo de trabalho**, não hierarquia (a hierarquia já é o recurso de sub-issues). Antes de criar uma label nova, confira se já existe uma equivalente:

```bash
gh label list --repo <owner>/<repo>
```

Se as labels padrão do GitHub (`bug`, `documentation`, `enhancement`, `question`...) não cobrem o tipo de trabalho, crie uma label específica e descritiva:

```bash
gh label create "pesquisa" --repo <owner>/<repo> --description "Levantamento teórico/bibliográfico, sem código de produção" --color "5319e7"
gh label create "pipeline" --repo <owner>/<repo> --description "Execução e avaliação de resultado contra um gabarito" --color "0e8a16"
```

Aplique a label em cada issue (pai e filhas podem ter labels diferentes — não há herança automática):

```bash
gh issue edit <numero> --repo <owner>/<repo> --add-label "pesquisa"
```

## Passo 5 — criar a issue-pai e as sub-issues via `gh` CLI

`gh issue create` não aceita direto um parâmetro de "pai" — a vinculação de sub-issue nativa é feita depois, via GraphQL (`addSubIssue`), porque a CLI ainda não tem um atalho de primeira classe para isso em todas as versões.

### 5.1 — criar a issue-pai

```bash
gh issue create --repo <owner>/<repo> \
  --title "<título do objetivo maior>" \
  --body-file corpo_pai.md \
  --assignee <login1>,<login2>
```

Guarde o número retornado (ex. `#12`).

### 5.2 — criar cada sub-issue normalmente

```bash
gh issue create --repo <owner>/<repo> \
  --title "<Verbo de ação: o que essa parte entrega>" \
  --body-file corpo_filha.md \
  --assignee <login>
```

### 5.3 — pegar os node IDs (GraphQL usa ID interno, não o número)

```bash
gh api graphql -f query='
query {
  repository(owner: "<owner>", name: "<repo>") {
    pai: issue(number: <numero_pai>) { id }
    filha: issue(number: <numero_filha>) { id }
  }
}'
```

### 5.4 — vincular como sub-issue nativa

```bash
gh api graphql -f query='
mutation($parentId: ID!, $subId: ID!) {
  addSubIssue(input: {issueId: $parentId, subIssueId: $subId}) {
    issue { number }
    subIssue { number }
  }
}' -f parentId="<ID da pai>" -f subId="<ID da filha>"
```

Repita 5.4 para cada sub-issue. Depois disso, a página da issue-pai no GitHub já mostra a seção "Sub-issues" com barra de progresso automática — não crie checklist manual repetindo isso no corpo.

## Passo 6 — ao corrigir uma issue já criada

Se um comentário ou corpo ficou errado (ex.: nome trocado, divisão de trabalho desatualizada):

- **Prefira editar** o corpo com `gh issue edit <numero> --body-file novo_corpo.md` em vez de postar um comentário "correção" por cima — mantém uma única fonte de verdade.
- Se o erro está em um **comentário antigo** (não no corpo) e ele pode confundir quem lê a timeline, delete-o com a API REST e poste um único comentário correto no lugar, em vez de acumular "correções sobre correções":
  ```bash
  gh api repos/<owner>/<repo>/issues/comments/<comment_id> -X DELETE
  ```
  Para achar o ID do comentário: `gh api repos/<owner>/<repo>/issues/<numero>/comments --jq '.[] | {id, body: .body[0:60]}'`.

## Checklist antes de considerar a issue pronta

- [ ] O corpo tem objetivo claro em 1-3 frases, sem jargão desnecessário?
- [ ] Sub-issues reais usam o recurso nativo (`addSubIssue`), não checklist markdown?
- [ ] Nenhum conteúdo está duplicado entre pai e filhas?
- [ ] Títulos de sub-issue começam com verbo de ação?
- [ ] Labels aplicadas refletem o tipo de trabalho, não a hierarquia?
- [ ] Assignees correspondem de fato às pessoas combinadas (confira nomes com o usuário se vierem de uma transcrição de áudio/WhatsApp — nomes parecidos trocam fácil)?
- [ ] A redação soa como uma pessoa do time escrevendo, não como texto genérico gerado por IA?
