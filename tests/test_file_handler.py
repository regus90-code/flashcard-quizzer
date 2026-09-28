"""Tests for the JSON helpers in utils/file_handler.py."""

import json
import re
from pathlib import Path

import pytest

from utils.file_handler import JsonFileError, read_json, write_json


def test_write_then_read_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "folder" / "data.json"
    data = {"name": "Überprüfung", "values": [1, 2, 3]}

    write_json(path, data)

    assert read_json(path) == data


def test_write_json_replaces_existing_file_without_leftovers(tmp_path: Path) -> None:
    path = tmp_path / "data.json"
    write_json(path, {"version": 1})

    write_json(path, {"version": 2})

    assert read_json(path) == {"version": 2}
    assert [p.name for p in tmp_path.iterdir()] == ["data.json"]


def test_read_missing_file(tmp_path: Path) -> None:
    with pytest.raises(JsonFileError, match="File not found"):
        read_json(tmp_path / "missing.json")


def test_read_directory_instead_of_file(tmp_path: Path) -> None:
    with pytest.raises(JsonFileError, match="(folder|Permission denied)"):
        read_json(tmp_path)


def test_read_non_utf8_file(tmp_path: Path) -> None:
    path = tmp_path / "latin1.json"
    path.write_bytes('{"name": "Müller"}'.encode("latin-1"))

    with pytest.raises(JsonFileError, match="not valid UTF-8"):
        read_json(path)


def test_read_reports_other_os_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def failing_read(self: Path, encoding: str) -> str:
        raise OSError(5, "Input/output error")

    monkeypatch.setattr(Path, "read_text", failing_read)

    with pytest.raises(JsonFileError, match="Could not read .*Input/output error"):
        read_json(tmp_path / "data.json")


def test_read_invalid_json_reports_position(tmp_path: Path) -> None:
    broken = '{\n  "a": 1,\n}'
    path = tmp_path / "broken.json"
    path.write_text(broken, encoding="utf-8")
    # Python 3.13 changed where a trailing comma is reported (the comma
    # itself instead of the closing brace), so ask the decoder for the
    # position instead of hardcoding it.
    with pytest.raises(json.JSONDecodeError) as decoder_error:
        json.loads(broken)
    position = f"line {decoder_error.value.lineno}, column {decoder_error.value.colno}"

    with pytest.raises(JsonFileError, match=re.escape(position)):
        read_json(path)


def test_write_unserializable_data(tmp_path: Path) -> None:
    with pytest.raises(JsonFileError, match="cannot be saved as JSON"):
        write_json(tmp_path / "data.json", {"callback": print})


def test_write_into_a_file_instead_of_folder(tmp_path: Path) -> None:
    blocker = tmp_path / "blocker"
    blocker.write_text("", encoding="utf-8")

    with pytest.raises(JsonFileError, match="Could not write"):
        write_json(blocker / "data.json", {"a": 1})


def test_failed_write_removes_temporary_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def failing_replace(source: str, target: str) -> None:
        raise OSError(28, "No space left on device")

    monkeypatch.setattr("utils.file_handler.os.replace", failing_replace)

    with pytest.raises(JsonFileError, match="No space left on device"):
        write_json(tmp_path / "data.json", {"a": 1})
    assert list(tmp_path.iterdir()) == []
