"""Tests for persisting results between sessions (history.py)."""

import json
from pathlib import Path

import pytest

from history import HistoryStore, deck_key, default_history_path
from models import CardHistory, Flashcard
from utils.file_handler import JsonFileError

DNS = Flashcard("DNS", "Domain Name System")
SSH = Flashcard("SSH", "Secure Shell")


def test_load_without_file_returns_empty_history(tmp_path: Path) -> None:
    assert HistoryStore(tmp_path / "history.json").load("deck") == {}


def test_record_accumulates_across_sessions(tmp_path: Path) -> None:
    store = HistoryStore(tmp_path / "history.json")

    store.record("deck", [(DNS, True), (SSH, False)])
    store.record("deck", [(DNS, False), (DNS, True)])

    assert store.load("deck") == {
        "DNS": CardHistory(correct=2, incorrect=1),
        "SSH": CardHistory(correct=0, incorrect=1),
    }


def test_decks_are_stored_separately(tmp_path: Path) -> None:
    store = HistoryStore(tmp_path / "history.json")

    store.record("deck_a", [(DNS, True)])
    store.record("deck_b", [(DNS, False)])

    assert store.load("deck_a") == {"DNS": CardHistory(correct=1, incorrect=0)}
    assert store.load("deck_b") == {"DNS": CardHistory(correct=0, incorrect=1)}


@pytest.mark.parametrize(
    "content",
    [
        [],
        {"decks": []},
        {"decks": {"deck": ["DNS"]}},
        {"decks": {"deck": {"DNS": 5}}},
        {"decks": {"deck": {"DNS": {"correct": "many"}}}},
    ],
)
def test_corrupt_history_raises_readable_error(tmp_path: Path, content: object) -> None:
    path = tmp_path / "history.json"
    path.write_text(json.dumps(content), encoding="utf-8")

    with pytest.raises(JsonFileError, match="History file has an"):
        HistoryStore(path).load("deck")


def test_record_refuses_to_overwrite_corrupt_history(tmp_path: Path) -> None:
    path = tmp_path / "history.json"
    corrupt = json.dumps({"decks": {"deck": {"DNS": 5}}})
    path.write_text(corrupt, encoding="utf-8")

    with pytest.raises(JsonFileError):
        HistoryStore(path).record("deck", [(DNS, True)])
    assert path.read_text(encoding="utf-8") == corrupt


def test_deck_key_is_the_same_for_relative_and_absolute_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    assert deck_key("deck.json") == deck_key(tmp_path / "deck.json")


def test_default_history_path_is_in_home_folder() -> None:
    assert default_history_path().parent.parent == Path.home()
