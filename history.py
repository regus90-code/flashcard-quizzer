"""Persist per-card results across sessions.

The adaptive mode uses this history to ask previously missed cards first,
and ``--stats`` prints it. File layout::

    {"version": 1,
     "decks": {"<absolute deck path>": {"<card front>": {"correct": 2,
                                                          "incorrect": 1}}}}
"""

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from models import CardHistory, Flashcard
from utils.file_handler import JsonFileError, read_json, write_json

HISTORY_VERSION = 1


def default_history_path() -> Path:
    """Location of the history file when ``--history-file`` is not given."""
    return Path.home() / ".flashcard_quizzer" / "history.json"


def deck_key(deck_path: str | Path) -> str:
    """Identify a deck by its absolute path so relative paths match."""
    return str(Path(deck_path).resolve())


class HistoryStore:
    """Reads and updates the history JSON file."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self, deck: str) -> dict[str, CardHistory]:
        """Return the stored history of one deck (empty if none yet).

        Raises:
            JsonFileError: If the history file exists but is unreadable or
                has an unexpected structure.
        """
        entries = self._read_all().get(deck, {})
        history = {}
        for front, counts in entries.items():
            if not (
                isinstance(counts, dict)
                and isinstance(counts.get("correct", 0), int)
                and isinstance(counts.get("incorrect", 0), int)
            ):
                raise JsonFileError(
                    f"History file has an invalid entry for '{front}': {self.path}"
                )
            history[front] = CardHistory(
                correct=counts.get("correct", 0),
                incorrect=counts.get("incorrect", 0),
            )
        return history

    def record(self, deck: str, results: Iterable[tuple[Flashcard, bool]]) -> None:
        """Add a session's answers to the stored history of ``deck``.

        Raises:
            JsonFileError: If the history file cannot be read or written.
        """
        decks = self._read_all()
        history = self.load(deck)
        for card, correct in results:
            past = history.setdefault(card.front, CardHistory())
            if correct:
                past.correct += 1
            else:
                past.incorrect += 1
        decks[deck] = {
            front: {"correct": past.correct, "incorrect": past.incorrect}
            for front, past in history.items()
        }
        write_json(self.path, {"version": HISTORY_VERSION, "decks": decks})

    def _read_all(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        data = read_json(self.path)
        decks = data.get("decks") if isinstance(data, dict) else None
        if not isinstance(decks, dict) or not all(
            isinstance(entries, dict) for entries in decks.values()
        ):
            raise JsonFileError(f"History file has an unexpected format: {self.path}")
        return decks
