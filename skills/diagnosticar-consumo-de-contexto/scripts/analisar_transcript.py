#!/usr/bin/env python3
"""Mede onde uma sessão do Claude Code gastou contexto, a partir do .jsonl bruto.

Uso:
    python3 analisar_transcript.py <caminho/para/sessao.jsonl>
    python3 analisar_transcript.py --ultima   # acha o .jsonl mais recente do projeto atual

Não depende de nada além da stdlib — roda em qualquer máquina sem pip install.
"""
import collections
import glob
import json
import os
import sys


def achar_jsonl_mais_recente():
    """Localiza o .jsonl mais recente do projeto atual em ~/.claude/projects/."""
    cwd = os.path.abspath(os.getcwd())
    slug = cwd.replace("/", "-")
    base = os.path.expanduser("~/.claude/projects")
    candidatos = glob.glob(os.path.join(base, f"{slug}*", "*.jsonl"))
    if not candidatos:
        candidatos = glob.glob(os.path.join(base, "*", "*.jsonl"))
    if not candidatos:
        return None
    return max(candidatos, key=os.path.getmtime)


def analisar(caminho):
    tool_counts = collections.Counter()
    tool_use_ids = {}
    tool_result_bytes = collections.Counter()
    tool_result_calls = collections.Counter()
    read_files = collections.Counter()
    bash_prefixes = collections.Counter()
    reentradas_plan_mode = 0
    turnos_reais = 0
    n_linhas = 0
    tamanho_total = 0

    with open(caminho) as f:
        for linha in f:
            n_linhas += 1
            tamanho_total += len(linha)
            if "Re-entering Plan Mode" in linha:
                reentradas_plan_mode += 1
            try:
                d = json.loads(linha)
            except json.JSONDecodeError:
                continue

            if d.get("type") == "user":
                msg = d.get("message", {})
                content = msg.get("content")
                texto = ""
                if isinstance(content, str):
                    texto = content
                elif isinstance(content, list):
                    texto = " ".join(
                        b.get("text", "") for b in content
                        if isinstance(b, dict) and b.get("type") == "text"
                    )
                t = texto.strip()
                if t and "SYSTEM NOTIFICATION" not in t and not t.startswith("<system-reminder>"):
                    turnos_reais += 1

            content = d.get("message", {}).get("content")
            if not isinstance(content, list):
                continue
            for bloco in content:
                if not isinstance(bloco, dict):
                    continue
                tipo = bloco.get("type")
                if tipo == "tool_use":
                    nome = bloco.get("name", "?")
                    tool_counts[nome] += 1
                    tool_use_ids[bloco.get("id")] = nome
                    if nome == "Bash":
                        cmd = bloco.get("input", {}).get("command", "")
                        prefixo = cmd.strip().splitlines()[0][:60] if cmd.strip() else ""
                        bash_prefixes[prefixo] += 1
                    elif nome == "Read":
                        read_files[bloco.get("input", {}).get("file_path", "?")] += 1
                elif tipo == "tool_result":
                    tuid = bloco.get("tool_use_id")
                    nome = tool_use_ids.get(tuid, "?")
                    c = bloco.get("content")
                    tam = 0
                    if isinstance(c, list):
                        for cc in c:
                            if isinstance(cc, dict) and cc.get("type") == "text":
                                tam += len(cc.get("text", ""))
                    elif isinstance(c, str):
                        tam = len(c)
                    tool_result_bytes[nome] += tam
                    tool_result_calls[nome] += 1

    print(f"Transcript: {caminho}")
    print(f"  {n_linhas} linhas, {tamanho_total / 1e6:.1f} MB")
    print(f"  {turnos_reais} turnos reais do usuário (excluindo system-reminder/notificação)")
    print()

    if reentradas_plan_mode:
        print(f"⚠️  'Re-entering Plan Mode' apareceu {reentradas_plan_mode}x — cada reentrada "
              "reimprime o plano inteiro de volta no contexto. Ver seção 'Reentrada em plan mode' "
              "no SKILL.md desta skill.")
        print()

    print("=== Tool calls por tipo (contagem) ===")
    for nome, n in tool_counts.most_common(15):
        print(f"  {nome}: {n}")
    print()

    print("=== Bytes de tool_result por ferramenta (o que de fato ocupou contexto) ===")
    for nome, b in tool_result_bytes.most_common(15):
        n = tool_result_calls[nome]
        print(f"  {nome}: {b / 1e3:.0f}k chars em {n} calls (média {b / max(n, 1) / 1e3:.1f}k/call)")
    print()

    repetidos = [(f, n) for f, n in read_files.most_common(20) if n > 1]
    if repetidos:
        print("=== Arquivos lidos mais de uma vez (Read) ===")
        for f, n in repetidos:
            print(f"  {n}x  {f}")
        print()

    cmds_repetidos = [(c, n) for c, n in bash_prefixes.most_common(20) if n > 1]
    if cmds_repetidos:
        print("=== Prefixos de comando Bash repetidos ===")
        for c, n in cmds_repetidos:
            print(f"  {n}x  {c}")


def main():
    args = sys.argv[1:]
    if args and args[0] == "--ultima":
        caminho = achar_jsonl_mais_recente()
        if not caminho:
            print("Nenhum .jsonl encontrado em ~/.claude/projects/.", file=sys.stderr)
            sys.exit(1)
    elif args:
        caminho = args[0]
    else:
        print(__doc__)
        sys.exit(2)

    analisar(caminho)


if __name__ == "__main__":
    main()
