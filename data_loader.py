"""Load flashcard decks from JSON and validate their structure.

Two layouts are accepted::

    [{"front": "DNS", "back": "Domain Name System"}, ...]          # array
    {"cards": [{"front": "DNS", "back": "Domain Name System"}]}    # object
"""

from pathlib import Path
from typing import Any

from models import Flashcard
from utils.file_handler import JsonFileError, read_json

REQUIRED_FIELDS = ("front", "back")


class FlashcardLoadError(Exception):
    """Raised when a deck cannot be loaded; the message is user-facing."""


def load_flashcards(path: str | Path) -> list[Flashcard]:
    """Load and validate a flashcard deck from a JSON file.

    Args:
        path: Location of the JSON deck.

    Returns:
        The cards in file order.

    Raises:
        FlashcardLoadError: If the file is missing, is not valid JSON, or
            does not describe a non-empty list of cards.
    """
    try:
        raw = read_json(path)
    except JsonFileError as error:
        raise FlashcardLoadError(str(error)) from None
    return parse_flashcards(raw, source=str(path))


def parse_flashcards(raw: Any, source: str = "deck") -> list[Flashcard]:
    """Validate already-parsed JSON data and convert it to flashcards.

    Args:
        raw: Parsed JSON value (array or ``{"cards": [...]}`` object).
        source: Name used in error messages, usually the file path.

    Raises:
        FlashcardLoadError: If the structure is not a valid deck.
    """
    if isinstance(raw, dict):
        if "cards" not in raw:
            raise FlashcardLoadError(
                f'{source}: expected a list of cards or an object with a "cards" key'
            )
        raw_cards = raw["cards"]
        if not isinstance(raw_cards, list):
            raise FlashcardLoadError(f'{source}: "cards" must be a list')
    elif isinstance(raw, list):
        raw_cards = raw
    else:
        raise FlashcardLoadError(
            f'{source}: expected a list of cards or an object with a "cards" key'
        )

    if not raw_cards:
        raise FlashcardLoadError(f"{source}: the deck contains no flashcards")

    return [
        _parse_card(item, position, source)
        for position, item in enumerate(raw_cards, start=1)
    ]


def _parse_card(item: Any, position: int, source: str) -> Flashcard:
    """Validate one card entry; ``position`` is 1-based for readable errors."""
    if not isinstance(item, dict):
        raise FlashcardLoadError(
            f'{source}: card #{position} must be an object with "front" and "back"'
        )
    for field_name in REQUIRED_FIELDS:
        if field_name not in item:
            raise FlashcardLoadError(
                f"{source}: card #{position} is missing the required "
                f'field "{field_name}"'
            )
        value = item[field_name]
        if not isinstance(value, str) or not value.strip():
            raise FlashcardLoadError(
                f'{source}: card #{position} field "{field_name}" '
                "must be non-empty text"
            )
    return Flashcard(front=item["front"].strip(), back=item["back"].strip())
