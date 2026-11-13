import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


def extract_json(path: Path) -> pd.DataFrame:
    """Lit un tableau JSON ou un fichier JSON Lines dans un DataFrame."""
    if not path.exists():
        raise FileNotFoundError("Fichier source introuvable : {}".format(path))

    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return pd.DataFrame()

    try:
        payload = json.loads(raw)
        if isinstance(payload, dict):
            payload = payload.get("events", [payload])
        if not isinstance(payload, list):
            raise ValueError("Le JSON doit contenir une liste d'événements.")
        records: List[Dict[str, Any]] = payload
    except json.JSONDecodeError:
        records = [json.loads(line) for line in raw.splitlines() if line.strip()]

    return pd.json_normalize(records)
