import json
import pathlib
import sys
from typing import Any, Dict, List, Literal, Optional, Set, get_args

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from src.verify import PROVIDERS_TYPE, parse_provider, ALL_PROVIDERS
import config


def print_err(s):
    print(s, file=sys.stderr)


CONFIDENCE_LEVELS_TYPE = Literal["NONE", "LOW", "MEDIUM", "HIGH"]
CONFIDENCE_LEVELS: Set[CONFIDENCE_LEVELS_TYPE] = set(get_args(CONFIDENCE_LEVELS_TYPE))


LLM_API_KEY = config.LLM_API_KEY
LLM_BASE_URL = config.LLM_BASE_URL

if not LLM_BASE_URL:
    raise RuntimeError("LLM_BASE_URL must be defined in config.py")

client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)


def parse_confidence(confidence: str | None) -> CONFIDENCE_LEVELS_TYPE | None:
    if confidence in CONFIDENCE_LEVELS:
        return confidence
    return None


def shallow_extract_json(text: str) -> Optional[str]:
    """
    Note: Returned JSON may not be valid.
    """
    end_index = None
    for i, ch in reversed(list(enumerate(text))):
        if ch == "}":
            if end_index is None:
                end_index = i
        elif ch == "{":
            if end_index is not None:
                return text[i : end_index + 1]
    return None


class ClassificationResponse:
    confidence: CONFIDENCE_LEVELS_TYPE | None = None
    provider: PROVIDERS_TYPE | None = None
    line: str

    def __init__(self, line: str, response_content: str | None):
        self.line = line
        if response_content == None:
            return
        response_json = shallow_extract_json(response_content)
        if response_json == None:
            return
        try:
            json_object: Dict[str, Any] = json.loads(response_json)
            self.confidence = parse_confidence(json_object.get("confidence", None))
            self.provider = parse_provider(json_object.get("provider", None))
        except Exception as exception:
            print_err(f"ClassificationResponse exception: {exception}")
            print_err(f"Response Content: {response_content}")
            print_err(f"Response JSON: {response_json}")


PROMPT_PATH = pathlib.Path(__file__).resolve().parent.parent / "prompt.txt"


def get_prompt(line: str) -> List[ChatCompletionMessageParam]:
    providers_string = ", ".join(ALL_PROVIDERS)
    system_template = PROMPT_PATH.read_text(encoding="utf-8")
    system = system_template.replace("{providers_string}", providers_string)
    user = f"Analyze the following variable:\n{line}\n"
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def classify_single_line(
    line: str,
    model: str,
) -> ClassificationResponse:
    messages = get_prompt(line)

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0,
        max_tokens=2000,
    )

    response_content = response.choices[0].message.content

    return ClassificationResponse(line, response_content)


def classify_lines(
    lines: List[str],
    model: str,
) -> List[ClassificationResponse]:
    results: List[ClassificationResponse] = []
    for line in lines:
        results.append(classify_single_line(line, model))
    return results
