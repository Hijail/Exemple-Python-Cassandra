import pandas as pd
import pytest

from app.load.cassandra_loader import CassandraLoader


class FakeFuture:
    def __init__(self, error=None):
        self.error = error
        self.resolved = False

    def result(self):
        self.resolved = True
        if self.error:
            raise self.error


class FakeSession:
    def __init__(self, future_errors=None):
        self.prepared = []
        self.calls = []
        self.futures = []
        self.future_errors = list(future_errors or [])

    def prepare(self, query):
        self.prepared.append(query)
        return query

    def execute_async(self, statement, values):
        self.calls.append((statement, values))
        error = self.future_errors.pop(0) if self.future_errors else None
        future = FakeFuture(error)
        self.futures.append(future)
        return future


def purchase_frame(quantities):
    return pd.DataFrame({"quantity": quantities, "amount": [2.5] * len(quantities)})


def test_loader_prepares_only_known_tables_and_keyspace():
    session = FakeSession()

    loader = CassandraLoader(session, "analytics")

    assert len(session.prepared) == 3
    assert all("analytics." in query for query in session.prepared)
    assert set(loader.statements) == {
        "events_by_player_day",
        "events_by_type_day",
        "purchases_by_player_month",
    }


def test_loader_converts_nullable_quantity_to_cassandra_int_and_null():
    session = FakeSession()
    loader = CassandraLoader(session, "analytics", max_in_flight=2)

    loaded = loader.load("purchases_by_player_month", purchase_frame([1, None, 3]))

    assert loaded == 3
    assert [call[1][0] for call in session.calls] == [1, None, 3]
    assert all(future.resolved for future in session.futures)


def test_loader_rejects_fractional_cassandra_integer():
    loader = CassandraLoader(FakeSession(), "analytics")

    with pytest.raises(ValueError, match="entier Cassandra 32 bits"):
        loader.load("purchases_by_player_month", purchase_frame([1.5]))


def test_loader_rejects_unknown_table():
    loader = CassandraLoader(FakeSession(), "analytics")

    with pytest.raises(KeyError, match="Table non autorisée"):
        loader.load("unknown", pd.DataFrame())


def test_loader_requires_positive_in_flight_limit():
    loader = CassandraLoader(FakeSession(), "analytics", max_in_flight=0)

    with pytest.raises(ValueError, match="max_in_flight"):
        loader.load("purchases_by_player_month", purchase_frame([1]))


def test_loader_drains_batch_before_raising_write_error():
    session = FakeSession([RuntimeError("write failed"), None])
    loader = CassandraLoader(session, "analytics", max_in_flight=2)

    with pytest.raises(RuntimeError, match="write failed"):
        loader.load("purchases_by_player_month", purchase_frame([1, 2]))

    assert all(future.resolved for future in session.futures)
