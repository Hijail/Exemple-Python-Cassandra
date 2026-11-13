from app.config import get_settings


def test_settings_parse_hosts_and_read_environment(monkeypatch):
    monkeypatch.setenv("CASSANDRA_HOSTS", " node-a, node-b ,, ")
    monkeypatch.setenv("CASSANDRA_PORT", "9142")
    monkeypatch.setenv("CASSANDRA_KEYSPACE", "analytics")
    monkeypatch.setenv("CASSANDRA_LOCAL_DC", "dc-test")
    monkeypatch.setenv("INPUT_PATH", "fixtures/input.json")
    monkeypatch.setenv("PURCHASE_BASELINE_PATH", "fixtures/baseline.json")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    settings = get_settings()

    assert settings.cassandra_hosts == ["node-a", "node-b"]
    assert settings.cassandra_port == 9142
    assert settings.keyspace == "analytics"
    assert settings.local_dc == "dc-test"
    assert str(settings.input_path) == "fixtures/input.json"
    assert str(settings.baseline_path) == "fixtures/baseline.json"
    assert settings.log_level == "DEBUG"
