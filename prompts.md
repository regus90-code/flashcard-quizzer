# Prompt Log

Tool: **Claude Code** (terminal agent, model Claude Opus 5.5), one session on
2026-09-28, Windows 11, Python 3.12.

The project was driven by one high-level request that contained the complete
project specification and rubric. Following the workflow
*Decompose → Generate → Review → Refine → Verify*, the specification was
broken into the step prompts below and executed in this order. The review
findings for each step, and what was changed because of them, are documented
in [docs/ai_edit_log.md](docs/ai_edit_log.md).

## 0. Initial request

> Here are the project requirements [full specification, starter repository
> link and rubric pasted]. Do everything that is necessary, the same way as in
> the previous project.

## 1. Setup

> Get the starter code from https://github.com/udacity/cd14602-project-starter
> (folder `project/starter`) into a new folder `flashcard-quizzer`. Create a
> `venv` with Python 3.12 and install pytest, pytest-cov, black, isort, flake8
> and mypy with pinned versions. Use only pip, no Poetry or Pipenv.

## 2. Data layer (Phase 1)

> Create `models.py` with a frozen `Flashcard` dataclass (`front`, `back`) and a
> `matches(answer)` method that compares case-insensitively and ignores extra
> whitespace. Create `data_loader.py` with `load_flashcards(path)` that accepts
> both `[{"front", "back"}]` and `{"cards": [...]}`. Validate the structure and
> raise a custom `FlashcardLoadError` with a one-line, user-facing message
> (file name, card number, field name) for missing files, invalid JSON, empty
> decks, non-object cards and missing or empty fields. Put the low-level JSON
> reading in `utils/file_handler.py` so I/O errors are translated in one place.
> Full type hints and docstrings everywhere.

## 3. Quiz engine (Phase 2)

> In `quiz_engine.py`, implement the Strategy pattern: an abstract `QuizMode`
> with `next_card() -> Flashcard | None` and a `record_result(card, correct)`
> hook, and three subclasses `SequentialMode`, `RandomMode` (injectable
> `random.Random` for reproducible tests) and `AdaptiveMode`. Adaptive must
> prioritize cards the user got wrong: order by past miss rate from a history,
> and re-ask a missed card a few questions later, with a cap so the quiz always
> ends. Add a factory `create_quiz_mode(name, cards, history, rng)` and a
> `QuizSession` class that counts score without doing any input/output.

## 4. Persistence

> Add `history.py` with a `HistoryStore` that saves correct/incorrect counts per
> card and deck in a JSON file in the user's home folder, so the adaptive mode
> can use results from previous sessions. Writes must be atomic (temp file +
> replace).

## 5. CLI and UI (Phase 3)

> Create `ui.py` with a `ConsoleUI` class whose input function and output
> streams are injectable for tests. Show green "Correct!" and red "Incorrect"
> using colorama, a summary table (Total Questions, Correct, Accuracy %) and
> the list of missed terms. Typing `exit`/`quit`, end of input and Ctrl+C must
> end the quiz gracefully and still show the summary. Create `cli.py` with
> argparse flags `-f/--file`, `-m/--mode`, `-n/--limit`, `--stats`,
> `--export`, `--history-file`, `--seed`, `--no-color`; `main.py` only calls
> `cli.main()` and exits with its return code (0 success, 1 load/export error).

## 6. Quality gate

> Configure black, isort, flake8 (max line length 88) and mypy in strict mode
> in `pyproject.toml`/`.flake8`, excluding `venv`. Run flake8 and mypy and fix
> every finding. Then run the app manually: `--help`, a sequential quiz, a
> missing file, broken JSON, a card without "back", two adaptive sessions in a
> row, `--stats` and `--export`.

## 7. Tests

> Write a pytest suite in `tests/`. Required tests:
> `test_flashcard_loader.py` with `test_load_valid_flashcards_array`,
> `test_load_invalid_json`, `test_load_missing_required_field`;
> `test_quiz_modes.py` with `test_quiz_mode_factory` and
> `test_adaptive_mode_behavior`; `test_integration.py` with `test_full_session`
> (simulate a user answering 3 questions and check the final stats). Add edge
> cases and error conditions (malformed structures, corrupt history, Ctrl+C,
> export failure, invalid `--limit`). Use descriptive test names, no real
> terminal input, temporary folders only. Target > 90 % coverage.

## 8. Refinement

> The two table assertions fail when a column gets wider; make table checks
> independent of padding and put the shared helper in `conftest.py`. Remove
> the unused `__main__` block from `cli.py`. isort rewrote the starter scripts
> in `.claude/commands/`: restore them and exclude that folder.

## 9. Documentation

> Update `README.md` (setup for Windows and macOS/Linux, usage examples, flag
> table, deck format, architecture diagram, test overview). Fill in
> `docs/ai_edit_log.md` with at least 5 concrete review findings and write the
> final report from `docs/report_template.md` (1000–1500 words). Save the
> coverage report as `docs/coverage_report.txt`.
