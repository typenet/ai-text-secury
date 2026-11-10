"""Comandos administrativos.

python -m app.cli bootstrap --org "Minha Empresa"   # cria org, projeto e API key
python -m app.cli sync-rules                        # popula a tabela rules
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
    s = sub.add_parser("scan")
    s.add_argument("path")
    args = parser.parse_args()
    if args.cmd == "bootstrap":
        bootstrap(args.org)
    elif args.cmd == "sync-rules":
        sync_rules()
    else:
        scan_file(args.path)


if __name__ == "__main__":
    main()
