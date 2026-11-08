---
name: proteger-credenciais
description: Auditoria de segurança antes de qualquer ação que possa expor credenciais ou chaves privadas — ler arquivos sensíveis, montar comandos de conexão, configurar clientes de banco de dados ou VPN. Carregue esta skill sempre que o usuário pedir para configurar DBeaver, pgAdmin, MySQL Workbench, WireGuard, SSH, ou qualquer cliente que precise de host/porta/usuário/senha.
---

# Proteger Credenciais

## Regra absoluta

**Nunca leia arquivos de credenciais.** Isso inclui qualquer ferramenta disponível: `Read`, `cat`, `Get-Content`, `Bash`, `PowerShell`, ou qualquer outra.

Se precisar de dados de conexão para ajudar o usuário, peça que ele abra o arquivo manualmente e informe **só o campo específico necessário** (ex.: "qual é o host?"), nunca o arquivo inteiro.

## Arquivos proibidos

Qualquer arquivo cujo nome contenha ou corresponda a:

| Padrão | Exemplos |
|---|---|
| `.env*` | `.env`, `.env.livemes`, `.env.local`, `.env.production` |
| `*.conf` | `yan_leite.conf`, `wg0.conf`, `my.cnf` |
| `*secret*` | `secrets.yaml`, `api_secret.txt` |
| `*credential*` | `credentials.json`, `aws_credentials` |
| `*password*` | `passwords.txt`, `db_password.env` |
| `*token*` | `token.txt`, `gh_token` |
| `*private*` | `private_key.pem`, `id_rsa` |
| `*segredos*` | `.segredos-locais` |
| `*.pem`, `*.key`, `*.p12`, `*.pfx` | Certificados e chaves criptográficas |

## Como ajudar sem ler o arquivo

### Configurar um cliente de banco (DBeaver, pgAdmin, etc.)

Peça ao usuário:
1. "Abra o arquivo `.env` (ou `.env.livemes`) no seu editor de texto."
2. "Me informe o valor de `HOST`, `PORT` e `DB` — não precisa me passar usuário nem senha, você preenche esses campos diretamente no cliente."

Depois mostre o passo a passo de configuração do cliente com `<HOST>`, `<PORT>`, `<DB>` como placeholders — o usuário substitui.

### Configurar VPN (WireGuard, OpenVPN)

Oriente o usuário a importar o arquivo `.conf` diretamente no cliente VPN, sem copiar o conteúdo para o chat.

### Testar conexão

Use comandos que não expõem credenciais:
```powershell
# Testar alcance de rede (não revela senha)
ping <HOST>
Test-NetConnection -ComputerName <HOST> -Port <PORT>
```

## Checklist antes de qualquer ação

Antes de executar qualquer comando de conexão ou configuração de cliente:

- [ ] O comando vai ler um arquivo `.env` ou similar? → **Não fazer. Pedir ao usuário.**
- [ ] O comando vai imprimir credenciais no terminal? → **Não fazer. Usar placeholders.**
- [ ] O usuário vai colar uma string de conexão com senha? → **Avisar para não fazer isso no chat.**
- [ ] A ação vai persistir credenciais em arquivo de histórico do shell? → **Avisar.**

## Por que esta regra existe

Credenciais lidas acidentalmente durante uma sessão de IA trafegam pela API do provedor — em contas pessoais sem Zero Data Retention, isso pode violar termos de confidencialidade de projetos com dados industriais sensíveis. A regra acima evita esse risco completamente.
