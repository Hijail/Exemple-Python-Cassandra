import logging
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from app.extract.json_extractor import extract_json
from app.transform.common import validate_and_normalize
from app.transform.anomaly import train_purchase_anomaly_model, score_purchases
from app.routing.registry import TRANSFORM_REGISTRY
from app.routing.router import transform_for_table

LOGGER = logging.getLogger(__name__)


def build_purchase_projection(df: pd.DataFrame, model) -> pd.DataFrame:
    purchases = df.loc[df["event_type"].eq("purchase")].copy()
    if purchases.empty:
        return pd.DataFrame(columns=[
            "player_id", "purchase_month", "occurred_at", "event_id",
            "product_id", "category", "quantity", "amount", "currency",
            "anomaly_score", "is_anomaly"
        ])

    purchases = score_purchases(purchases, model)
    purchases["purchase_month"] = purchases["occurred_at"].dt.strftime("%Y-%m")
    columns = [
        "player_id", "purchase_month", "occurred_at", "event_id",
        "product_id", "category", "quantity", "amount", "currency",
        "anomaly_score", "is_anomaly"
    ]
    for column in columns:
        if column not in purchases.columns:
            purchases[column] = None
    return purchases[columns].copy()


def run_etl(
    input_path: Path,
    baseline_path: Path,
    loader=None,
    dry_run: bool = False,
) -> Dict[str, int]:
    source = extract_json(input_path)
    LOGGER.info("Événements extraits : %d", len(source))

    valid, rejected = validate_and_normalize(source)
    LOGGER.info("Événements valides : %d ; rejetés : %d", len(valid), len(rejected))

    if not rejected.empty:
        rejected.to_json("rejected_events.json", orient="records", date_format="iso", indent=2)
        LOGGER.warning("%d événements rejetés (rejected_events.json)", len(rejected))

    if valid.empty:
        return {}

    # Le modèle est entraîné sur un jeu de référence distinct du lot à traiter.
    model = train_purchase_anomaly_model(baseline_path)

    loaded: Dict[str, int] = {}
    projections = {
        "events_by_player_day": transform_for_table(valid, "events_by_player_day"),
        "events_by_type_day": transform_for_table(valid, "events_by_type_day"),
        "purchases_by_player_month": build_purchase_projection(valid, model),
    }

    for table_name, projection in projections.items():
        if dry_run:
            LOGGER.info("[DRY RUN] %s : %d lignes", table_name, len(projection))
            loaded[table_name] = len(projection)
        elif loader is not None:
            loaded[table_name] = loader.load(table_name, projection)
        else:
            raise ValueError("Un loader Cassandra est requis hors dry-run.")

    return loaded
