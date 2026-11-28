---
name: diagnosticar-consumo-de-contexto
description: Mede, a partir do .jsonl bruto de uma sessão do Claude Code, onde o contexto foi gasto de verdade (tool calls por tipo, bytes de tool_result por ferramenta, arquivos relidos, reentradas em plan mode) e lista os padrões estruturais de interação que custam caro, cada um com o número medido ao lado. Use quando o usuário perguntar por que os tokens/contexto acabam rápido, pedir para investigar o consumo de uma sessão, ou quando o tema for "effort muito alto"/"sessão cara" sem medição real por trás.
---

# Diagnosticar consumo de contexto

## Por que medir em vez de advinhar

"Acabou o contexto rápido" tem causas muito diferentes — e a causa intuitiva (nível
de *effort*, modelo escolhido, tamanho de cada resposta) raramente é a real. Numa
sessão medida para construir esta skill (30 MB, 146 turnos reais de usuário), o
suspeito inicial era o *effort*; o achado real foi outro: **40 reentradas em plan
mode**, cada uma reimprimindo o plano inteiro de volta ao contexto. O usuário usava
`effort: low` e mesmo assim via o contexto esgotar rápido — o gasto estava no
**número de voltas estruturais**, não na profundidade de cada resposta.

Por isso o primeiro passo é sempre medir o transcript real da sessão, nunca inferir
do que "parece" ter acontecido.

## Passo 1 — rodar o script de diagnóstico

```bash
python3 scripts/analisar_transcript.py --ultima          # acha o .jsonl mais recente do projeto atual
python3 scripts/analisar_transcript.py <caminho.jsonl>    # ou aponte direto
```

O `.jsonl` de uma sessão do Claude Code vive em
`~/.claude/projects/<slug-do-diretório-do-projeto>/<session-id>.jsonl` — um arquivo
por sessão, podendo chegar a dezenas de MB numa sessão longa.

**Nunca abra o `.jsonl` com `cat`, `Read`, ou qualquer ferramenta que jogue o
conteúdo bruto de volta no contexto da conversa atual** — isso reproduziria
exatamente o problema que esta skill existe para diagnosticar (o arquivo é, por
definição, maior que qualquer orçamento razoável de contexto de uma sessão
produtiva). O script parseia e resume; só a saída resumida (tipicamente <100 linhas)
deve entrar no contexto.

O script reporta: contagem de tool calls por tipo, bytes de `tool_result` por
ferramenta (o que de fato ocupou contexto, não só quantas vezes foi chamada),
arquivos lidos mais de uma vez, prefixos de comando `Bash` repetidos, contagem de
turnos reais do usuário (excluindo notificações de tarefa em background e
system-reminders), e um alerta específico se `"Re-entering Plan Mode"` aparecer no
transcript.

## Passo 2 — padrões caros, cada um com o sinal que o denuncia

### Reentrada em plan mode no meio de trabalho já aprovado

**Sinal:** `grep -c "Re-entering Plan Mode" sessao.jsonl` > 0, ou o alerta do script.
Cada reentrada reimprime o `ExitPlanMode` inteiro de volta (na sessão medida: ~9,5k
caracteres por chamada, 208k no total só nisso).

Acontece quando um pedido no meio da execução *soa* como reabertura de decisão —
"hierarquize de novo", "e se fizéssemos diferente", até perguntas de status
formuladas de um jeito ambíguo. Se o plano já foi aprovado e está em execução, um
pedido de status ("como está?", "o que falta?") não deveria soar como pedido de
replanejamento. Evitar misturar uma pergunta informacional com qualquer frase que
pareça reabrir a estratégia já decidida.

### Re-leitura do mesmo arquivo sem o conteúdo ter mudado

**Sinal:** a lista "Arquivos lidos mais de uma vez" do script, com contagem alta para
um arquivo que ninguém editou entre as leituras (ex.: o plano foi lido 10x numa
sessão onde ele só foi editado 6x — 4 releituras não tinham motivo).

Reler faz sentido depois de editar o arquivo, ou depois de uma reentrada em plan mode
(ver item anterior — são sintomas do mesmo problema raiz, não dois problemas
distintos). Reler "só para confirmar" o que já está no contexto não.

### Re-validação sem fato novo (distinguir da validação legítima)

**Sinal:** o mesmo comando (ou variação mínima) repetido no `Bash`, mas aqui o número
sozinho não decide — importa o *resultado* de cada repetição.

Numa sessão real, um comando de demo rodou 3 vezes seguidas: isso não foi
desperdício, porque cada rodada expôs um bug real diferente (um zumbi de processo
não detectado, depois uma correção incompleta, só na terceira rodada o resultado
saiu limpo) — repetir foi o jeito certo de confirmar a correção. O oposto seria
repetir o mesmo comando sem ter mudado nada entre uma tentativa e outra, "só para ter
certeza" de um resultado que já veio determinístico. Antes de marcar uma repetição
como desperdício, perguntar: *a repetição anterior mudou alguma coisa que justifique
rodar de novo?*

### Pedido que mistura execução com pedido de explicação longa

**Sinal:** no transcript, uma resposta de assistente muito mais longa que as vizinhas,
logo após um turno de usuário que pede ação ("faça X") e também pede relato
("...e me explica tudo o que você fez em detalhe").

Separar os dois pedidos em turnos distintos deixa cada resposta do tamanho do que
foi de fato pedido, em vez de a resposta de execução já vir inflada com narrativa
que ninguém pediu ainda.

### Investigação por tentativa e erro quando o pedido já sabia o alvo

**Sinal:** uma sequência longa de `Bash` explorando (`grep`, `cat`, comandos de
diagnóstico) antes de chegar à ação real, quando o próprio pedido do usuário já
continha a pista do que checar.

Dar o resultado esperado junto do pedido ("valide que X funciona rodando Y") custa
menos que pedir para o agente descobrir sozinho o que validar — a descoberta em si
consome tool calls e seus resultados.

### Ruído de shell de baixo custo unitário, mas alto volume

**Sinal:** prefixos de comando `Bash` repetidos dezenas de vezes na lista do script —
na sessão medida, `cd /caminho/do/projeto` sozinho apareceu 358 vezes.

Cada ocorrência isolada é barata; o volume agregado não é. Preferir comandos com
caminho absoluto embutido a repetir `cd` antes de cada comando, e evitar `echo` de
separador decorativo entre blocos de investigação quando o resultado de cada comando
já se distingue sozinho.

## Passo 3 — reportar ao usuário com números, não com impressão

Ao final do diagnóstico, apresentar os achados na forma "sinal medido → padrão →
consequência", igual à tabela usada nesta skill — nunca como lista de conselhos
genéricos de prompt engineering desconectados do que a sessão realmente mostrou.
Se o script não encontrar nenhum padrão caro (poucas reentradas, poucas releituras,
repetições todas justificadas por mudança real), dizer isso também — a ausência de
padrão caro é também um resultado do diagnóstico, não um motivo para inventar um.
