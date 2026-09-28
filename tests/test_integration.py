"""End-to-end tests: run the CLI with a simulated user."""

import io
import json
import runpy
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

from cli import main
from tests.conftest import scripted_input, squash

DECK = [
    {"front": "DNS", "back": "Domain Name System"},
    {"front": "SSH", "back": "Secure Shell"},
    {"front": "VPN", "back": "Virtual Private Network"},
]


@pytest.fixture
def deck(write_json_file: Callable[..., Path]) -> Path:
    return write_json_file(DECK)


@pytest.fixture
def history_file(tmp_path: Path) -> Path:
    return tmp_path / "history.json"


def run_cli(
    args: list[str], answers: list[str], history_file: Path
) -> tuple[int, str, str]:
    """Run the app like a user would; return (exit code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    code = main(
        [*args, "--no-color", "--history-file", str(history_file)],
        input_func=scripted_input(answers),
        output=out,
        error_output=err,
    )
    return code, out.getvalue(), err.getvalue()


def test_full_session(deck: Path, history_file: Path, tmp_path: Path) -> None:
    """A user answers 3 questions (2 right, 1 wrong); check the final stats."""
    export = tmp_path / "summary.json"

    code, out, err = run_cli(
        ["-f", str(deck), "-m", "sequential", "--export", str(export)],
        ["domain name system", "Secure Socket", "VIRTUAL PRIVATE NETWORK"],
        history_file,
    )

    assert code == 0
    assert err == ""
    assert out.count("Correct!") == 2
    assert "Incorrect. Answer: Secure Shell" in out
    assert "| Total Questions | 3 |" in squash(out)
    assert "| Accuracy | 66.7% |" in squash(out)
    assert "  - SSH -> Secure Shell" in out
    assert json.loads(export.read_text(encoding="utf-8")) == {
        "total_questions": 3,
        "correct": 2,
        "accuracy_percent": 66.7,
        "missed": [{"front": "SSH", "back": "Secure Shell"}],
    }


def test_exit_command_ends_quiz_with_summary(deck: Path, history_file: Path) -> None:
    code, out, _ = run_cli(
        ["-f", str(deck)], ["Domain Name System", "exit"], history_file
    )

    assert code == 0
    assert "Quiz ended early." in out
    assert "| Total Questions | 1 |" in squash(out)
    assert "No missed terms. Well done!" in out


def test_ctrl_c_ends_quiz_gracefully(deck: Path, history_file: Path) -> None:
    def interrupted(prompt: str) -> str:
        raise KeyboardInterrupt

    out = io.StringIO()
    code = main(
        ["-f", str(deck), "--no-color", "--history-file", str(history_file)],
        input_func=interrupted,
        output=out,
        error_output=io.StringIO(),
    )

    assert code == 0
    assert "Quiz ended early." in out.getvalue()
    assert "| Total Questions | 0 |" in squash(out.getvalue())
    assert not history_file.exists()  # nothing answered, nothing saved


def test_end_of_input_ends_quiz(deck: Path, history_file: Path) -> None:
    code, out, _ = run_cli(["-f", str(deck)], [], history_file)

    assert code == 0
    assert "Quiz ended early." in out


def test_missing_file_prints_friendly_error(tmp_path: Path, history_file: Path) -> None:
    code, out, err = run_cli(["-f", str(tmp_path / "missing.json")], [], history_file)

    assert code == 1
    assert out == ""
    assert err.startswith("Error: File not found")
    assert "Traceback" not in err


def test_malformed_deck_prints_friendly_error(
    write_json_file: Callable[..., Path], history_file: Path
) -> None:
    deck = write_json_file({"cards": [{"front": "DNS"}]})

    code, _, err = run_cli(["-f", str(deck)], [], history_file)

    assert code == 1
    assert 'missing the required field "back"' in err


def test_adaptive_mode_uses_history_from_previous_session(
    deck: Path, history_file: Path
) -> None:
    run_cli(
        ["-f", str(deck)],
        ["Domain Name System", "wrong", "Virtual Private Network"],
        history_file,
    )

    _, out, _ = run_cli(
        ["-f", str(deck), "-m", "adaptive", "-n", "1"], ["exit"], history_file
    )

    assert "Q1: SSH" in out


def test_stats_flag_shows_all_time_results(deck: Path, history_file: Path) -> None:
    run_cli(["-f", str(deck)], ["Domain Name System", "wrong", "exit"], history_file)
    run_cli(["-f", str(deck)], ["Domain Name System", "exit"], history_file)

    code, out, _ = run_cli(["-f", str(deck), "--stats"], [], history_file)

    assert code == 0
    assert "| DNS | 2 | 0 | 100% |" in squash(out)
    assert "| SSH | 0 | 1 | 0% |" in squash(out)
    assert "| VPN | 0 | 0 | - |" in squash(out)


def test_stats_flag_without_history(deck: Path, history_file: Path) -> None:
    code, out, _ = run_cli(["-f", str(deck), "--stats"], [], history_file)

    assert code == 0
    assert "No answers recorded for this deck yet" in out


def test_corrupt_history_file_only_warns(deck: Path, history_file: Path) -> None:
    history_file.write_text(
        json.dumps({"decks": {str(deck.resolve()): {"DNS": 5}}}), encoding="utf-8"
    )

    code, out, err = run_cli(
        ["-f", str(deck)], ["Domain Name System", "exit"], history_file
    )

    assert code == 0
    assert "Starting without past results" in err
    assert "Results were not saved" in err
    assert "| Total Questions | 1 |" in squash(out)


def test_export_failure_returns_error_code(
    deck: Path, history_file: Path, tmp_path: Path
) -> None:
    blocker = tmp_path / "not_a_folder"
    blocker.write_text("", encoding="utf-8")

    code, _, err = run_cli(
        ["-f", str(deck), "--export", str(blocker / "summary.json")],
        ["exit"],
        history_file,
    )

    assert code == 1
    assert "Could not write" in err


@pytest.mark.parametrize("limit", ["0", "-3", "two"])
def test_invalid_limit_is_rejected_by_argparse(
    deck: Path, history_file: Path, limit: str
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        run_cli(["-f", str(deck), "-n", limit], [], history_file)

    assert exc_info.value.code == 2


def test_colors_are_used_unless_disabled(
    deck: Path, history_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("NO_COLOR", raising=False)
    out = io.StringIO()

    main(
        ["-f", str(deck), "--history-file", str(history_file)],
        input_func=scripted_input(["Domain Name System", "wrong", "exit"]),
        output=out,
        error_output=io.StringIO(),
    )

    assert "\x1b[32mCorrect!" in out.getvalue()  # green
    assert "\x1b[31mIncorrect." in out.getvalue()  # red


def test_no_color_environment_variable(
    deck: Path, history_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("NO_COLOR", "1")
    out = io.StringIO()

    main(
        ["-f", str(deck), "--history-file", str(history_file)],
        input_func=scripted_input(["exit"]),
        output=out,
        error_output=io.StringIO(),
    )

    assert "\x1b[" not in out.getvalue()


def test_main_script_shows_help(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["main.py", "--help"])

    with pytest.raises(SystemExit) as exc_info:
        runpy.run_path("main.py", run_name="__main__")

    assert exc_info.value.code == 0
    help_text = capsys.readouterr().out
    for flag in ("--file", "--mode", "--limit", "--stats", "--export", "--seed"):
        assert flag in help_text
