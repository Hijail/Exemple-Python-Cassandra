import pandas as pd

from app import dashboard


class FakeStatement:
    fetch_size = None


class FakeSession:
    def __init__(self, rows):
        self.rows = rows
        self.statement = FakeStatement()
        self.executed = None

    def prepare(self, query):
        self.query = query
        return self.statement

    def execute(self, statement, values):
        self.executed = (statement, values)
        return self.rows


def test_read_partition_sets_fetch_limit_and_returns_dataframe():
    session = FakeSession([{"event_id": "e1"}])

    frame = dashboard.read_partition(session, "SELECT * FROM events WHERE id = ?", ("e1",))

    assert isinstance(frame, pd.DataFrame)
    assert frame["event_id"].tolist() == ["e1"]
    assert session.statement.fetch_size == dashboard.MAX_ROWS
    assert session.executed == (session.statement, ("e1",))


def test_dashboard_shows_connection_error_without_starting_queries(monkeypatch):
    calls = []

    class FakeStreamlit:
        def set_page_config(self, **kwargs):
            calls.append("page")

        def title(self, value):
            calls.append("title")

        def caption(self, value):
            calls.append("caption")

        def error(self, value):
            calls.append("error")

        def exception(self, error):
            calls.append("exception")

    monkeypatch.setattr(dashboard, "st", FakeStreamlit())
    monkeypatch.setattr(dashboard, "connect", lambda *args: (_ for _ in ()).throw(ConnectionError()))

    dashboard.main()

    assert calls == ["page", "title", "caption", "error", "exception"]
