# Deploy em VPS

A mesma stack do dev roda na VPS, com três diferenças: nenhuma porta de banco, Redis ou
storage fica pública; o Caddy fica na frente com HTTPS automático; e todos os segredos são
obrigatórios (o compose recusa subir sem eles).

```
Internet ──443──▶ Caddy ──┬─ /v1, /health, /docs ─▶ api:8000 ─┬─ postgres
                          └─ resto ───────────────▶ web:3000  ├─ redis ◀── worker
                                                              └─ storage (S3 local, RustFS)
```

## 1. Preparar a VPS (uma vez)

Qualquer VPS Linux com 2 vCPU e 4 GB de RAM serve para começar.

```bash
# Docker + plugin compose (Ubuntu/Debian)
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER   # saia e entre de novo no SSH

# Firewall: só SSH e web
sudo ufw allow OpenSSH && sudo ufw allow 80 && sudo ufw allow 443 && sudo ufw enable
```

No seu provedor de DNS, crie um registro **A** apontando o domínio (ex.:
`app.seudominio.com.br`) para o IP da VPS. O Caddy só consegue emitir o certificado depois
que o DNS estiver propagado.

## 2. Baixar o código e configurar

```bash
git clone https://github.com/typenet/ai-text-secury.git
cd ai-text-secury
cp .env.example .env
nano .env
```

No `.env`, troque tudo que está marcado com `[prod]`:

| Variável | Valor |
| --- | --- |
| `ENVIRONMENT` | `production` |
| `POSTGRES_PASSWORD` | `openssl rand -hex 24` |
| `S3_ACCESS_KEY` / `S3_SECRET_KEY` | `openssl rand -hex 12` / `openssl rand -hex 24` |
| `STORAGE_SSE_MASTER_KEY` | `openssl rand -base64 32` (guarde fora da VPS também) |
| `BOOTSTRAP_API_KEY` | vazio (uma chave aleatória é gerada na primeira subida) |
| `DOMAIN` | `app.seudominio.com.br` |

## 3. Subir

```bash
make prod-up                      # build + sobe tudo
make prod-ps                      # todos devem ficar "healthy"
docker compose logs migrate       # mostra a API key gerada (só na primeira vez)
```

Abra `https://SEU_DOMINIO`, cole a API key e envie um arquivo.

## 4. Atualizar para uma versão nova

```bash
git pull
make prod-up      # reconstrói as imagens; o serviço migrate aplica as migrações antes da API subir
```

Para poder voltar atrás, defina `APP_VERSION` no `.env` (ex.: `0.2.0`) antes do build: a
imagem anterior continua no Docker com a tag antiga.

## 5. Backup

```bash
make backup       # gera backups/db-AAAAMMDD-HHMMSS.dump e backups/storage-....tar.gz
```

- O dump do Postgres é consistente com a API rodando. O `.tar.gz` do storage é uma cópia
  do volume feita a quente; para uma cópia 100% consistente, pare a API e o worker antes
  (`docker compose stop api worker`), ou espelhe o bucket para outro S3 com qualquer
  cliente S3 (`rclone sync`, `aws s3 sync --endpoint-url ...`).
- Os arquivos no storage são cifrados com `STORAGE_SSE_MASTER_KEY`. **Sem essa chave o
  backup do storage não serve para nada**: guarde-a num cofre de senhas, separada da VPS.
- Leve a pasta `backups/` para fora da VPS (outro servidor, S3, Backblaze B2...). Um cron
  diário é suficiente no início:
  `0 3 * * * cd ~/ai-text-secury && make backup && rclone copy backups remoto:secury-backups`

Restaurar o banco: `make restore-db FILE=backups/db-....dump`.

## 6. Storage: local na VPS ou S3 gerenciado?

O storage local (serviço `storage`) fala a mesma API S3 que a AWS, então a troca é só de
configuração, sem mudar código. Fique no local enquanto o volume couber com folga no disco
da VPS. Vale migrar para S3 gerenciado (AWS S3, Cloudflare R2, Backblaze B2) quando:

- o disco da VPS começar a apertar, ou os documentos passarem de algumas centenas de GB;
- um cliente exigir durabilidade, região ou certificação específica (bancos, governo);
- você tiver mais de uma VPS rodando a API/worker;
- não quiser mais cuidar do backup do storage.

Para migrar:

1. Crie o bucket no provedor e uma credencial com acesso só a ele.
2. Copie os arquivos: `rclone sync local:documents s3novo:documents` (ou `aws s3 sync`).
3. No `.env`: `COMPOSE_PROFILES=` (vazio), `S3_ENDPOINT_URL=` (vazio para AWS, ou a URL do
   R2/B2), `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_BUCKET`, `S3_REGION` do provedor.
4. `make prod-up`. O serviço `storage` deixa de subir e a API passa a usar o S3.

> Sobre o MinIO: a imagem oficial `minio/minio` foi removida do Docker Hub em 2026 (o projeto
> open source foi arquivado). Por isso o compose usa o **RustFS** (Apache 2.0), que é
> compatível com a API S3 e funciona com os mesmos clientes (boto3, rclone, aws cli).
