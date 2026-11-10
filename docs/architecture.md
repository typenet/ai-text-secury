# Arquitetura

## Fluxo de um scan

```
cliente ──POST /v1/scans──▶ API ──▶ storage S3 (arquivo, criptografado em repouso)
                             │
                             ├──▶ Postgres: documents + scans (status=queued)
                             └──▶ Redis ──▶ worker Celery
                                             │ baixa o arquivo
                                             │ scanner.scan_bytes()
                                             │   1. detecta o formato pelos magic bytes
                                             │   2. extrator (pdf/docx/txt): segmentos + findings estruturais
                                             │   3. unicode em todos os segmentos
                                             │   4. prompt injection (oculto => crítico)
                                             │   5. LGPD no texto visível
                                             │   6. score + faixa
                                             └──▶ Postgres: findings, score, status=done
cliente ──GET /v1/scans/{id}──▶ API
```

O engine (`app/scanner`) não conhece banco, fila nem HTTP: recebe bytes e devolve um `ScanReport`.
Isso permite usá-lo no worker, no CLI, num SDK ou numa versão self-hosted.

## Formato de um finding

```json
{
  "rule": "WHITE_TEXT",
  "severity": "HIGH",
  "page": 1,
  "bbox": [72.0, 132.4, 404.8, 144.4],
  "text": "Ignore all previous instructions",
  "confidence": 100,
  "technique": "hidden_text",
  "detector_version": "pdf@0.1.0",
  "evidence": {"font_size": 12.0, "color": "(1, 1, 1)"}
}
```

`bbox` usa o sistema do pdfplumber (x0, top, x1, bottom em pontos) para destacar no viewer.
`detector_version` permite reprocessar só o que mudou quando uma regra evoluir.

## Modelo de dados

Multi-tenant por `organization_id`. Um documento pode ter vários scans, para reanalisar quando as
regras mudarem sem perder o histórico. API keys guardam só o hash SHA-256.

## Decisões

- **Sem PyMuPDF**: AGPL exige licença comercial em SaaS fechado. pdfplumber + pikepdf cobrem
  caractere, cor, posição, content stream, OCG, JavaScript e anexos.
- **Render/OCR só nas páginas suspeitas**: o PhantomLint leva 44–68 s por documento fazendo isso em
  tudo. O módulo `ocr.py` está pronto, mas ainda não está ligado ao fluxo.
- **Classificador plugável**: `injection.set_classifier()` aceita qualquer objeto com `predict()`.
  O baseline é heurístico; o próximo passo é um modelo pequeno (Transformers → ONNX, CPU).
- **Proteções de parsing**: tamanho máximo de upload, limite de páginas, XML sem entidades externas,
  limite de tamanho por parte do DOCX.

## Roadmap técnico

1. Ligar o OCR às páginas com achados e implementar `TEXT_UNDER_IMAGE` de ponta a ponta.
2. WHITE_TEXT comparando com a cor real do fundo renderizado (hoje assume fundo branco).
3. Decodificar texto via `ToUnicode` para fontes compostas no detector de render mode.
4. Classificador de injection em ONNX, com dataset em português.
5. Avaliação automática no benchmark CrackedPDFs (precisão, recall, falso positivo).
6. Relatório em PDF e viewer com PDF.js destacando cada bbox.
7. Autenticação de usuários no painel (hoje o painel usa a API key) e retenção por organização.
8. Sanitização: devolver o texto limpo para indexação.
