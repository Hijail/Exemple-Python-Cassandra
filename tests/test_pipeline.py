import json

import pandas as pd
import pytest

from app.pipeline.etl import build_purchase_projection, run_etl


def write_baseline(path):
    rows = [
        {
            "amount": 4.0 + (index % 5) * 0.7,
            "quantity": 1 + (index % 2),
            "occurred_at": "2026-10-01T12:00:00Z",
        }
        for index in range(40)
    ]
    path.write_text(json.dumps(rows), encoding="utf-8")


def write_events(path, events):
    path.write_text(json.dumps({"events": events}), encoding="utf-8")


def event(event_id, event_type="login", quantity=None):
    return {
        "event_id": event_id,
        "player_id": "player-001",
        "event_type": event_type,
        "occurred_at": "2026-11-13T10:00:00Z",
        "product_id": "coins" if event_type == "purchase" else None,
        "category": "virtual" if event_type == "purchase" else None,
        "quantity": quantity,
        "amount": 2.5 if event_type == "purchase" else None,
        "currency": "EUR" if event_type == "purchase" else None,
    }


def test_purchase_projection_empty_has_expected_columns():
    columns = ["event_type", "occurred_at"]
    source = pd.DataFrame(columns=columns)

    projection = build_purchase_projection(source, model=None)

    assert projection.empty
    assert projection.columns.tolist() == [
        "player_id", "purchase_month", "occurred_at", "event_id", "product_id",
        "category", "quantity", "amount", "currency", "anomaly_score", "is_anomaly",
    ]


def test_purchase_projection_scores_and_derives_month(monkeypatch):
    source = pd.DataFrame([event("p1", "purchase", 1)])
    source["occurred_at"] = pd.to_datetime(source["occurred_at"], utc=True)

    def fake_score(frame, model):
        result = frame.copy()
        result["anomaly_score"] = -0.2
        result["is_anomaly"] = True
        return result

    monkeypatch.setattr("app.pipeline.etl.score_purchases", fake_score)

    projection = build_purchase_projection(source, model=object())

    assert projection.iloc[0]["purchase_month"] == "2026-11"
    assert projection.iloc[0]["anomaly_score"] == -0.2
    assert bool(projection.iloc[0]["is_anomaly"])


def test_run_etl_dry_run_returns_projection_counts(tmp_path, monkeypatch):
    source_path = tmp_path / "events.json"
    baseline_path = tmp_path / "baseline.json"
    write_events(source_path, [event("e1"), event("e2", "purchase", 1)])
    write_baseline(baseline_path)
    monkeypatch.chdir(tmp_path)

    counts = run_etl(source_path, baseline_path, dry_run=True)

    assert counts == {
        "events_by_player_day": 2,
        "events_by_type_day": 2,
        "purchases_by_player_month": 1,
    }
    assert not (tmp_path / "rejected_events.json").exists()


def test_run_etl_returns_empty_when_every_event_is_invalid(tmp_path, monkeypatch):
    source_path = tmp_path / "events.json"
    baseline_path = tmp_path / "unused-baseline.json"
    write_events(source_path, [{
        "event_id": "bad",
        "player_id": "player-001",
        "event_type": "login",
        "occurred_at": "invalid",
    }])
    monkeypatch.chdir(tmp_path)

    counts = run_etl(source_path, baseline_path, dry_run=True)

    assert counts == {}
    assert json.loads((tmp_path / "rejected_events.json").read_text())


def test_run_etl_requires_loader_outside_dry_run(tmp_path):
    source_path = tmp_path / "events.json"
    baseline_path = tmp_path / "baseline.json"
    write_events(source_path, [event("e1")])
    write_baseline(baseline_path)

    with pytest.raises(ValueError, match="loader Cassandra est requis"):
        run_etl(source_path, baseline_path)


def test_run_etl_sends_each_projection_to_loader(tmp_path):
    source_path = tmp_path / "events.json"
    baseline_path = tmp_path / "baseline.json"
    write_events(source_path, [event("e1"), event("e2", "purchase", 1)])
    write_baseline(baseline_path)

    class RecordingLoader:
        def __init__(self):
            self.calls = []

        def load(self, table, frame):
            self.calls.append((table, len(frame)))
            return len(frame)

    loader = RecordingLoader()

    result = run_etl(source_path, baseline_path, loader=loader)

    assert result["purchases_by_player_month"] == 1
    assert loader.calls == [
        ("events_by_player_day", 2),
        ("events_by_type_day", 2),
        ("purchases_by_player_month", 1),
    ]
