# skills

Coleção pessoal de [skills do Claude Code](https://docs.claude.com/en/docs/claude-code/skills) — instruções empacotadas que o Claude carrega para tarefas recorrentes específicas, em vez de reconstruir a abordagem do zero a cada conversa.

## Como usar

Cada skill vive em `skills/<nome>/` com um `SKILL.md` (frontmatter `name` + `description`, seguido das instruções) e, quando aplicável, scripts auxiliares em `skills/<nome>/scripts/`.

Para usar num projeto: copie a pasta da skill para `.claude/skills/<nome>/` dentro do repositório onde você quer usá-la. O Claude Code carrega skills automaticamente a partir dessa pasta e as invoca quando a tarefa combina com a `description`, ou quando chamada explicitamente (`/nome-da-skill`).

## Skills disponíveis

| Skill | O que faz |
|---|---|
| [`revisao-critica-relatorio`](skills/revisao-critica-relatorio/) | Revisão crítica linha-por-linha de relatórios científicos e textos técnicos: detector determinístico de traços de escrita por IA (travessão, antítese, adjetivo vazio, conectivo clichê, densidade de parágrafo), rigor de gramático sênior em português, validação de cadeia lógica premissa→evidência→conclusão e falácias comuns, e um passo de reescrita para fluidez narrativa extrema. |

## Licença

MIT — use, copie, adapte.
