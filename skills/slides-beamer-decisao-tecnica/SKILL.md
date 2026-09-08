---
name: slides-beamer-decisao-tecnica
description: Gera/atualiza slides Beamer (.tex, para colar no Overleaf) narrando qualquer decisão técnica em 3 batidas (o que medimos → o que significou → o que decidimos), com tabelas de números reais em vez de estimativas. Use quando o usuário pedir para "preparar isso pro Overleaf", "fazer slide de uma comparação técnica", "documentar essa decisão em slide", ou "gerar apresentação de uma migração/experimento".
---

# Slides Beamer — narrativa de decisão técnica

## Formato: Beamer (.tex) para Overleaf, não Markdown

Esta skill produz **LaTeX/Beamer** — o usuário monta a apresentação no Overleaf, não em outro
formato. Saída: um arquivo `.tex` (documento Beamer completo, com `\documentclass{beamer}` por
conta própria — não é um trecho para colar dentro de outro arquivo, a menos que o usuário já
tenha um projeto Overleaf e peça para anexar frames a ele).

Usar `references/tema_neutro.sty` como ponto de partida de tema — trocar as cores por um tema
próprio se o usuário tiver identidade visual definida (é só um placeholder neutro azul/cinza) —
e seguir a estrutura de `references/exemplo_frame_comparacao.tex` como modelo de frame: reler
os dois antes de gerar/atualizar o `.tex`, não reinventar o estilo a cada vez.

## Princípio central: narrativa, não só tabela

Cada decisão técnica vira um **frame com 3 batidas**, nessa ordem (ver exemplo em
`references/exemplo_frame_comparacao.tex`):

1. **O que medimos** — a tabela de números reais (antes x depois, ou opção A x opção B), num
   bloco de destaque visual. Nunca um número estimado ou "deveria melhorar" — só o que a
   medição/experimento realmente produziu, com a fonte (script + data) anotada.
2. **O que isso significou** — 1-2 frases interpretando o número: o ganho veio de quê
   especificamente? regrediu ou não? Isso é o que transforma uma tabela fria em argumento.
3. **O que decidimos** — bloco de alerta/decisão com a escolha tomada e a razão. Se a decisão
   foi "não mudar" (número não justificou a mudança), isso também é decisão narrável, não um
   item para omitir. Se foi "mudar mesmo sem ganho isolado" por outra razão (ex.: consistência
   arquitetural com algo planejado), essa razão TEM que aparecer explicitamente no frame — é a
   parte que mais defende a decisão numa arguição.

Isso é o oposto de um slide de changelog ("fizemos X, resultado Y") — a narrativa é sobre o
**raciocínio de engenharia**: medir antes de decidir, e decidir com base no que foi medido (ou
declarar explicitamente quando a decisão pesou outro critério além do número).

## Passo 1 — Obter o estado e os números atuais

Nunca escrever a partir de memória:

1. Reler a fonte de verdade da decisão (documento de roadmap, relatório de experimento,
   changelog do projeto) — checklist de progresso e a razão registrada de cada decisão já
   tomada.
2. Para cada decisão já avaliada, pegar os números reais do relatório/commit daquela
   comparação — não reconstruir números de memória.
3. Se algo está "em progresso", registrar como tal no slide, com o que já se sabe até agora —
   não inventar números finais antes de existirem.

## Passo 2 — Estrutura do documento Beamer

```latex
\documentclass{beamer}
\usepackage[utf8]{inputenc}
\usepackage[brazilian]{babel}
\usepackage{booktabs}
\usepackage{xcolor}
\input{tema_neutro}  % ou colar o conteúdo de references/tema_neutro.sty direto aqui

\title{Título da decisão/processo}
\subtitle{Progresso, comparações e decisões}
\author{Seu Nome}
\date{\today}

\begin{document}

\frame{\titlepage}

\begin{frame}{Por que essa mudança}
  % 2-3 bullets: motivação real, não um argumento genérico sem evidência
\end{frame}

\begin{frame}{Ordem/plano (se houver múltiplas etapas)}
  % lista as etapas planejadas, com um ícone/cor indicando status:
  % feito / avaliado-e-recusado / não iniciado
\end{frame}

% -- um frame de 3 batidas (bloco de medição / bloco de decisão) por decisão já avaliada --

\begin{frame}{Próximos passos}
  % próxima etapa não concluída do plano
\end{frame}

\end{document}
```

## Passo 3 — Conferir consistência

- Os números em cada frame devem bater com a fonte real daquela medição — se não bater, o
  slide está na frente da realidade; corrigir o slide, não inventar um número intermediário.
- Uma etapa só aparece como "concluída" no frame de status se a fonte de verdade do projeto já
  registrar isso como concluído — os dois lugares devem concordar.
- Se uma mudança regrediu e foi revertida, isso também vira um frame (3 batidas: medimos →
  regrediu → revertemos e ficamos com X) — é dado real do processo, mais forte numa
  apresentação do que só mostrar sucessos.

## Não fazer

- Não gerar PPTX/HTML — a saída é sempre `.tex` Beamer; se o usuário quiser outro formato,
  perguntar antes de trocar.
- Não anunciar algo como "pronto para produção" no slide antes do critério de aceite real ter
  sido cumprido (medição sem regressão, ou decisão explícita registrada por escrito em algum
  lugar do projeto).
- Não misturar com outros documentos de assunto diferente — um arquivo Beamer por assunto.
