from pathlib import Path


def read_text_file(path: Path) -> str:
    """
    Safely read a text file.
    """
    return path.read_text(encoding="utf-8", errors="ignore")


def find_line_number(content: str, search_text: str) -> int | None:
    """
    Find the first line number containing a given text.
    """
    for index, line in enumerate(content.splitlines(), start=1):
        if search_text in line:
            return index

    return None


def get_line_snippet(content: str, line_number: int | None) -> str | None:
    """
    Return a single-line snippet from file content.
    """
    if line_number is None:
        return None

    lines = content.splitlines()

    if 1 <= line_number <= len(lines):
        return lines[line_number - 1].strip()

    return None