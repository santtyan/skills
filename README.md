# skills

Coleção pessoal de [skills do Claude Code](https://docs.claude.com/en/docs/claude-code/skills) — instruções empacotadas que o Claude carrega para tarefas recorrentes específicas, em vez de reconstruir a abordagem do zero a cada conversa.

## Como usar

Cada skill vive em `skills/<nome>/` com um `SKILL.md` (frontmatter `name` + `description`, seguido das instruções) e, quando aplicável, scripts auxiliares em `skills/<nome>/scripts/`.

Para usar num projeto: copie a pasta da skill para `.claude/skills/<nome>/` dentro do repositório onde você quer usá-la. O Claude Code carrega skills automaticamente a partir dessa pasta e as invoca quando a tarefa combina com a `description`, ou quando chamada explicitamente (`/nome-da-skill`).

## Skills disponíveis

| Skill | O que faz |
|---|---|
| [`revisao-critica-relatorio`](skills/revisao-critica-relatorio/) | Revisão crítica linha-por-linha de relatórios científicos e textos técnicos: detector determinístico de traços de escrita por IA (travessão, antítese, adjetivo vazio, conectivo clichê, densidade de parágrafo), rigor de gramático sênior em português, validação de cadeia lógica premissa→evidência→conclusão e falácias comuns, e um passo de reescrita para fluidez narrativa extrema. |
| [`refatorar-organizar-repositorio`](skills/refatorar-organizar-repositorio/) | Audita um repositório inteiro em busca de dívida técnica estrutural (arquivos órfãos, lógica duplicada entre módulos, nomenclatura inconsistente, organização de pastas confusa, dependências não usadas), prioriza os achados por impacto x custo e aplica refatoração com comportamento preservado, em mudanças pequenas e reversíveis com baseline recuperável. |
| [`auditar-scripts-orfaos`](skills/auditar-scripts-orfaos/) | Classifica cada script standalone (com ponto de entrada de execução direta) de um repositório em útil, órfão, arquivado intencionalmente ou setup one-shot, cruzando evidência de chamada real (import, subprocess, comando documentado) com sinais de auto-abandono no próprio código (docstring desatualizado, paths hardcoded de máquina específica). Não remove nada sozinha — entrega o diagnóstico para decisão humana. |
| [`revisar-funcoes-orfas`](skills/revisar-funcoes-orfas/) | Revisa um arquivo ou pasta indicado pelo usuário linha por linha em busca de funções/métodos sem nenhuma chamada, cuidando de três fontes conhecidas de falso positivo: despacho por dicionário, métodos homônimos entre classes distintas, e underscore importado cross-file. Nunca remove sozinha — exige confirmação função por função. |
| [`migrar-para-langchain`](skills/migrar-para-langchain/) | Guia de risco por tipo de módulo (retrieval, self-repair, roteamento com regra de negócio, validação de segurança) para migrar sistemas de IA para LangChain/LangGraph, com regra de não regressão e critério de quando migrar mesmo sem ganho isolado de qualidade. |
| [`roadmap-rag-survey`](skills/roadmap-rag-survey/) | Autodiagnóstico Naive/Advanced/Modular RAG baseado no survey de Gao et al. (arXiv:2312.10997), template de tabela de gap, e síntese de pesquisa 2025-2026 sobre query rewrite, RRF, reranking e context compression, com evidência a favor e contra cada técnica. |
| [`rag-multimodal`](skills/rag-multimodal/) | Checklist para adicionar RAG multimodal (texto+imagem) a um projeto: decisão de arquitetura caption-then-embed vs. CLIP, tabela de VLMs locais por hardware, e pegadinhas de ambiente conhecidas (Ollama + PyTorch no mesmo processo). |
| [`slides-beamer-decisao-tecnica`](skills/slides-beamer-decisao-tecnica/) | Gera slides Beamer (.tex, Overleaf) narrando qualquer decisão técnica em 3 batidas — o que medimos, o que significou, o que decidimos — com números reais, nunca estimados. |
| [`padrao-gerador-validador`](skills/padrao-gerador-validador/) | Guia de quando separar quem gera de quem valida em sistemas com LLM (nunca confiar em instrução de prompt para impor regra dura), com evidência quantitativa do paper AutoGen e do OpenAI Agents SDK. |
| [`memoria-longo-prazo-agentes`](skills/memoria-longo-prazo-agentes/) | Arquitetura de memória de longo prazo por usuário em agentes com LLM: distingue memória de histórico de conversa e session state, apresenta memory stream → reflection → planning (Generative Agents) e a paginação hierárquica MemGPT (ambas validadas empiricamente), e as armadilhas mais comuns de retrieval e memória fabricada. |
| [`tool-calling-multiframework`](skills/tool-calling-multiframework/) | Boas práticas de design de tool/function calling através de provedores (OpenAI, Anthropic) e frameworks de agente: schema e strict mode, deferred loading para catálogos grandes, client vs. server tools. |
| [`observability-llm-opentelemetry`](skills/observability-llm-opentelemetry/) | Guia de quando/como instrumentar um pipeline de LLM com OpenTelemetry como alternativa vendor-neutral e self-hosted a plataformas proprietárias de observability. |
| [`padrao-react-raciocinio-acao`](skills/padrao-react-raciocinio-acao/) | O paradigma ReAct (raciocínio e ação intercalados) para reduzir alucinação e melhorar tarefas de decisão, com evidência quantitativa do paper original (Yao et al., ICLR 2023). |
| [`esquema-de-trace-agentes`](skills/esquema-de-trace-agentes/) | Padrão-ouro para desenhar o esquema de trace de um agente com LLM: quando OpenTelemetry GenAI basta e quando falta a camada semântica de proveniência entre passos, e como estruturar um trace JSONL portável entre frameworks. |
| [`replicacao-experimento-agente`](skills/replicacao-experimento-agente/) | Protocolo de replicação de experimentos com agente: os três artefatos obrigatórios (código, trace, relatório), record-replay de chamadas externas, pin de versão, ablação por flag, e a regra de baseline justo entre agente único e multiagente. |

## Licença

MIT — use, copie, adapte.
