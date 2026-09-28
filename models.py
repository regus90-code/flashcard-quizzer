"""Core data types shared across the Flashcard Quizzer."""

from dataclasses import dataclass, field
from typing import Any


def normalize_answer(text: str) -> str:
    """Normalize text for comparison: case-insensitive, whitespace-collapsed."""
    return " ".join(text.split()).casefold()


@dataclass(frozen=True)
class Flashcard:
    """A single question (front) and answer (back) pair."""

    front: str
    back: str

    def matches(self, answer: str) -> bool:
        """Return True if ``answer`` equals the back of the card.

        The comparison ignores letter case and extra whitespace, so
        " domain name  SYSTEM " matches "Domain Name System".
        """
        return normalize_answer(answer) == normalize_answer(self.back)


@dataclass
class CardHistory:
    """How often a card was answered correctly/incorrectly in past sessions."""

    correct: int = 0
    incorrect: int = 0

    @property
    def attempts(self) -> int:
        """Total number of recorded answers for the card."""
        return self.correct + self.incorrect

    @property
    def miss_rate(self) -> float:
        """Share of incorrect answers (0.0 for cards never answered)."""
        return self.incorrect / self.attempts if self.attempts else 0.0


@dataclass
class SessionStats:
    """Results collected during one quiz session."""

    results: list[tuple[Flashcard, bool]] = field(default_factory=list)

    def record(self, card: Flashcard, correct: bool) -> None:
        """Store the outcome of one answered question."""
        self.results.append((card, correct))

    @property
    def total(self) -> int:
        """Number of questions answered."""
        return len(self.results)

    @property
    def correct(self) -> int:
        """Number of correct answers."""
        return sum(1 for _, correct in self.results if correct)

    @property
    def accuracy(self) -> float:
        """Percentage of correct answers (0.0 when nothing was answered)."""
        return 100.0 * self.correct / self.total if self.total else 0.0

    @property
    def missed(self) -> list[Flashcard]:
        """Cards answered incorrectly at least once, in first-missed order."""
        missed: list[Flashcard] = []
        for card, correct in self.results:
            if not correct and card not in missed:
                missed.append(card)
        return missed

    def to_dict(self) -> dict[str, Any]:
        """Serialize the summary for JSON export."""
        return {
            "total_questions": self.total,
            "correct": self.correct,
            "accuracy_percent": round(self.accuracy, 1),
            "missed": [{"front": c.front, "back": c.back} for c in self.missed],
        }
