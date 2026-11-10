# AI Text Secury

SaaS B2B de **AI Document Security**: analisa PDF, DOCX e TXT **antes** de serem consumidos por IA
ou indexados em RAG e devolve um **score de risco de 0 a 100** com cada achado localizado
(regra, página, posição e trecho).

O que detecta hoje:

- **Texto oculto**: cor do fundo, fonte < 2 pt, render mode 3, opacidade 0, fora da página,
  camadas desligadas, `w:vanish` no Word.
- **Unicode invisível**: zero-width, tag characters (U+E0000, com o texto decodificado) e controles bidi.
- **Prompt injection**: baseline heurístico PT/EN, com severidade crítica quando o trecho está oculto.
- **Conteúdo ativo**: JavaScript, OpenAction, arquivos embutidos.
- **Contêiner**: comentários e campos ocultos, metadados suspeitos.
- **Dados pessoais (LGPD, beta)**: CPF e CNPJ com dígito verificador, e-mail (valores mascarados).

## Stack

| Camada | Escolha |
| --- | --- |
| API | Python 3.13, FastAPI, SQLAlchemy 2, Alembic |
| Fila | Celery + Redis |
| Banco | PostgreSQL (findings com `evidence` em JSONB) |
| Arquivos | MinIO local, S3 em produção (boto3) |
| PDF | pdfplumber + pikepdf (sem PyMuPDF por ser AGPL), pypdfium2 para render |
| DOCX | lxml direto no XML |
| OCR | Tesseract `por+eng`, só nas páginas suspeitas |
| Frontend | Next.js, Tailwind CSS v4, shadcn/ui |

## Subir local

```bash
cp .env.example .env
make up            # postgres, redis, minio, migrações, api, worker e web
make bootstrap     # cria organização, projeto e imprime uma API key
```

- API e docs OpenAPI: http://localhost:8000/docs
- Web: http://localhost:3000 (cole a API key no formulário)
- Console do MinIO: http://localhost:9001

Exemplo pela API:

```bash
curl -H "X-API-Key: $KEY" -F file=@curriculo.pdf http://localhost:8000/v1/scans
curl -H "X-API-Key: $KEY" http://localhost:8000/v1/scans/<id>
```

## Desenvolvimento sem Docker

```bash
cd backend
uv venv && uv pip install -e ".[dev]"   # ou: python -m venv .venv && pip install -e ".[dev]"
pytest                                   # testes geram os PDFs/DOCX em memória
python -m app.cli scan arquivo.pdf       # roda o engine local, sem banco nem fila

cd ../frontend
npm install && npm run dev
```

Com `SCAN_EAGER=true` a API roda o scan na própria requisição, sem precisar do worker.

## Estrutura

```
backend/
  app/
    api/            rotas REST (/health, /v1/scans) e autenticação por X-API-Key
    models/         organizations, users, projects, api_keys, documents, document_pages,
                    scans, findings, rules, reports
    scanner/        engine de detecção (independente da API)
      engine.py     detecta o formato e orquestra os detectores
      pdf.py docx.py txt.py   extratores + regras estruturais
      unicode.py metadata.py ocr.py injection.py lgpd.py
      rules.py      catálogo de regras    report.py  score e relatório
    services/       storage S3/MinIO e execução do scan
    worker/         Celery
  alembic/          migrações
frontend/
  src/app/          páginas (upload e resultado do scan)
  src/components/ui componentes shadcn/ui
docs/architecture.md
```

## Score

`score = 100 × (1 − ∏(1 − wᵢ·cᵢ))`, com peso por severidade (baixa 0,1; média 0,3; alta 0,6;
crítica 0,9) e confiança `c`. A combinação satura, então dez achados baixos não superam um crítico.
Texto oculto + prompt injection leva o documento direto para crítico.

Faixas: 0–20 seguro · 21–50 atenção · 51–80 alto risco · 81–100 crítico.

## Design system

O frontend usa **shadcn/ui** como padrão. Para trocar: os tokens de cor e raio ficam em
`frontend/src/app/globals.css` e os componentes em `frontend/src/components/ui/`. As páginas só
importam desses dois lugares.

## Próximos passos

Veja `docs/architecture.md` para o roadmap técnico (OCR ligado ao fluxo, classificador ONNX,
relatório PDF, viewer com destaque por bbox, avaliação no benchmark CrackedPDFs).
