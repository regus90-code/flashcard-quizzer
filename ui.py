"""Console input/output for the quiz: prompts, colored feedback, summaries."""

import sys
from collections.abc import Callable, Mapping, Sequence
from typing import Optional, TextIO

from colorama import Fore, Style, just_fix_windows_console

from models import CardHistory, Flashcard, SessionStats

QUIT_COMMANDS = frozenset({"exit", "quit"})


class ConsoleUI:
    """Terminal user interface.

    ``input_func`` and the output streams are injectable so tests can
    simulate a user without a real terminal.
    """

    def __init__(
        self,
        input_func: Callable[[str], str] = input,
        output: Optional[TextIO] = None,
        error_output: Optional[TextIO] = None,
        use_color: bool = True,
    ) -> None:
        self._input = input_func
        self._out = output if output is not None else sys.stdout
        self._err = error_output if error_output is not None else sys.stderr
        self._use_color = use_color
        if use_color:
            just_fix_windows_console()

    def _color(self, text: str, color: str) -> str:
        return f"{color}{text}{Style.RESET_ALL}" if self._use_color else text

    def _print(self, text: str = "") -> None:
        print(text, file=self._out)

    def show_welcome(self, deck_name: str, mode: str, card_count: int) -> None:
        """Print the quiz header and how to quit."""
        self._print(self._color("Flashcard Quizzer", Style.BRIGHT))
        self._print(f"Deck: {deck_name} ({card_count} cards) | Mode: {mode}")
        self._print(
            "Type your answer and press Enter. " "Type 'exit' or press Ctrl+C to quit."
        )
        self._print()

    def ask(self, card: Flashcard, number: int) -> Optional[str]:
        """Show the front of a card and read the answer.

        Returns:
            The typed answer, or None if the user wants to quit ('exit',
            'quit', or end of input).
        """
        self._print(self._color(f"Q{number}: {card.front}", Fore.CYAN))
        try:
            answer = self._input("> ")
        except EOFError:
            return None
        if answer.strip().lower() in QUIT_COMMANDS:
            return None
        return answer

    def show_feedback(self, correct: bool, card: Flashcard) -> None:
        """Print Correct (green) or Incorrect plus the right answer (red)."""
        if correct:
            self._print(self._color("Correct!", Fore.GREEN))
        else:
            self._print(self._color(f"Incorrect. Answer: {card.back}", Fore.RED))
        self._print()

    def show_quit(self) -> None:
        """Confirm that the quiz was ended early."""
        self._print()
        self._print(self._color("Quiz ended early.", Fore.YELLOW))

    def show_summary(self, stats: SessionStats) -> None:
        """Print the session summary table and the list of missed terms."""
        rows = [
            ("Total Questions", str(stats.total)),
            ("Correct", str(stats.correct)),
            ("Accuracy", f"{stats.accuracy:.1f}%"),
        ]
        self._print(self._color("Session Summary", Style.BRIGHT))
        self._print_table(("Metric", "Value"), rows)
        if stats.missed:
            self._print("Missed terms:")
            for card in stats.missed:
                self._print(self._color(f"  - {card.front} -> {card.back}", Fore.RED))
        elif stats.total:
            self._print(self._color("No missed terms. Well done!", Fore.GREEN))

    def show_history(
        self, cards: Sequence[Flashcard], history: Mapping[str, CardHistory]
    ) -> None:
        """Print lifetime results per card of a deck (for ``--stats``)."""
        self._print(self._color("All-time statistics", Style.BRIGHT))
        if not any(history.get(card.front) for card in cards):
            self._print("No answers recorded for this deck yet. Play a quiz first.")
            return
        rows = []
        for card in cards:
            past = history.get(card.front, CardHistory())
            accuracy = f"{100 - 100 * past.miss_rate:.0f}%" if past.attempts else "-"
            rows.append((card.front, str(past.correct), str(past.incorrect), accuracy))
        self._print_table(("Card", "Correct", "Incorrect", "Accuracy"), rows)

    def show_info(self, message: str) -> None:
        """Print a neutral message."""
        self._print(message)

    def show_warning(self, message: str) -> None:
        """Print a non-fatal problem to the error stream."""
        print(self._color(f"Warning: {message}", Fore.YELLOW), file=self._err)

    def show_error(self, message: str) -> None:
        """Print a fatal problem to the error stream."""
        print(self._color(f"Error: {message}", Fore.RED), file=self._err)

    def _print_table(
        self, headers: Sequence[str], rows: Sequence[Sequence[str]]
    ) -> None:
        widths = [
            max(len(str(row[i])) for row in [headers, *rows])
            for i in range(len(headers))
        ]
        border = "+" + "+".join("-" * (w + 2) for w in widths) + "+"

        def line(cells: Sequence[str]) -> str:
            padded = (f" {cell:<{w}} " for cell, w in zip(cells, widths))
            return "|" + "|".join(padded) + "|"

        self._print(border)
        self._print(line(headers))
        self._print(border)
        for row in rows:
            self._print(line(row))
        self._print(border)
