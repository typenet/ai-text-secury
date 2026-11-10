# Design system

Visual sóbrio e institucional para um produto de segurança vendido a bancos, jurídico e governo.
A vitrine ao vivo fica em **`/design`** (ex.: http://localhost:3000/design), com todos os componentes nos temas claro e escuro.

## Princípios

1. **Confiança antes de alarme.** A interface é neutra (azul-tinta e cinzas frios). Vermelho, laranja e amarelo só aparecem quando o documento tem risco.
2. **Uma cor = um significado.** `primary` (azul-tinta) é ação principal; `brand` (verde-petróleo) é a marca e o selo de "verificado"; `risk-*` é só para risco.
3. **Explicar para leigos.** Toda regra do motor tem nome e explicação em português (`src/lib/rules.ts`), e toda faixa de risco diz o que fazer (`BANDS` em `src/components/risk.tsx`).
4. **Acessível por padrão.** Contraste AA, foco visível, alvos de toque de 40 px ou mais, `prefers-reduced-motion` respeitado.

## Tokens (`frontend/src/app/globals.css`)

Cada cor é definida uma vez com `light-dark(claro, escuro)`. O tema segue o sistema operacional e o botão no topo força claro ou escuro (classe `.light`/`.dark` no `<html>`, salva no navegador).

| Token | Uso |
|---|---|
| `background`, `card`, `muted`, `border`, `input` | Superfícies e linhas |
| `foreground`, `muted-foreground` | Texto principal e de apoio |
| `primary` / `primary-foreground` | Botão principal, logo |
| `brand` / `brand-soft` / `brand-foreground` | Marca, links, ícones de destaque, foco (`ring`) |
| `destructive` | Erros de formulário e ações perigosas |
| `risk-{safe,attention,high,critical}` | Cor sólida da faixa (anel do score, barras) |
| `risk-*-soft` + `risk-*-fg` | Fundo suave + texto legível (badges, alertas) |

Faixas do score (iguais ao backend): **Seguro 0–20 · Atenção 21–50 · Alto risco 51–80 · Crítico 81–100**.

Tipografia: **IBM Plex Sans** (interface) e **IBM Plex Mono** (códigos de regra, trechos, API keys), servidas localmente via Fontsource (sem chamada ao Google Fonts). Raio base `0.5rem`.

## Componentes

`src/components/ui/` segue o padrão shadcn/ui (pode-se adicionar outros com `npx shadcn add <nome>`):
Button (`default`, `brand`, `outline`, `secondary`, `ghost`, `destructive`, `link`), Badge (inclui variantes de risco), Card, Input, Label, Alert (inclui variantes de risco), Separator, Skeleton, Progress.

Componentes do produto em `src/components/`:

- `brand/logo.tsx` — marca (escudo + linhas do documento + linha de varredura).
- `risk.tsx` — `RiskBadge`, `SeverityBadge` e o mapa `BANDS` com rótulo, veredito e ação de cada faixa.
- `score-gauge.tsx` — anel de 270° com o score e marcas em 20/50/80.
- `scan-result.tsx` — tela de resultado (score, filtros por severidade, lista de achados).
- `dropzone.tsx` — arrastar-e-soltar com fallback de clique e teclado.
- `theme-toggle.tsx`, `site-header.tsx`.

## Regras para novas telas

- Use só tokens (`bg-card`, `text-muted-foreground`, `bg-risk-high`…), nunca hex solto nem cores do Tailwind (`bg-red-500`).
- Uma ação principal (`Button` padrão) por tela.
- Para mudar a paleta, edite apenas `globals.css`; as telas acompanham.
