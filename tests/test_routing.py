from app.routing.registry import TRANSFORM_REGISTRY
from app.routing.router import transform_for_table


def test_registry_has_distinct_transformations():
    assert "events_by_player_day" in TRANSFORM_REGISTRY
    assert "events_by_type_day" in TRANSFORM_REGISTRY
    assert TRANSFORM_REGISTRY["events_by_player_day"] is not TRANSFORM_REGISTRY["events_by_type_day"]


def test_player_projection(sample_events):
    from app.transform.common import validate_and_normalize
    valid, _ = validate_and_normalize(sample_events)
    result = transform_for_table(valid, "events_by_player_day")
    assert list(result.columns)[0] == "player_id"
    assert result.iloc[0]["player_id"] == "player-001"


def test_type_projection_has_calendar_and_source_fields(sample_events):
    from app.transform.common import validate_and_normalize
    valid, _ = validate_and_normalize(sample_events)

    result = transform_for_table(valid, "events_by_type_day")

    assert result.iloc[0]["event_type"] == "login"
    assert str(result.iloc[0]["event_day"]) == "2026-11-13"
    assert result.iloc[0]["player_id"] == "player-001"


def test_unknown_table_fails(sample_events):
    import pytest
    with pytest.raises(KeyError):
        transform_for_table(sample_events, "unknown_table")
