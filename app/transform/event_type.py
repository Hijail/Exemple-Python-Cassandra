import pandas as pd

from app.transform.common import add_calendar_columns


def transform_events_by_type(df: pd.DataFrame) -> pd.DataFrame:
    result = add_calendar_columns(df)
    columns = [
        "event_type", "event_day", "occurred_at", "event_id",
        "player_id", "session_id", "level_id", "amount", "currency"
    ]
    for column in columns:
        if column not in result.columns:
            result[column] = None
    return result[columns].copy()
