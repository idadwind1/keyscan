from typing import Callable, Dict, Literal
import requests

from src.llm_classify import PROVIDERS_TYPE


DEFAULT_TIMEOUT_SECONDS = 5


def _http_get_status_code(url: str, headers: Dict[str, str]) -> int:
    response = requests.get(url, headers=headers, timeout=DEFAULT_TIMEOUT_SECONDS)
    return response.status_code


# Provider-specific verifiers


def verify_openai(api_key: str) -> bool:
    status = _http_get_status_code(
        "https://api.openai.com/v1/models",
        {"Authorization": f"Bearer {api_key}"},
    )
    return status == 200


def verify_anthropic(api_key: str) -> bool:
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }
    status = _http_get_status_code("https://api.anthropic.com/v1/models", headers)
    return status == 200


def verify_google(api_key: str) -> bool:
    status = _http_get_status_code(
        f"https://generativelanguage.googleapis.com/v1/models?key={api_key}",
        {},
    )
    return status == 200


def verify_xai(api_key: str) -> bool:
    status = _http_get_status_code(
        "https://api.x.ai/v1/models",
        {"Authorization": f"Bearer {api_key}"},
    )
    return status == 200


def verify_groq(api_key: str) -> bool:
    status = _http_get_status_code(
        "https://api.groq.com/openai/v1/models",
        {"Authorization": f"Bearer {api_key}"},
    )
    return status == 200


def verify_mistral(api_key: str) -> bool:
    status = _http_get_status_code(
        "https://api.mistral.ai/v1/models",
        {"Authorization": f"Bearer {api_key}"},
    )
    return status == 200


def verify_cohere(api_key: str) -> bool:
    status = _http_get_status_code(
        "https://api.cohere.ai/v1/models",
        {"Authorization": f"Bearer {api_key}"},
    )
    return status == 200


def verify_together(api_key: str) -> bool:
    status = _http_get_status_code(
        "https://api.together.xyz/v1/models",
        {"Authorization": f"Bearer {api_key}"},
    )
    return status == 200


def verify_openrouter(api_key: str) -> bool:
    # IMPORTANT: Models endpoint does not require API key.
    # Using credits endpoint instead.
    status = _http_get_status_code(
        "https://openrouter.ai/api/v1/credits",
        {"Authorization": f"Bearer {api_key}"},
    )
    return status == 200


def verify_replicate(api_key: str) -> bool:
    status = _http_get_status_code(
        "https://api.replicate.com/v1/models",
        {"Authorization": f"Bearer {api_key}"},
    )
    return status == 200


def verify_fireworks(api_key: str) -> bool:
    status = _http_get_status_code(
        "https://api.fireworks.ai/v1/models",
        {"Authorization": f"Bearer {api_key}"},
    )
    return status == 200


def verify_deepseek(api_key: str) -> bool:
    status = _http_get_status_code(
        "https://api.deepseek.com/models",
        {"Authorization": f"Bearer {api_key}"},
    )
    return status == 200


def verify_huggingface(api_key: str) -> bool:
    # Use whoami-v2 as verification endpoint
    status = _http_get_status_code(
        "https://huggingface.co/api/whoami-v2",
        {"Authorization": f"Bearer {api_key}"},
    )
    return status == 200


def verify_stability_ai(api_key: str) -> bool:
    status = _http_get_status_code(
        "https://api.stability.ai/v1/engines/list",
        {"Authorization": f"Bearer {api_key}"},
    )
    return status == 200


def verify_github(api_key: str) -> bool:
    status = _http_get_status_code(
        "https://api.github.com/user",
        {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/vnd.github+json",
        },
    )
    return status == 200


# Unsupported verifications
# Deepinfra - Models endpoint open.
# Azure - Endpoint unknown...?
# AWS - Region specific endpoints, not sure how they work
# Nvidia - No model listing endpoint or other free endpoints
# Black Forest Labs - No model listing endpoint

PROVIDERS_TO_VERIFIER_MAP: Dict[PROVIDERS_TYPE, Callable[[str], bool]] = {
    "openai": verify_openai,
    "anthropic": verify_anthropic,
    "google": verify_google,
    "gemini": verify_google,
    "grok": verify_xai,
    "xai": verify_xai,
    "groq": verify_groq,
    "deepseek": verify_deepseek,
    "mistral": verify_mistral,
    "cohere": verify_cohere,
    "together": verify_together,
    "openrouter": verify_openrouter,
    "replicate": verify_replicate,
    "fireworks": verify_fireworks,
    "huggingface": verify_huggingface,
    "stability_ai": verify_stability_ai,
    "github": verify_github,
}


VALIDITY = Literal["VALID", "INVALID", "UNKNOWN"]


def verify(
    provider: PROVIDERS_TYPE, api_key: str
) -> VALIDITY:
    fn = PROVIDERS_TO_VERIFIER_MAP.get(provider)
    if not fn:
        return "UNKNOWN"
    try:
        if fn(api_key):
            return "VALID"
        else:
            return "INVALID"
    except requests.RequestException:
        return "UNKNOWN"
