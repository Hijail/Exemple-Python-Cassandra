import pytest

from app.load import cassandra_client


class FakeCluster:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.shutdown_called = False

    def connect(self):
        if hasattr(self, "connect_error"):
            raise self.connect_error
        return "session"

    def shutdown(self):
        self.shutdown_called = True


def test_connect_uses_protocol_five_and_returns_cluster_session(monkeypatch):
    clusters = []

    def create_cluster(**kwargs):
        cluster = FakeCluster(**kwargs)
        clusters.append(cluster)
        return cluster

    monkeypatch.setattr(cassandra_client, "Cluster", create_cluster)

    cluster, session = cassandra_client.connect(["localhost"], 9042, "dc1")

    assert session == "session"
    assert cluster is clusters[0]
    assert cluster.kwargs["protocol_version"] == 5
    assert cluster.kwargs["contact_points"] == ["localhost"]


def test_connect_shuts_down_cluster_when_session_creation_fails(monkeypatch):
    cluster = FakeCluster()
    cluster.connect_error = RuntimeError("unavailable")
    monkeypatch.setattr(cassandra_client, "Cluster", lambda **kwargs: cluster)

    with pytest.raises(RuntimeError, match="unavailable"):
        cassandra_client.connect(["localhost"], 9042, "dc1")

    assert cluster.shutdown_called
