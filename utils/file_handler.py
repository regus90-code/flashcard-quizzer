"""JSON file helpers that turn low-level I/O failures into readable errors."""

import json
import os
import tempfile
from pathlib import Path
from typing import Any


class JsonFileError(Exception):
    """Raised when a JSON file cannot be read or written.

    The message is meant to be shown to the user as-is.
    """


def read_json(path: str | Path) -> Any:
    """Read and parse a UTF-8 JSON file.

    Args:
        path: Location of the JSON file.

    Returns:
        The parsed JSON value.

    Raises:
        JsonFileError: If the file is missing, unreadable or not valid JSON.
    """
    file_path = Path(path)
    try:
        text = file_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise JsonFileError(f"File not found: {file_path}") from None
    except IsADirectoryError:
        raise JsonFileError(f"Expected a file but got a folder: {file_path}") from None
    except PermissionError:
        raise JsonFileError(f"Permission denied when reading: {file_path}") from None
    except UnicodeDecodeError:
        raise JsonFileError(f"File is not valid UTF-8 text: {file_path}") from None
    except OSError as error:
        raise JsonFileError(f"Could not read {file_path}: {error.strerror}") from None

    try:
        return json.loads(text)
    except json.JSONDecodeError as error:
        raise JsonFileError(
            f"Invalid JSON in {file_path} (line {error.lineno}, "
            f"column {error.colno}): {error.msg}"
        ) from None


def write_json(path: str | Path, data: Any) -> None:
    """Write ``data`` as pretty-printed UTF-8 JSON, creating parent folders.

    The data goes to a temporary file first, which then replaces the target,
    so an interrupted write never leaves a half-written file behind.

    Args:
        path: Destination file.
        data: JSON-serializable value.

    Raises:
        JsonFileError: If the data is not JSON-serializable or the file
            cannot be written.
    """
    file_path = Path(path)
    try:
        payload = json.dumps(data, indent=2, ensure_ascii=False)
    except (TypeError, ValueError) as error:
        raise JsonFileError(f"Data cannot be saved as JSON: {error}") from None

    temp_name = None
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(dir=file_path.parent, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as temp_file:
            temp_file.write(payload + "\n")
        os.replace(temp_name, file_path)
    except OSError as error:
        if temp_name is not None and os.path.exists(temp_name):
            os.remove(temp_name)
        raise JsonFileError(f"Could not write {file_path}: {error.strerror}") from None
