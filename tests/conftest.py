"""Shared fixtures for the test suite."""

import json
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

import pytest

from models import Flashcard


@pytest.fixture
def cards() -> list[Flashcard]:
    """Three simple cards in a known order."""
    return [
        Flashcard("DNS", "Domain Name System"),
        Flashcard("SSH", "Secure Shell"),
        Flashcard("VPN", "Virtual Private Network"),
    ]


@pytest.fixture
def write_json_file(tmp_path: Path) -> Callable[[Any, str], Path]:
    """Write a value as JSON into the temp folder and return the path."""

    def write(data: Any, name: str = "deck.json") -> Path:
        path = tmp_path / name
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    return write


def scripted_input(answers: Iterable[str]) -> Callable[[str], str]:
    """Simulate a user typing ``answers`` one by one, then closing input."""
    remaining = iter(answers)

    def fake_input(prompt: str) -> str:
        try:
            return next(remaining)
        except StopIteration:
            raise EOFError from None

    return fake_input


def squash(text: str) -> str:
    """Collapse runs of whitespace so table assertions ignore column padding."""
    return " ".join(text.split())
