"""Tests for the quiz-mode strategies, their factory and QuizSession."""

import random

import pytest

from models import CardHistory, Flashcard
from quiz_engine import (
    AdaptiveMode,
    QuizMode,
    QuizSession,
    RandomMode,
    SequentialMode,
    create_quiz_mode,
)


def drain(mode: QuizMode) -> list[str]:
    """Ask every card without answering and return the fronts in order."""
    fronts = []
    while (card := mode.next_card()) is not None:
        fronts.append(card.front)
    return fronts


@pytest.mark.parametrize(
    ("name", "expected_class"),
    [
        ("sequential", SequentialMode),
        ("random", RandomMode),
        ("adaptive", AdaptiveMode),
        ("  Adaptive ", AdaptiveMode),
    ],
)
def test_quiz_mode_factory(
    cards: list[Flashcard], name: str, expected_class: type[QuizMode]
) -> None:
    mode = create_quiz_mode(name, cards)

    assert type(mode) is expected_class
    assert isinstance(mode, QuizMode)


def test_factory_rejects_unknown_mode(cards: list[Flashcard]) -> None:
    with pytest.raises(ValueError, match="Unknown quiz mode 'spaced'"):
        create_quiz_mode("spaced", cards)


def test_adaptive_mode_behavior(cards: list[Flashcard]) -> None:
    """A missed card is asked again after two other cards."""
    mode = AdaptiveMode(cards)
    asked = []

    while (card := mode.next_card()) is not None:
        asked.append(card.front)
        first_dns_attempt = card.front == "DNS" and asked.count("DNS") == 1
        mode.record_result(card, correct=not first_dns_attempt)

    assert asked == ["DNS", "SSH", "VPN", "DNS"]


def test_adaptive_mode_asks_previously_missed_cards_first(
    cards: list[Flashcard],
) -> None:
    history = {
        "DNS": CardHistory(correct=3, incorrect=0),
        "VPN": CardHistory(correct=1, incorrect=3),
        "SSH": CardHistory(correct=1, incorrect=1),
    }

    assert drain(AdaptiveMode(cards, history=history)) == ["VPN", "SSH", "DNS"]


def test_adaptive_mode_puts_new_cards_before_mastered_ones(
    cards: list[Flashcard],
) -> None:
    history = {"DNS": CardHistory(correct=5, incorrect=0)}

    assert drain(AdaptiveMode(cards, history=history)) == ["SSH", "VPN", "DNS"]


def test_adaptive_mode_stops_repeating_after_max_repeats(
    cards: list[Flashcard],
) -> None:
    mode = AdaptiveMode(cards[:1], max_repeats=2)
    asked = 0

    while (card := mode.next_card()) is not None:
        asked += 1
        mode.record_result(card, correct=False)

    assert asked == 3  # the first attempt plus two repeats


def test_adaptive_mode_rejects_negative_settings(cards: list[Flashcard]) -> None:
    with pytest.raises(ValueError):
        AdaptiveMode(cards, requeue_gap=-1)


def test_sequential_mode_keeps_file_order(cards: list[Flashcard]) -> None:
    mode = SequentialMode(cards)
    mode.record_result(cards[0], correct=False)  # must not change the order

    assert drain(mode) == ["DNS", "SSH", "VPN"]


def test_random_mode_asks_every_card_once_in_seeded_order(
    cards: list[Flashcard],
) -> None:
    first = drain(RandomMode(cards, rng=random.Random(7)))
    second = drain(RandomMode(cards, rng=random.Random(7)))

    assert sorted(first) == ["DNS", "SSH", "VPN"]
    assert first == second


def test_random_mode_does_not_reorder_the_callers_list(
    cards: list[Flashcard],
) -> None:
    original = list(cards)
    RandomMode(cards, rng=random.Random(1))

    assert cards == original


@pytest.mark.parametrize("mode_class", [SequentialMode, RandomMode, AdaptiveMode])
def test_modes_reject_an_empty_deck(mode_class: type[QuizMode]) -> None:
    with pytest.raises(ValueError, match="at least one flashcard"):
        mode_class([])


def test_session_stops_at_limit(cards: list[Flashcard]) -> None:
    session = QuizSession(SequentialMode(cards), limit=2)
    asked = 0

    while (card := session.next_card()) is not None:
        asked += 1
        session.submit_answer(card, "wrong")

    assert asked == 2


def test_session_rejects_invalid_limit(cards: list[Flashcard]) -> None:
    with pytest.raises(ValueError, match="at least 1"):
        QuizSession(SequentialMode(cards), limit=0)


@pytest.mark.parametrize(
    ("answer", "expected"),
    [
        ("Domain Name System", True),
        ("domain name system", True),
        ("  DOMAIN   name system ", True),
        ("Domain Name Server", False),
        ("", False),
    ],
)
def test_answers_are_compared_case_insensitively(
    cards: list[Flashcard], answer: str, expected: bool
) -> None:
    session = QuizSession(SequentialMode(cards))

    assert session.submit_answer(cards[0], answer) is expected
