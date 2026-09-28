# AI Edit Log

All code was generated with **Claude Code** and reviewed against
[ai_guidance/code_review_checklist.md](../ai_guidance/code_review_checklist.md)
using three kinds of checks: the automated tools (flake8, mypy `--strict`,
black, isort), running the application by hand, and the pytest suite. Each
entry below is a real finding from that review and describes what was changed
and why. The prompts themselves are in [prompts.md](../prompts.md).

---

### 2026-09-28 - 1. Starter repository could not be checked out on Windows

**Context:** Setup: getting the starter code from
`udacity/cd14602-project-starter`.

**AI Tool Used:** Claude Code

**Prompt/Request:** "Get the starter code from the repository (folder
`project/starter`) into a new folder `flashcard-quizzer`."

**AI Response:** The first attempt was a plain `git clone`. It failed: the
repository contains files such as `CLAUDE.md:Zone.Identifier` (Windows
download metadata that was committed by accident), and `:` is not allowed in
Windows file names. A sparse checkout of only `project/` failed for the same
reason, because `project/starter` has these files too.

**Changes Made:** Rejected both approaches. The files were instead extracted
one by one with `git show HEAD:<path>`, skipping every `*:Zone.Identifier`
entry.

**Reasoning:** The `Zone.Identifier` files have no content that matters for
the project; the real files are all intact.

**Outcome:** Complete starter code without the invalid files.

**Lessons Learned:** An agent's first "obvious" command can fail for
platform-specific reasons. Reading the error message closely was enough to
find a targeted workaround instead of retrying the same thing.

---

### 2026-09-28 - 2. Linters rejected the first draft (flake8 + mypy strict)

**Context:** Quality gate after generating the data layer, quiz engine, UI and
CLI.

**AI Tool Used:** Claude Code

**Prompt/Request:** "Run flake8 and mypy and fix every finding."

**AI Response:** The first draft passed the manual read-through, but the tools
found 6 problems:
- 3 × `E501 line too long`: user-facing error messages were written as single
  f-strings of up to 93 characters. black does not split string literals, so
  formatting alone could not fix them.
- `cli.py`: the parameter `cards: list` had no element type. With a bare
  `list`, mypy cannot check what is stored in it, so this silently weakens the
  "all functions typed" requirement.
- Missing type stubs for `colorama` (`import-untyped`).
- `tests/__init__.py` from the starter had no final newline (W292).

**Changes Made:** Split the long messages into implicitly concatenated
strings, changed the annotation to `list[Flashcard]`, added
`types-colorama` to `requirements.txt`, fixed the newline.

**Reasoning:** The rubric demands PEP 8 and type hints on all functions.
Suppressing the warnings (`# noqa`, `# type: ignore`) would hide the problem
instead of fixing it.

**Outcome:** `flake8 .` and `mypy .` (strict) report no issues.

**Lessons Learned:** AI-generated code that *looks* clean still needs the
automated tools. Strict mypy caught an annotation that a human reviewer would
likely accept.

---

### 2026-09-28 - 3. Corrupt history file caused a traceback (bug + incomplete first fix)

**Context:** Reviewing `history.py` against the requirement "crash gracefully
with a helpful error message, not a stack trace".

**AI Tool Used:** Claude Code

**Prompt/Request:** "Check the error handling of `HistoryStore` for malformed
history files."

**AI Response:** The generated `load()` called `counts.get(...)` and `int(...)`
on each entry without checking its type. A history file containing
`{"DNS": 5}` instead of `{"DNS": {"correct": 1, "incorrect": 0}}` raised an
`AttributeError` with a full traceback. The AI's first fix validated the
entries in `load()` only.

**Changes Made:** The first fix was **rejected as incomplete**. Following the
code path showed a second problem: `cli.py` catches the error from `load()`,
prints a warning and continues the quiz. At the end it calls `record()`, which
read the same corrupt file with its own unchecked code and crashed with a
`TypeError`. `record()` was rewritten to reuse the validated `load()`, so both
paths share one validation.

**Reasoning:** A fix is only complete when every code path that touches the
bad data is covered. Duplicated parsing logic was the root cause.

**Outcome:** A corrupt history file now produces two warnings ("Starting
without past results", "Results were not saved") and the quiz still works.
`test_corrupt_history_file_only_warns`, five parametrized cases in
`test_corrupt_history_raises_readable_error`, and
`test_record_refuses_to_overwrite_corrupt_history` keep it that way.

**Lessons Learned:** Ask "what happens next?" after an error is handled. The
first fix looked right in isolation.

---

### 2026-09-28 - 4. Adaptive mode treated never-seen cards like mastered ones

**Context:** Manual run of two adaptive sessions in a row
(`-m adaptive -f data/glossary.json`).

**AI Tool Used:** Claude Code

**Prompt/Request:** "Adaptive must prioritize cards the user got wrong: order
by past miss rate from a history."

**AI Response:** The generated code sorted cards by `-miss_rate`. It passed a
unit test and put the missed card (HTTP) first, as required.

**Changes Made:** Running the app showed a weakness no test had caught: after
HTTP came DNS and SSH, which had been answered *correctly* before, and only
then the cards that had never been practiced. The cause: an unseen card has
0 attempts and therefore a miss rate of 0, the same as a mastered card. The
sort key was changed to `(-miss_rate, attempts > 0)`, so the order is
*missed → new → mastered*, and a test was added
(`test_adaptive_mode_puts_new_cards_before_mastered_ones`).

**Reasoning:** The feature exists to help users learn. Showing known cards
before unknown ones works against that goal, even though it technically meets
the literal requirement.

**Outcome:** Correct priority order, documented in the `AdaptiveMode`
docstring and the README.

**Lessons Learned:** The AI implemented the literal prompt. Checking whether
the behavior makes sense for the user needed a real run, not just a passing
test.

---

### 2026-09-28 - 5. Brittle table assertions in the generated tests

**Context:** First run of the test suite (88 passed, 2 failed).

**AI Tool Used:** Claude Code

**Prompt/Request:** "Write a pytest suite ... `test_full_session` should
simulate a user answering 3 questions and check the final stats."

**AI Response:** The tests compared table rows including their exact padding,
e.g. `"| Total Questions | 1     |"`. When the accuracy was `100.0%` the value
column became one character wider, the padding changed, and two tests failed
although the output was correct.

**Changes Made:** Rejected the approach of adjusting the expected spaces (that
would break again with the next value). Added a `squash()` helper that
collapses whitespace, so tests check `"| Total Questions | 1 |"`. The helper
was first generated twice (in two test files) and was then moved to
`conftest.py`.

**Reasoning:** A test should fail when behavior is wrong, not when layout
details change.

**Outcome:** 91 of 91 tests pass; the assertions still check label and value
together.

**Lessons Learned:** AI-generated tests can be too literal. A failing test must
first be classified: bug in the code, or bug in the test? Here it was the test.

---

### 2026-09-28 - 6. isort modified files that are not part of the project

**Context:** Running `isort .` as part of the quality gate.

**AI Tool Used:** Claude Code

**Prompt/Request:** "Run isort, black, flake8, mypy and pytest."

**AI Response:** isort reported "Fixing" four files in `.claude/commands/`.
These are starter helper scripts without a `.py` extension that isort detected
as Python by their shebang line.

**Changes Made:** Compared the files with the originals (`git show`): only the
import order had changed. The originals were restored and `.claude` was
excluded via `extend_skip` in `pyproject.toml`.

**Reasoning:** Tools configured for "the whole folder" should not rewrite
provided files the project does not own. The change was harmless, but an
unreviewed change to someone else's files is still an unreviewed change.

**Outcome:** `isort --check-only .` is clean and the starter scripts are
untouched.

**Lessons Learned:** Check the output of automated fixers too. "Fixing" does
not mean the change was wanted.

---

### 2026-09-28 - 7. Removing the unused starter demo code

**Context:** The starter contains a `TaskManager` demo and a `FileHandler`
class that silently returns `{}` for missing files.

**AI Tool Used:** Claude Code

**Prompt/Request:** "Put the low-level JSON reading in
`utils/file_handler.py` so I/O errors are translated in one place."

**AI Response:** New `read_json`/`write_json` functions with a
`JsonFileError` that carries a readable message (missing file, folder instead
of file, permission, encoding, JSON position), plus atomic writes.

**Changes Made:** The starter `FileHandler` was **not** reused: returning `{}`
for a missing file directly contradicts the requirement that a missing deck
must produce an error. It also created the `data/` folder as a side effect of
its constructor. `task_manager.py` and both starter test files were removed
because nothing in the quiz uses them. The folder structure (`utils/`,
`tests/`, `docs/`, `data/`) was kept as required.

**Reasoning:** Dead code costs maintenance time and would lower the coverage
figure without adding value.

**Outcome:** `utils/file_handler.py` is used by both the deck loader and the
history store and has 98 % coverage (the missing line is a branch that only
occurs on Linux/macOS).

**Lessons Learned:** Starter code is a suggestion, not a constraint. It has to
pass the same review as generated code.

---

### 2026-09-28 - 8. Readability of a generated test

**Context:** Review of `test_adaptive_mode_behavior`.

**AI Tool Used:** Claude Code

**Prompt/Request:** "`test_adaptive_mode_behavior`: does it actually repeat
incorrect questions?"

**AI Response:** Correct test, but the answer logic was one line:
`correct=card.front != "DNS" or asked.count("DNS") > 1`.

**Changes Made:** Replaced it with a named variable
`first_dns_attempt = card.front == "DNS" and asked.count("DNS") == 1` and
`correct=not first_dns_attempt`.

**Reasoning:** A test documents the expected behavior; it should be readable
at a glance.

**Outcome:** Same assertion (`["DNS", "SSH", "VPN", "DNS"]`), clearer intent.

**Lessons Learned:** Review tests with the same care as production code.

---

## Reflection

1. **Where did AI help most?** Boilerplate-heavy parts: argparse setup,
   dataclasses, the table printer and parametrized test cases.
2. **Where were the most modifications needed?** Error paths (entry 3) and
   behavior that is technically correct but unhelpful (entry 4). Neither shows
   up when reading the code once.
3. **Patterns in strengths and weaknesses:** The AI follows explicit
   instructions reliably (required test names, patterns, flags). Weak spots
   were consequences across modules (entry 3) and overly literal tests
   (entry 5).
4. **How prompting improved:** Prompts got better when they named the concrete
   check ("run flake8 and mypy and fix every finding") instead of a general
   goal ("make it clean").
5. **Next time:** Start with a manual run before writing tests. Entry 4 was
   only found by using the application.

## Summary Statistics

- **Total AI interactions:** 10 step prompts (see `prompts.md`) plus the
  review-and-fix rounds documented above
- **Lines of AI-generated code used:** about 1,650 (832 application, 825 tests)
- **Lines of AI-generated code modified after review:** about 60
- **Most helpful AI interaction:** the Strategy/Factory implementation in
  `quiz_engine.py`, used almost unchanged
- **Most challenging AI interaction:** the corrupt-history bug (entry 3),
  because the first fix was incomplete
- **Biggest lesson learned:** Passing tests show that the code does what the
  tests check. Only running the application shows whether it does what the
  user needs.
