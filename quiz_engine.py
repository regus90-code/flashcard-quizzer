"""Quiz logic: card-selection strategies, their factory, and the quiz session.

Strategy pattern: every quiz mode answers the same question -- "which card
comes next?" -- with a different algorithm. ``QuizSession`` only talks to the
``QuizMode`` interface, so a new mode (e.g. spaced repetition) is one new
class plus one line in ``create_quiz_mode``; nothing else changes.
"""

import random
from abc import ABC, abstractmethod
from collections import Counter, deque
from collections.abc import Mapping, Sequence
from typing import Optional

from models import CardHistory, Flashcard, SessionStats

AVAILABLE_MODES = ("sequential", "random", "adaptive")


class QuizMode(ABC):
    """Strategy interface: decides which card is asked next."""

    def __init__(self, cards: Sequence[Flashcard]) -> None:
        if not cards:
            raise ValueError("A quiz needs at least one flashcard")
        self._cards = list(cards)

    @abstractmethod
    def next_card(self) -> Optional[Flashcard]:
        """Return the next card to ask, or None when the quiz is over."""

    def record_result(self, card: Flashcard, correct: bool) -> None:
        """React to an answer. Modes that do not adapt ignore it."""


class SequentialMode(QuizMode):
    """Asks every card once, in file order (1..N)."""

    def __init__(self, cards: Sequence[Flashcard]) -> None:
        super().__init__(cards)
        self._queue = deque(self._cards)

    def next_card(self) -> Optional[Flashcard]:
        return self._queue.popleft() if self._queue else None


class RandomMode(QuizMode):
    """Asks every card once, in shuffled order."""

    def __init__(
        self, cards: Sequence[Flashcard], rng: Optional[random.Random] = None
    ) -> None:
        super().__init__(cards)
        shuffled = list(self._cards)
        (rng or random.Random()).shuffle(shuffled)
        self._queue = deque(shuffled)

    def next_card(self) -> Optional[Flashcard]:
        return self._queue.popleft() if self._queue else None


class AdaptiveMode(QuizMode):
    """Prioritizes cards the user gets wrong.

    * Before the quiz: cards are ordered by their miss rate from earlier
      sessions, worst first. Among cards without misses, never-answered
      cards come before already-mastered ones. Ties keep file order.
    * During the quiz: a missed card is asked again after ``requeue_gap``
      other cards, at most ``max_repeats`` extra times, so a session always
      ends even if the user never gets a card right.
    """

    def __init__(
        self,
        cards: Sequence[Flashcard],
        history: Optional[Mapping[str, CardHistory]] = None,
        requeue_gap: int = 2,
        max_repeats: int = 2,
    ) -> None:
        super().__init__(cards)
        if requeue_gap < 0 or max_repeats < 0:
            raise ValueError("requeue_gap and max_repeats must not be negative")
        past = history or {}

        def priority(card: Flashcard) -> tuple[float, bool]:
            record = past.get(card.front, CardHistory())
            return (-record.miss_rate, record.attempts > 0)

        self._queue = deque(sorted(self._cards, key=priority))
        self._requeue_gap = requeue_gap
        self._max_repeats = max_repeats
        self._repeats: Counter[Flashcard] = Counter()

    def next_card(self) -> Optional[Flashcard]:
        return self._queue.popleft() if self._queue else None

    def record_result(self, card: Flashcard, correct: bool) -> None:
        if correct or self._repeats[card] >= self._max_repeats:
            return
        self._repeats[card] += 1
        self._queue.insert(min(self._requeue_gap, len(self._queue)), card)


def create_quiz_mode(
    name: str,
    cards: Sequence[Flashcard],
    history: Optional[Mapping[str, CardHistory]] = None,
    rng: Optional[random.Random] = None,
) -> QuizMode:
    """Factory: build the quiz mode selected by the user.

    Args:
        name: One of ``AVAILABLE_MODES`` (case-insensitive).
        cards: The deck to quiz on.
        history: Past results per card front, used by the adaptive mode.
        rng: Random generator for the random mode (seed it for repeatable
            order).

    Raises:
        ValueError: If ``name`` is not a known mode.
    """
    key = name.strip().lower()
    if key == "sequential":
        return SequentialMode(cards)
    if key == "random":
        return RandomMode(cards, rng=rng)
    if key == "adaptive":
        return AdaptiveMode(cards, history=history)
    raise ValueError(
        f"Unknown quiz mode '{name}'. Choose from: {', '.join(AVAILABLE_MODES)}"
    )


class QuizSession:
    """Runs one quiz: asks the cards picked by a mode and keeps score.

    The session contains no input/output code, so it can be driven by the
    console UI or directly by tests.
    """

    def __init__(self, mode: QuizMode, limit: Optional[int] = None) -> None:
        if limit is not None and limit < 1:
            raise ValueError("limit must be at least 1")
        self._mode = mode
        self._limit = limit
        self.stats = SessionStats()

    def next_card(self) -> Optional[Flashcard]:
        """Return the next card, or None when the mode or limit is exhausted."""
        if self._limit is not None and self.stats.total >= self._limit:
            return None
        return self._mode.next_card()

    def submit_answer(self, card: Flashcard, answer: str) -> bool:
        """Check an answer, record it, and let the mode adapt.

        Returns:
            True if the answer is correct (case-insensitive).
        """
        correct = card.matches(answer)
        self.stats.record(card, correct)
        self._mode.record_result(card, correct)
        return correct
