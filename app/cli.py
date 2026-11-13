import argparse
import logging
from pathlib import Path

from app.config import get_settings
from app.logging_config import configure_logging
from app.load.cassandra_client import connect
from app.load.cassandra_loader import CassandraLoader
from app.pipeline.etl import run_etl

SCHEMA_PATH = Path("cassandra/schema.cql")


def init_schema(session, keyspace: str) -> None:
    statements = [part.strip() for part in SCHEMA_PATH.read_text(encoding="utf-8").split(";") if part.strip()]
    for statement in statements:
        session.execute(statement)


def main() -> None:
    parser = argparse.ArgumentParser(description="ETL JSON vers Cassandra")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--input", type=Path)
    run_parser.add_argument("--dry-run", action="store_true")

    subparsers.add_parser("init-schema")
    args = parser.parse_args()

    settings = get_settings()
    configure_logging(settings.log_level)

    if args.command == "init-schema":
        cluster, session = connect(settings.cassandra_hosts, settings.cassandra_port, settings.local_dc)
        try:
            init_schema(session, settings.keyspace)
        finally:
            cluster.shutdown()
        logging.info("Schéma Cassandra initialisé.")
        return

    input_path = args.input or settings.input_path
    if args.dry_run:
        run_etl(input_path, settings.baseline_path, dry_run=True)
        return

    cluster, session = connect(settings.cassandra_hosts, settings.cassandra_port, settings.local_dc)
    try:
        loader = CassandraLoader(session, settings.keyspace)
        run_etl(input_path, settings.baseline_path, loader=loader)
    finally:
        cluster.shutdown()


if __name__ == "__main__":
    main()
