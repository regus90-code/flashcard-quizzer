"""Command-line interface: parses flags and wires the components together."""

import argparse
import os
import random
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Optional, TextIO

from data_loader import FlashcardLoadError, load_flashcards
from history import HistoryStore, deck_key, default_history_path
from models import CardHistory, Flashcard
from quiz_engine import AVAILABLE_MODES, QuizSession, create_quiz_mode
from ui import ConsoleUI
from utils.file_handler import JsonFileError, write_json


def build_parser() -> argparse.ArgumentParser:
    """Define all command-line flags."""
    parser = argparse.ArgumentParser(
        prog="python main.py",
        description="Quiz yourself on flashcards stored in a JSON file.",
        epilog="Example: python main.py -m adaptive -f data/python_basics.json",
    )
    parser.add_argument(
        "-f",
        "--file",
        required=True,
        help='JSON deck: a list of {"front", "back"} objects or {"cards": [...]}',
    )
    parser.add_argument(
        "-m",
        "--mode",
        choices=AVAILABLE_MODES,
        default="sequential",
        help="card order: sequential (1..N), random (shuffled) or adaptive "
        "(previously missed cards first, missed cards repeat) "
        "(default: %(default)s)",
    )
    parser.add_argument(
        "-n",
        "--limit",
        type=_positive_int,
        help="stop after this many questions",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="show all-time statistics for the deck instead of starting a quiz",
    )
    parser.add_argument(
        "--export",
        metavar="PATH",
        help="save the session summary as JSON to PATH",
    )
    parser.add_argument(
        "--history-file",
        metavar="PATH",
        default=str(default_history_path()),
        help="where results are stored between sessions (default: %(default)s)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="random seed for a repeatable order in random mode",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="disable colored output (also honors the NO_COLOR variable)",
    )
    return parser


def _positive_int(value: str) -> int:
    """argparse type for integers >= 1."""
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{value}' is not a whole number") from None
    if number < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return number


def run_quiz(session: QuizSession, ui: ConsoleUI) -> None:
    """Ask cards until the session ends or the user quits (exit/Ctrl+C)."""
    number = 0
    try:
        while (card := session.next_card()) is not None:
            number += 1
            answer = ui.ask(card, number)
            if answer is None:
                ui.show_quit()
                return
            ui.show_feedback(session.submit_answer(card, answer), card)
    except KeyboardInterrupt:
        ui.show_quit()


def main(
    argv: Optional[Sequence[str]] = None,
    input_func: Callable[[str], str] = input,
    output: Optional[TextIO] = None,
    error_output: Optional[TextIO] = None,
) -> int:
    """Run the application and return the process exit code.

    Returns:
        0 on success, 1 if the deck or the export file cannot be used.
    """
    args = build_parser().parse_args(argv)
    use_color = not args.no_color and "NO_COLOR" not in os.environ
    ui = ConsoleUI(input_func, output, error_output, use_color=use_color)

    try:
        cards = load_flashcards(args.file)
    except FlashcardLoadError as error:
        ui.show_error(str(error))
        return 1

    store = HistoryStore(args.history_file)
    deck = deck_key(args.file)
    try:
        history = store.load(deck)
    except JsonFileError as error:
        ui.show_warning(f"{error}. Starting without past results.")
        history = {}

    if args.stats:
        ui.show_history(cards, history)
        return 0

    return _play(args, cards, history, store, deck, ui)


def _play(
    args: argparse.Namespace,
    cards: list[Flashcard],
    history: dict[str, CardHistory],
    store: HistoryStore,
    deck: str,
    ui: ConsoleUI,
) -> int:
    """Run one quiz session, then save history and the optional export."""
    mode = create_quiz_mode(
        args.mode, cards, history=history, rng=random.Random(args.seed)
    )
    session = QuizSession(mode, limit=args.limit)

    ui.show_welcome(Path(args.file).name, args.mode, len(cards))
    run_quiz(session, ui)
    ui.show_summary(session.stats)

    if session.stats.total:
        try:
            store.record(deck, session.stats.results)
        except JsonFileError as error:
            ui.show_warning(f"Results were not saved: {error}")

    if args.export:
        try:
            write_json(args.export, session.stats.to_dict())
        except JsonFileError as error:
            ui.show_error(str(error))
            return 1
        ui.show_info(f"Summary exported to {args.export}")
    return 0
