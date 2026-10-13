---
name: tema-cerise-pptx
description: Aplica o tema visual institucional do grupo CERISE (Centro de Excelência em Redes Inteligentes Sem Fio e Serviços Avançados - UFG) a um deck PowerPoint (.pptx) gerado via pptxgenjs. Já traz prontos os logos (Cerise, FAPEG), a cor exata do título (azul 0033CC) e o padrão de layout (capa com fundo de rede clareado, slides de conteúdo com logo Cerise no canto superior direito e FAPEG no rodapé esquerdo) extraídos e validados a partir de apresentações reais do grupo. Use sempre que o usuário pedir para fazer um slide/apresentação/deck "no padrão do Cerise", "como as apresentações do grupo", "estilo HarboR/FAPEG/UFG", ou mencionar o grupo de pesquisa CERISE em qualquer contexto de criação de PowerPoint. Não re-extrai nada de um .pptx de referência: os assets já estão prontos para uso direto.
---

# Tema institucional CERISE para PowerPoint

Esta skill aplica, a um deck novo gerado com `pptxgenjs`, o padrão visual que se repete nas
apresentações reais do grupo CERISE (confirmado comparando o compilado geral do grupo, a
apresentação de Yan Santos e a apresentação de Carlos Daniel): fundo branco, título em azul
institucional, logo Cerise no canto superior direito dos slides de conteúdo, logo FAPEG no
rodapé esquerdo, e uma capa com o logo grande sobre o fundo de rede/malha característico.

Carregue primeiro a skill `pptx` (built-in) para a API do `pptxgenjs` e os cuidados gerais de
geração — esta skill cobre só o que é específico do tema CERISE, não repete o conteúdo da `pptx`.

## Por que os valores abaixo são fixos, não exemplos

Cada valor numérico e cada asset aqui vieram de medição direta em apresentações reais do grupo,
não de estimativa visual. A cor do título foi lida do XML do slide (`grep srgbClr`), não
"parece azul". Os logos foram identificados por um grid de thumbnails comparando as imagens
brutas do pacote `.pptx`, não adivinhados pelo nome do arquivo. Use os valores como estão; se
precisar ajustar, prefira medir de novo uma apresentação real do grupo a estimar visualmente.

## Assets prontos (pasta `assets/` desta skill)

| Arquivo | Uso |
|---|---|
| `logo_cerise.png` | Logo Cerise pequeno (464×141), para o canto superior direito dos slides de conteúdo |
| `logo_cerise_grande.png` | Logo Cerise grande (1114×301), para a capa |
| `logo_fapeg.png` | Logo FAPEG (294×60), para o rodapé esquerdo |
| `capa_fundo_rede_clara.png` | Textura de rede/malha já clareada (ver "Por que a imagem já vem clareada" abaixo), para o fundo da capa |

Copie esses quatro arquivos para a pasta `assets/` do projeto onde o deck está sendo gerado
(`pptxgenjs` referencia arquivos locais, não paths fora do diretório de trabalho do script).

## Paleta e tipografia

```js
const THEME_CERISE = {
  headFontFace: "Calibri",
  bodyFontFace: "Calibri",
  colors: {
    dk2: "0033CC",   // azul do título — lido direto do XML do slide, não estimado
    lt2: "FFFFFF",   // fundo branco puro — o grupo não usa fundo cinza/cream
    accent5: "6B7280", // cinza para texto secundário e legendas
  },
};
```

O verde/âmbar/vermelho de indicadores de status (ex. "replicado"/"pendente"/"bloqueado") e o
azul institucional (`accent4`, para destaques neutros tipo bullets ou ícones) não são parte do
tema do grupo — são convenção própria de quem monta o deck. Mantenha-os como cores à parte,
nunca substituindo o `dk2` institucional.

## Master de capa

```js
pres.defineSlideMaster({
  title: "CAPA",
  background: { color: "FFFFFF" },
  objects: [
    { image: { path: "assets/capa_fundo_rede_clara.png", x: 0, y: 0, w: 13.333, h: 7.5 } },
    { image: { path: "assets/logo_cerise_grande.png", x: 0.9, y: 1.05, w: 6.3, h: 1.7 } },
    { placeholder: { options: { name: "title", type: "title", x: 0.9, y: 4.15, w: 11.5, h: 0.9,
        fontFace: THEME_CERISE.headFontFace, fontSize: 26, bold: true, color: THEME_CERISE.colors.dk2,
        align: "left" }, text: "" } },
    { placeholder: { options: { name: "subtitle", type: "body", x: 0.9, y: 4.95, w: 11.5, h: 0.6,
        fontFace: THEME_CERISE.bodyFontFace, fontSize: 15, color: THEME_CERISE.colors.accent5,
        align: "left" }, text: "" } },
    { placeholder: { options: { name: "meta", type: "body", x: 0.9, y: 6.7, w: 11.5, h: 0.4,
        fontFace: THEME_CERISE.bodyFontFace, fontSize: 11, color: THEME_CERISE.colors.accent5,
        align: "left" }, text: "" } },
  ],
});
```

**Por que o logo fica em `y: 1.05` e o título em `y: 4.15`, não mais próximos**: o logo grande
tem 1,7" de altura; qualquer título abaixo de `y: 4.0` evita sobrepor o texto "CENTRO DE
EXCELÊNCIA..." que vem embutido na própria imagem do logo. Testado visualmente — aproximar essas
posições faz o texto colidir com o logo.

### Por que a imagem de fundo já vem clareada

A textura de rede/malha, extraída crua do pacote `.pptx` original, é escura (tom verde-azulado
saturado) — não é o fundo que aparece de fato na capa real das apresentações do grupo. A capa
real usa essa mesma textura com um efeito de clareamento por cima. `capa_fundo_rede_clara.png`
já tem esse efeito aplicado (composição com camada branca a ~75% de opacidade via
`PIL.Image.alpha_composite`). Use sempre essa versão clareada, nunca a textura crua — a crua
deixa qualquer texto escuro sobre ela ilegível por baixo contraste.

## Master de conteúdo

```js
pres.defineSlideMaster({
  title: "CONTEUDO",
  background: { color: "FFFFFF" },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 9.5, h: 0.75,
        fontFace: THEME_CERISE.headFontFace, fontSize: 24, bold: true, color: THEME_CERISE.colors.dk2,
        align: "left" }, text: "" } },
    { image: { path: "assets/logo_cerise.png", x: 10.9, y: 0.3, w: 1.85, h: 0.56 } },
    { image: { path: "assets/logo_fapeg.png", x: 0.5, y: 6.95, w: 1.3, h: 0.27 } },
  ],
  slideNumber: { x: 12.7, y: 7.15, fontFace: THEME_CERISE.bodyFontFace, fontSize: 10,
    color: THEME_CERISE.colors.accent5 },
});
```

Isto pressupõe `pres.layout = "LAYOUT_WIDE"` (13,3" × 7,5"). Em `LAYOUT_16x9` (10" × 5,625",
o padrão do pptxgenjs se você não setar `pres.layout`) refaça as coordenadas proporcionalmente —
não copie os números acima sem ajustar.

## A armadilha real: logo colidindo com conteúdo que cresce

O logo FAPEG do rodapé fica em `y: 6.95`, perto da borda inferior. Qualquer conteúdo que também
se aproxime dessa borda — uma tabela grande com `autoPage: false`, uma lista longa de itens, um
bloco de texto que você redimensionou depois de já ter calibrado o layout — pode terminar depois
de `y: 6.95` e sobrepor o logo sem que isso apareça óbvio só de olhar o código. Isso aconteceu de
fato num slide com uma tabela de 14 linhas mais uma lista de 8 perguntas abaixo dela: a primeira
versão colidia com o rodapé.

**Por isso, depois de aplicar este tema a qualquer deck, gere as imagens de todas as páginas
(não só a primeira) e confira especificamente o canto inferior esquerdo e o canto superior
direito de cada uma** — são exatamente os dois pontos onde os logos deste tema ficam, e são os
dois pontos que um ajuste de conteúdo feito sem recalibrar o layout mais frequentemente invade:

```bash
# No Windows, o wrapper scripts/office/soffice.py da skill pptx falha
# ("module socket has no attribute AF_UNIX") — chame o soffice.exe direto:
"/c/Program Files/LibreOffice/program/soffice.exe" --headless --convert-to pdf deck.pptx
pdftoppm -jpeg -r 110 deck.pdf slide
```

Depois, olhe cada imagem gerada (`slide-01.jpg`, `slide-02.jpg`, ...). Se qualquer tabela ou
bloco de texto tiver crescido depois do primeiro layout, reduza sua altura/fonte ou encurte o
conteúdo — não mova os logos para abrir espaço, eles são o elemento fixo do tema.

## Se a referência institucional mudar ou um logo não bater

Os valores desta skill vêm de três fontes específicas do grupo (ver "Por que os valores abaixo
são fixos"). Se precisar atualizar algo (nova versão do logo, cor que mudou, outro grupo
afiliado), repita o processo de extração em vez de estimar a mudança:

1. Converter o `.pptx` de referência atualizado para imagens (comando acima) e olhar várias
   páginas de autores diferentes, não só a primeira — o que se repete entre páginas de pessoas
   diferentes é padrão institucional; o que aparece só numa página é estilo pessoal de quem fez
   aquele slide (ex. uma barra de cor sob o título, vista em só uma das três referências
   comparadas nesta skill, não entrou no tema por ser escolha individual, não do grupo).
2. Extrair as imagens do pacote (`python3 -c "import zipfile; zipfile.ZipFile('ref.pptx').extractall('unpacked')"`,
   mídia fica em `unpacked/ppt/media/*.png`) e montar um grid de thumbnails antes de decidir qual
   arquivo é qual logo — os nomes `image1.png`, `image2.png` não indicam o conteúdo.
3. Extrair a cor do título do XML real (`grep -o 'srgbClr val="[0-9A-Fa-f]*"' unpacked/ppt/slides/slideN.xml`
   num slide que tenha o título na cor certa), não estimar olhando a imagem.
4. Atualizar os arquivos em `assets/` desta skill e os valores no `THEME_CERISE` acima.
