"""Tests for loading and validating flashcard decks (data_loader.py)."""

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from data_loader import FlashcardLoadError, load_flashcards, parse_flashcards
from models import Flashcard

WriteJson = Callable[..., Path]


def test_load_valid_flashcards_array(write_json_file: WriteJson) -> None:
    path = write_json_file(
        [
            {"front": "DNS", "back": "Domain Name System"},
            {"front": "SSH", "back": "Secure Shell"},
        ]
    )

    assert load_flashcards(path) == [
        Flashcard("DNS", "Domain Name System"),
        Flashcard("SSH", "Secure Shell"),
    ]


def test_load_valid_flashcards_object_format(write_json_file: WriteJson) -> None:
    path = write_json_file({"cards": [{"front": "def", "back": "define a function"}]})

    assert load_flashcards(path) == [Flashcard("def", "define a function")]


def test_load_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "broken.json"
    path.write_text('[{"front": "DNS", "back": }]', encoding="utf-8")

    with pytest.raises(FlashcardLoadError, match=r"Invalid JSON .*line 1"):
        load_flashcards(path)


def test_load_missing_required_field(write_json_file: WriteJson) -> None:
    path = write_json_file(
        [{"front": "DNS", "back": "Domain Name System"}, {"front": "SSH"}]
    )

    with pytest.raises(
        FlashcardLoadError, match='card #2 is missing the required field "back"'
    ):
        load_flashcards(path)


def test_load_missing_file_reports_path(tmp_path: Path) -> None:
    with pytest.raises(FlashcardLoadError, match="File not found"):
        load_flashcards(tmp_path / "does_not_exist.json")


def test_loaded_text_is_trimmed(write_json_file: WriteJson) -> None:
    path = write_json_file([{"front": "  DNS ", "back": " Domain Name System\n"}])

    assert load_flashcards(path) == [Flashcard("DNS", "Domain Name System")]


def test_extra_card_fields_are_ignored() -> None:
    raw = [{"front": "DNS", "back": "Domain Name System", "hint": "networking"}]

    assert parse_flashcards(raw) == [Flashcard("DNS", "Domain Name System")]


@pytest.mark.parametrize(
    ("raw", "message"),
    [
        ([], "contains no flashcards"),
        ({"cards": []}, "contains no flashcards"),
        ({"deck": []}, 'object with a "cards" key'),
        ({"cards": {"front": "a"}}, '"cards" must be a list'),
        ("just text", 'object with a "cards" key'),
        (42, 'object with a "cards" key'),
        (["DNS"], "card #1 must be an object"),
        ([{"back": "Domain Name System"}], 'missing the required field "front"'),
        ([{"front": "DNS", "back": ""}], 'field "back" must be non-empty text'),
        ([{"front": "   ", "back": "x"}], 'field "front" must be non-empty text'),
        ([{"front": "DNS", "back": 53}], 'field "back" must be non-empty text'),
        ([{"front": None, "back": "x"}], 'field "front" must be non-empty text'),
    ],
)
def test_invalid_deck_structures_are_rejected(raw: Any, message: str) -> None:
    with pytest.raises(FlashcardLoadError, match=message):
        parse_flashcards(raw, source="deck.json")


def test_error_message_names_the_source() -> None:
    with pytest.raises(FlashcardLoadError, match=r"^my_deck\.json: "):
        parse_flashcards([], source="my_deck.json")
