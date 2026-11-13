import pandas as pd

from app.transform.common import add_calendar_columns


def transform_player_events(df: pd.DataFrame) -> pd.DataFrame:
    result = add_calendar_columns(df)
    columns = [
        "player_id", "event_day", "occurred_at", "event_id",
        "event_type", "session_id", "level_id", "score", "amount", "currency"
    ]
    for column in columns:
        if column not in result.columns:
            result[column] = None
    return result[columns].copy()
