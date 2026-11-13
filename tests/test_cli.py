from pathlib import Path
from types import SimpleNamespace

from app import cli


class FakeSession:
    def __init__(self):
        self.statements = []

    def execute(self, statement):
        self.statements.append(statement)


class FakeCluster:
    def __init__(self):
        self.shutdown_called = False

    def shutdown(self):
        self.shutdown_called = True


def settings(tmp_path):
    return SimpleNamespace(
        cassandra_hosts=["localhost"],
        cassandra_port=9042,
        local_dc="dc1",
        keyspace="analytics",
        input_path=tmp_path / "default.json",
        baseline_path=tmp_path / "baseline.json",
        log_level="INFO",
    )


def test_init_schema_executes_nonempty_cql_statements(tmp_path, monkeypatch):
    schema = tmp_path / "schema.cql"
    schema.write_text("CREATE KEYSPACE x;\n\nCREATE TABLE y;", encoding="utf-8")
    monkeypatch.setattr(cli, "SCHEMA_PATH", schema)
    session = FakeSession()

    cli.init_schema(session, "analytics")

    assert session.statements == ["CREATE KEYSPACE x", "CREATE TABLE y"]


def test_cli_dry_run_uses_override_input_and_skips_connection(tmp_path, monkeypatch):
    config = settings(tmp_path)
    calls = []
    monkeypatch.setattr(cli, "get_settings", lambda: config)
    monkeypatch.setattr(cli, "configure_logging", lambda level: None)
    monkeypatch.setattr(cli, "run_etl", lambda *args, **kwargs: calls.append((args, kwargs)))
    monkeypatch.setattr(cli, "connect", lambda *args: (_ for _ in ()).throw(AssertionError("connected")))
    monkeypatch.setattr("sys.argv", ["app.cli", "run", "--input", "custom.json", "--dry-run"])

    cli.main()

    assert calls == [((Path("custom.json"), config.baseline_path), {"dry_run": True})]


def test_cli_init_schema_always_shuts_down_cluster(tmp_path, monkeypatch):
    config = settings(tmp_path)
    session = FakeSession()
    cluster = FakeCluster()
    monkeypatch.setattr(cli, "get_settings", lambda: config)
    monkeypatch.setattr(cli, "configure_logging", lambda level: None)
    monkeypatch.setattr(cli, "connect", lambda *args: (cluster, session))
    monkeypatch.setattr(cli, "init_schema", lambda *args: None)
    monkeypatch.setattr("sys.argv", ["app.cli", "init-schema"])

    cli.main()

    assert cluster.shutdown_called


def test_cli_normal_run_loads_data_and_shuts_down_cluster(tmp_path, monkeypatch):
    config = settings(tmp_path)
    session = FakeSession()
    cluster = FakeCluster()
    loader = object()
    calls = []
    monkeypatch.setattr(cli, "get_settings", lambda: config)
    monkeypatch.setattr(cli, "configure_logging", lambda level: None)
    monkeypatch.setattr(cli, "connect", lambda *args: (cluster, session))
    monkeypatch.setattr(cli, "CassandraLoader", lambda *args: loader)
    monkeypatch.setattr(cli, "run_etl", lambda *args, **kwargs: calls.append((args, kwargs)))
    monkeypatch.setattr("sys.argv", ["app.cli", "run"])

    cli.main()

    assert calls == [
        ((config.input_path, config.baseline_path), {"loader": loader})
    ]
    assert cluster.shutdown_called
