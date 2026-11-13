from app.transform.common import validate_and_normalize


def test_validation_normalizes_event(sample_events):
    valid, rejected = validate_and_normalize(sample_events)
    assert len(valid) == 1
    assert len(rejected) == 0
    assert valid.iloc[0]["player_id"] == "player-001"
    assert valid.iloc[0]["event_type"] == "login"
    assert str(valid.iloc[0]["occurred_at"].tz) == "UTC"


def test_validation_rejects_invalid_timestamp(sample_events):
    sample_events.loc[0, "occurred_at"] = "not-a-date"
    valid, rejected = validate_and_normalize(sample_events)
    assert valid.empty
    assert len(rejected) == 1
