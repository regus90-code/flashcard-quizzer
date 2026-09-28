"""Tests for the data types in models.py."""

from models import CardHistory, Flashcard, SessionStats

DNS = Flashcard("DNS", "Domain Name System")
SSH = Flashcard("SSH", "Secure Shell")


def test_empty_session_has_zero_accuracy() -> None:
    stats = SessionStats()

    assert (stats.total, stats.correct, stats.accuracy) == (0, 0, 0.0)
    assert stats.missed == []


def test_session_stats_count_repeated_questions() -> None:
    stats = SessionStats()
    for card, correct in [(DNS, False), (SSH, True), (DNS, False), (DNS, True)]:
        stats.record(card, correct)

    assert stats.total == 4
    assert stats.correct == 2
    assert stats.accuracy == 50.0
    assert stats.missed == [DNS]  # listed once, even though missed twice


def test_missed_cards_keep_first_missed_order() -> None:
    stats = SessionStats()
    for card in (SSH, DNS, SSH):
        stats.record(card, correct=False)

    assert stats.missed == [SSH, DNS]


def test_card_history_miss_rate() -> None:
    assert CardHistory().miss_rate == 0.0
    assert CardHistory(correct=1, incorrect=3).miss_rate == 0.75
    assert CardHistory(correct=1, incorrect=3).attempts == 4
