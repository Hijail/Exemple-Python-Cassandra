import json
from app.extract.json_extractor import extract_json


def test_extracts_json_array(tmp_path):
    path = tmp_path / "events.json"
    path.write_text(json.dumps({"events": [{"event_id": "e1"}]}), encoding="utf-8")
    df = extract_json(path)
    assert len(df) == 1
    assert df.iloc[0]["event_id"] == "e1"
