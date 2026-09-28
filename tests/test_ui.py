"""Tests for console output details in ui.py."""

import io

from models import CardHistory, Flashcard, SessionStats
from tests.conftest import scripted_input, squash
from ui import ConsoleUI

DNS = Flashcard("DNS", "Domain Name System")


def make_ui(answers: list[str]) -> tuple[ConsoleUI, io.StringIO, io.StringIO]:
    out, err = io.StringIO(), io.StringIO()
    ui = ConsoleUI(scripted_input(answers), out, err, use_color=False)
    return ui, out, err


def test_ask_shows_front_and_returns_answer() -> None:
    ui, out, _ = make_ui(["Domain Name System"])

    assert ui.ask(DNS, 3) == "Domain Name System"
    assert "Q3: DNS" in out.getvalue()


def test_ask_treats_quit_words_as_exit() -> None:
    ui, _, _ = make_ui(["  QUIT "])

    assert ui.ask(DNS, 1) is None


def test_empty_answer_is_returned_not_treated_as_exit() -> None:
    ui, _, _ = make_ui([""])

    assert ui.ask(DNS, 1) == ""


def test_summary_of_empty_session_has_no_missed_section() -> None:
    ui, out, _ = make_ui([])

    ui.show_summary(SessionStats())

    assert "| Accuracy | 0.0% |" in squash(out.getvalue())
    assert "Missed" not in out.getvalue()
    assert "Well done" not in out.getvalue()


def test_history_table_shows_accuracy_per_card() -> None:
    ui, out, _ = make_ui([])

    ui.show_history([DNS], {"DNS": CardHistory(correct=3, incorrect=1)})

    assert "| DNS | 3 | 1 | 75% |" in squash(out.getvalue())


def test_warnings_and_errors_go_to_error_stream() -> None:
    ui, out, err = make_ui([])

    ui.show_warning("careful")
    ui.show_error("broken")

    assert out.getvalue() == ""
    assert err.getvalue() == "Warning: careful\nError: broken\n"
