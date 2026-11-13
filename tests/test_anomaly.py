from pathlib import Path

from app.transform.anomaly import train_purchase_anomaly_model, score_purchases


def test_purchase_model_scores_rows(tmp_path):
    import json
    baseline = []
    for i in range(40):
        baseline.append({
            "amount": 4.0 + (i % 5) * 0.7,
            "quantity": 1,
            "occurred_at": "2026-10-01T12:00:00Z"
        })
    path = tmp_path / "baseline.json"
    path.write_text(json.dumps(baseline), encoding="utf-8")

    model = train_purchase_anomaly_model(path)
    import pandas as pd
    purchase = pd.DataFrame([{
        "amount": 500.0,
        "quantity": 20,
        "occurred_at": pd.Timestamp("2026-11-13T12:00:00Z")
    }])
    result = score_purchases(purchase, model)
    assert "anomaly_score" in result
    assert "is_anomaly" in result
