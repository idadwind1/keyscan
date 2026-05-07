import re
from typing import List


def preprocess_dotenv(text: str) -> List[str]:
    """
    Split into lines, strip whitespace, remove # and // comments, drop empty lines.

    TODO: Normalize based on file_type (Possible?)
    """
    candidate_lines: List[str] = []

    for line in text.splitlines():
        line = line.strip()
        if line.startswith("#") or line.startswith("//") or len(line) <= 0:
            continue
        candidate_lines.append(line)

    return candidate_lines


def get_dotenv_value(text: str) -> str | None:
    # Gets everything after the first "="
    match = re.match(r"^[^=]+=(.+)$", text)
    if match == None:
        return None
    value = match.group(1)
    if value == None:
        return None
    value = value.strip()
    # Strip surrounding quotes if any
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        value = value[1:-1]
    if value == "":
        return None
    return value
