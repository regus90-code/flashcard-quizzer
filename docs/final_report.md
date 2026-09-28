# AI-Assisted Development Project Report

**Student Name:** Peter Essel
**Project Title:** Flashcard Quizzer – a CLI quiz tool built with Claude Code
**Date:** 2026-09-28

## Executive Summary

The Flashcard Quizzer is a small terminal app for learning terms like server
acronyms. It reads a deck from a JSON file, asks the cards one by one, checks
the answer (case-insensitive), shows green or red feedback and ends with a
summary of accuracy and missed terms.

I didn't write the code myself. Claude Code did. My job was to split the
specification into prompts, check what came back and send the agent back when
something was off. That turned out to be more work than I expected, and also
the most interesting part.

## Project Overview

### Problem Statement
New hires need a quick way to memorize internal acronyms. The tool should run
in the terminal, load decks from JSON, offer a few quiz modes and stay clean
enough that someone can extend it later.

### Solution Approach
I split the app into small modules: `data_loader.py` for loading and
validation, `quiz_engine.py` for the quiz logic, `ui.py` for terminal output,
`history.py` for saved results and `cli.py` for the command-line flags. The
quiz logic never reads from the keyboard directly, which made testing much
easier later on.

### Final Features
- [x] Decks as a plain list or as `{"cards": [...]}`, with validation
- [x] Short, readable error messages instead of tracebacks
- [x] Sequential, random and adaptive modes
- [x] Summary table with accuracy and missed terms
- [x] Results saved between sessions, viewable with `--stats`
- [x] `--export`, `-n` (question limit), `--seed` and `--no-color`

## AI Collaboration Experience

### AI Tools Used
- [x] Claude (Claude Code in the terminal)

### Collaboration Workflow
I followed the course loop: decompose, generate, review, refine, verify. The
spec became ten prompts (all in `prompts.md`), each with file names, class
names and the exact test names the rubric asks for. After every step I ran
flake8, mypy and black, played the quiz myself and checked the result against
the review checklist. When something was wrong, I described the symptom and
let the agent fix it instead of editing the code by hand.

### Most Valuable AI Interactions

#### Example 1: The adaptive order
**Context:** I played two adaptive rounds in a row.
**AI Prompt:** "Order the cards by past miss rate."
**AI Response:** It sorted by miss rate, worst first.
**Your Changes:** New cards also have a miss rate of 0, just like cards I
already knew, so known cards sometimes came before new ones. I asked for the
order missed → new → mastered.
**Outcome:** The mode now does what it's supposed to do, and there's a test
for it.

#### Example 2: The broken history file
**Context:** Reviewing the error handling in `history.py`.
**AI Prompt:** "Check how `HistoryStore` handles a malformed history file."
**AI Response:** It added validation to `load()`.
**Your Changes:** I didn't accept that. After the warning the app keeps going
and later calls `record()`, which crashed on the same file. Both methods now
use the same check.
**Outcome:** A corrupt file only gives a warning.

### Challenges with AI Collaboration
The agent fixed exactly the spot I pointed at, but not the second place that
used the same data. It also took my wording very literally, edge cases
included. Some generated tests compared whole table strings and broke as soon
as a number got one digit wider. And on Windows, the starter repo had file
names that couldn't even be checked out.

## Software Engineering Practices

### Code Quality Measures
- [x] Formatting with black and isort
- [x] flake8 and mypy (strict) without errors
- [x] Type hints and docstrings everywhere
- [x] Custom exceptions (`FlashcardLoadError`, `JsonFileError`)

### Testing Strategy
There are 91 pytest tests with 99 % coverage. They include twelve kinds of
broken decks, corrupt history files and full runs with a simulated user,
including Ctrl+C. I wrote the tests after the first manual run, and that run
found the adaptive bug, not the tests.

### Design Patterns Used
**Strategy:** `QuizMode` with `SequentialMode`, `RandomMode` and
`AdaptiveMode`. All three answer the same question ("which card comes
next?") in different ways, so this pattern fits naturally. **Factory:**
`create_quiz_mode()` turns the `--mode` flag into the right object. A
spaced-repetition mode would be one new class and one line in the factory.

### Code Structure and Organization
I kept the starter's folder structure but removed its unused `TaskManager`
and `FileHandler`. The old `FileHandler` returned `{}` for a missing file,
which goes against the error-handling requirement.

## Technical Challenges and Solutions

### Challenge 1: Failing gracefully
**Problem:** Missing files, bad JSON and encoding problems all throw
different exceptions.
**Solution:** `utils/file_handler.py` turns them into one `JsonFileError`
with a readable message, including line and column for JSON errors.
**AI Involvement:** Generated by the AI; I added the history-file case in
review.
**Lessons Learned:** One place for error messages keeps them consistent.

### Challenge 2: Testing an interactive program
**Problem:** The quiz waits for keyboard input.
**Solution:** The UI takes its input function as a parameter, so tests can
feed scripted answers.
**AI Involvement:** The agent suggested this once I asked for tests without a
real terminal.
**Lessons Learned:** It's easier to plan for testing early than to mock
things later.

## Code Quality Analysis

### Metrics
- Lines of code: 832 (application), 825 (tests)
- Test coverage: 99 %
- Functions/classes: 55 functions and methods, 13 classes
- Linting: 0 issues (flake8, mypy, black, isort)

### Self-Assessment
- **Code Readability: 5** – small modules with clear names.
- **Code Maintainability: 5** – new modes don't touch existing code.
- **Test Quality: 4** – thorough, but a manual run still found a bug.
- **Documentation: 5** – README, prompt log, edit log and this report.

## Learning Outcomes

### Technical Skills Developed
Using Strategy and Factory in a real project, strict type checking with mypy
and testing a CLI without a real terminal.

### AI Collaboration Skills
Precise prompts with names and constraints give usable code on the first
try. Vague ones don't. Reviewing means trying to break the code, not just
reading it.

### Software Engineering Insights
Keeping the quiz logic free of input and output made the integration test
almost easy.

## Reflection

### What Worked Well
Small prompts and a fixed check after every step. I'm happiest with the
adaptive mode and the error handling.

### What Could Be Improved
Next time I'd play the app earlier, before the tests are written.

### Future Enhancements
Spaced repetition, alternative answers per card and a history reset.

## Conclusion
With an AI agent my role shifted from writing code to describing and checking
it. The agent was fast and followed clear instructions well. The two real
bugs, though, I only found by using the app and asking "what happens next?".
That mix of automatic checks and actually using the program is what I'll keep
doing.

## Appendices

### Appendix A: AI Interaction Log
See `docs/ai_edit_log.md`, especially entries 3 and 4.

### Appendix B: Code Statistics
See `docs/coverage_report.txt`.
