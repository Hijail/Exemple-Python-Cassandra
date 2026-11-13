import pandas as pd
import pytest

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


def test_validation_rejects_missing_required_columns():
    with pytest.raises(ValueError, match="Colonnes obligatoires absentes"):
        validate_and_normalize(pd.DataFrame({"event_id": ["e1"]}))


def test_validation_rejects_blank_required_values(sample_events):
    sample_events.loc[0, "player_id"] = "  "

    valid, rejected = validate_and_normalize(sample_events)

    assert valid.empty
    assert len(rejected) == 1


def test_validation_keeps_last_duplicate_event_id(sample_events):
    duplicate = sample_events.copy()
    duplicate.loc[0, "event_type"] = "logout"
    source = pd.concat([sample_events, duplicate], ignore_index=True)

    valid, rejected = validate_and_normalize(source)

    assert len(valid) == 1
    assert valid.iloc[0]["event_type"] == "logout"
    assert len(rejected) == 1


def test_validation_handles_empty_input():
    valid, rejected = validate_and_normalize(pd.DataFrame())

    assert valid.empty
    assert rejected.empty
