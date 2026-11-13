import pandas as pd
import pytest


@pytest.fixture
def sample_events():
    return pd.DataFrame([{
        "event_id": "evt-1",
        "player_id": " player-001 ",
        "event_type": " LOGIN ",
        "occurred_at": "2026-11-13T10:00:00Z",
        "session_id": "session-1",
        "level_id": None,
        "score": None,
        "amount": None,
        "currency": None,
        "quantity": None,
        "product_id": None,
        "category": None,
    }])
