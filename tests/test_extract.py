import json
import pytest
from app.extract.json_extractor import extract_json


def test_extracts_json_array(tmp_path):
    path = tmp_path / "events.json"
    path.write_text(json.dumps({"events": [{"event_id": "e1"}]}), encoding="utf-8")
    df = extract_json(path)
    assert len(df) == 1
    assert df.iloc[0]["event_id"] == "e1"


def test_extracts_single_event_object(tmp_path):
    path = tmp_path / "event.json"
    path.write_text(json.dumps({"event_id": "e1"}), encoding="utf-8")

    df = extract_json(path)

    assert df.to_dict(orient="records") == [{"event_id": "e1"}]


def test_extracts_json_lines_and_ignores_blank_lines(tmp_path):
    path = tmp_path / "events.jsonl"
    path.write_text('{"event_id":"e1"}\n\n{"event_id":"e2"}\n', encoding="utf-8")

    df = extract_json(path)

    assert df["event_id"].tolist() == ["e1", "e2"]


def test_empty_file_returns_empty_dataframe(tmp_path):
    path = tmp_path / "empty.json"
    path.write_text(" \n", encoding="utf-8")

    assert extract_json(path).empty


def test_rejects_non_list_json_payload(tmp_path):
    path = tmp_path / "events.json"
    path.write_text(json.dumps("not an event list"), encoding="utf-8")

    with pytest.raises(ValueError, match="liste d'événements"):
        extract_json(path)


def test_missing_file_has_clear_error(tmp_path):
    with pytest.raises(FileNotFoundError, match="Fichier source introuvable"):
        extract_json(tmp_path / "missing.json")
