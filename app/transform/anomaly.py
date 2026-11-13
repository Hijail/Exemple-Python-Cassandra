from pathlib import Path
from typing import List

import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

FEATURE_COLUMNS = ["amount", "quantity", "event_hour"]


def _purchase_features(df: pd.DataFrame) -> pd.DataFrame:
    features = pd.DataFrame(index=df.index)
    features["amount"] = pd.to_numeric(df.get("amount"), errors="coerce")
    features["quantity"] = pd.to_numeric(df.get("quantity"), errors="coerce")
    features["event_hour"] = df["occurred_at"].dt.hour.astype(float)
    return features.fillna({"amount": 0.0, "quantity": 1.0, "event_hour": 0.0})


def train_purchase_anomaly_model(baseline_path: Path) -> Pipeline:
    baseline = pd.read_json(baseline_path)
    if len(baseline) < 20:
        raise ValueError("Le baseline d'achat doit contenir au moins 20 lignes.")
    baseline["occurred_at"] = pd.to_datetime(baseline["occurred_at"], utc=True)
    features = _purchase_features(baseline)
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("detector", IsolationForest(
            n_estimators=200,
            contamination=0.05,
            random_state=42,
        )),
    ])
    pipeline.fit(features[FEATURE_COLUMNS])
    return pipeline


def score_purchases(df: pd.DataFrame, model: Pipeline) -> pd.DataFrame:
    result = df.copy()
    features = _purchase_features(result)
    result["anomaly_score"] = model.decision_function(features[FEATURE_COLUMNS])
    result["is_anomaly"] = model.predict(features[FEATURE_COLUMNS]) == -1
    return result
