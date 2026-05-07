"""
Contains file type specific processing functions.
"""

from typing import Callable, List, Literal, Optional, get_args

from src.file_modules.dotenv import get_dotenv_value, preprocess_dotenv


GIST_FILE_TYPE = Literal[
    "Dotenv",
    # Add more file types here.
]
ALL_FILE_TYPES = set(get_args(GIST_FILE_TYPE))


def get_preprocessing_function(file_type: GIST_FILE_TYPE) -> Callable[[str], List[str]]:
    # Add more file types below.
    if file_type == "Dotenv":
        return preprocess_dotenv
    else:
        raise Exception(
            f"get_preprocessing_function(): Unsupported file type {file_type}"
        )


def get_value_extraction_function(
    file_type: GIST_FILE_TYPE,
) -> Callable[[str], Optional[str]]:
    # Add more file types below.
    if file_type == "Dotenv":
        return get_dotenv_value
    else:
        raise Exception(
            f"get_value_extraction_function(): Unsupported file type {file_type}"
        )


def preprocess_contents(contents: List[str], file_type: GIST_FILE_TYPE) -> List[str]:
    """
    Preprocess file contents into forms suitable for key detection.
    """
    all_lines: List[str] = []
    preprocessing_function = get_preprocessing_function(file_type)
    for content in contents:
        all_lines.extend(preprocessing_function(content))
    return all_lines


def extract_verifiable_value(text: str, file_type: GIST_FILE_TYPE) -> str | None:
    """
    Extracts a value from the text that can be used for verification.
    """
    value_extraction_function = get_value_extraction_function(file_type)
    return value_extraction_function(text)
