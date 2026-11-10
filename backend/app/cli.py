"""Comandos administrativos.

python -m app.cli setup                             # sync-rules + init-storage + seed (idempotente)
python -m app.cli bootstrap --org "Minha Empresa"   # cria org, projeto e uma nova API key
python -m app.cli sync-rules                        # popula a tabela rules
python -m app.cli init-storage                      # cria o bucket se não existir
python -m app.cli seed                              # garante org/projeto/API key iniciais
python -m app.cli scan arquivo.pdf                  # roda o engine localmente (sem banco)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def bootstrap(org_name: str) -> None:
    from app.core.security import generate_api_key
    from app.db.session import SessionLocal
    from app.models import ApiKey, Organization, Project

    with SessionLocal() as db:
        org = Organization(name=org_name)
        project = Project(organization=org, name="default")
        key, prefix, key_hash = generate_api_key()
        db.add_all([org, project])
        db.flush()
        db.add(
            ApiKey(
                organization_id=org.id,
                project_id=project.id,
                name="bootstrap",
                prefix=prefix,
                key_hash=key_hash,
            )
        )
        db.commit()
        print(f"organization_id={org.id}\nproject_id={project.id}\napi_key={key}")
        print("Guarde a API key: ela não será exibida novamente.", file=sys.stderr)


def seed() -> None:
    """Idempotente: pode rodar a cada subida do compose sem duplicar nada."""
    from sqlalchemy import func, select

    from app.core.config import get_settings
    from app.core.security import KEY_PREFIX, generate_api_key, hash_api_key
    from app.db.session import SessionLocal
    from app.models import ApiKey, Organization, Project

    s = get_settings()
    fixed_key = (s.bootstrap_api_key or "").strip()
    if fixed_key and (not fixed_key.startswith(KEY_PREFIX) or len(fixed_key) < 24):
        sys.exit(f"BOOTSTRAP_API_KEY precisa começar com {KEY_PREFIX!r} e ter 24+ caracteres")

    with SessionLocal() as db:
        exists = select(ApiKey).where(ApiKey.key_hash == hash_api_key(fixed_key or ""))
        if fixed_key and db.scalar(exists):
            print("seed: API key de BOOTSTRAP_API_KEY já cadastrada")
            return
        if not fixed_key and db.scalar(select(func.count()).select_from(ApiKey)):
            print("seed: já existem API keys, nada a fazer")
            return

        org = db.scalar(select(Organization).where(Organization.name == s.bootstrap_org))
        if org is None:
            org = Organization(name=s.bootstrap_org)
            db.add(org)
            db.flush()
        project = db.scalar(
            select(Project).where(Project.organization_id == org.id, Project.name == "default")
        )
        if project is None:
            project = Project(organization=org, name="default")
            db.add(project)
            db.flush()

        if fixed_key:
            key, prefix, key_hash = fixed_key, fixed_key[:12], hash_api_key(fixed_key)
        else:
            key, prefix, key_hash = generate_api_key()
        db.add(
            ApiKey(
                organization_id=org.id,
                project_id=project.id,
                name="bootstrap",
                prefix=prefix,
                key_hash=key_hash,
            )
        )
        db.commit()
        print(f"seed: organização {org.name!r} pronta (organization_id={org.id})")
        if fixed_key:
            print(f"seed: API key de BOOTSTRAP_API_KEY cadastrada (prefixo {prefix})")
        else:
            print(f"seed: API key gerada, guarde agora (não será exibida de novo): {key}")


def init_storage() -> None:
    from app.services.storage import S3Storage

    storage = S3Storage()
    created = storage.ensure_bucket()
    print(f"bucket {storage.bucket!r} {'criado' if created else 'já existe'}")


def setup() -> None:
    sync_rules()
    init_storage()
    seed()


def sync_rules() -> None:
    from app.db.session import SessionLocal
    from app.models import RuleRow
    from app.scanner.rules import RULES

    with SessionLocal() as db:
        for r in RULES.values():
            db.merge(
                RuleRow(
                    code=r.code,
                    severity=r.severity.value,
                    technique=r.technique,
                    formats=list(r.formats),
                    description=r.description,
                )
            )
        db.commit()
    print(f"{len(RULES)} regras sincronizadas")


def scan_file(path: str) -> None:
    from app.scanner import scan_bytes

    report = scan_bytes(Path(path).read_bytes(), path)
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(prog="app.cli")
    sub = parser.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("bootstrap")
    b.add_argument("--org", required=True)
    sub.add_parser("sync-rules")
    sub.add_parser("init-storage")
    sub.add_parser("seed")
    sub.add_parser("setup")
    s = sub.add_parser("scan")
    s.add_argument("path")
    args = parser.parse_args()
    if args.cmd == "bootstrap":
        bootstrap(args.org)
    elif args.cmd == "sync-rules":
        sync_rules()
    elif args.cmd == "init-storage":
        init_storage()
    elif args.cmd == "seed":
        seed()
    elif args.cmd == "setup":
        setup()
    else:
        scan_file(args.path)


if __name__ == "__main__":
    main()
