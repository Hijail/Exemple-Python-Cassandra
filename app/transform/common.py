from typing import Tuple

import pandas as pd

REQUIRED_COLUMNS = {
    "event_id", "player_id", "event_type", "occurred_at"
}


def validate_and_normalize(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Retourne (valides, rejetés). Ne modifie pas le DataFrame d'entrée."""
    if df.empty:
        return df.copy(), df.copy()

    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        raise ValueError("Colonnes obligatoires absentes : {}".format(sorted(missing)))

    result = df.copy()
    result["event_id"] = result["event_id"].astype("string").str.strip()
    result["player_id"] = result["player_id"].astype("string").str.strip()
    result["event_type"] = result["event_type"].astype("string").str.strip().str.lower()
    result["occurred_at"] = pd.to_datetime(result["occurred_at"], errors="coerce", utc=True)

    valid_mask = (
        result["event_id"].notna()
        & result["event_id"].ne("")
        & result["player_id"].notna()
        & result["player_id"].ne("")
        & result["event_type"].notna()
        & result["event_type"].ne("")
        & result["occurred_at"].notna()
    )

    valid = result.loc[valid_mask].copy()
    rejected = result.loc[~valid_mask].copy()

    # event_id est une clé de déduplication globale du lot.
    duplicated = valid["event_id"].duplicated(keep="last")
    rejected = pd.concat([rejected, valid.loc[duplicated]], ignore_index=True)
    valid = valid.loc[~duplicated].copy()

    return valid.reset_index(drop=True), rejected.reset_index(drop=True)


def add_calendar_columns(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["event_day"] = result["occurred_at"].dt.date
    result["event_month"] = result["occurred_at"].dt.strftime("%Y-%m")
    return result
