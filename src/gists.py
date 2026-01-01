from typing import Dict, List, Literal, TypedDict, cast

import requests
import config


class FileJSON(TypedDict):
    language: str | None
    size: int
    """
    Note on file content and truncation:

    Entire books have been uploaded on GitHub gists (ex: Alice in Wonderland,
    size 100k+) without being truncated. Therefore, we can be confident that
    99.999% of legitimate env files will not be truncated by the GitHub API.
    """
    truncated: bool
    content: str


class GistJSON(TypedDict):
    html_url: str
    files: Dict[str, FileJSON]
    owner: Dict[Literal["login"], str]


GIST_API_BASE_URL = "https://api.github.com/gists"


def build_gist_api_url(gist_id: str) -> str:
    return f"{GIST_API_BASE_URL}/{gist_id}"


def get_api_headers() -> Dict[str, str]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    }
    if config.GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {config.GITHUB_TOKEN}"
    return headers


def fetch_gist_by_id(
    session: requests.Session, gist_id: str, timeout_seconds: int = 20
) -> GistJSON:
    """Get's gist using ID and GitHub API. May throw exceptions."""
    url = build_gist_api_url(gist_id)
    response = session.get(url, headers=get_api_headers(), timeout=timeout_seconds)
    response.raise_for_status()
    return cast(GistJSON, response.json())


def filter_file_type(gist_json: GistJSON, file_type: str) -> List[FileJSON]:
    files = gist_json.get("files", {})
    result: List[FileJSON] = []
    for file in files.values():
        language = cast(str, file.get("language", ""))
        if language == file_type:
            result.append(file)
    return result


class GistInfo:
    owner: str
    file_contents: List[str]

    def __init__(self, owner: str, file_contents: List[str]):
        self.owner = owner
        self.file_contents = file_contents


def get_gist_info(
    session: requests.Session, gist_id: str, file_type: str, timeout_seconds: int = 20
) -> GistInfo:
    """
    Return an array of strings containing the file contents of the desired type.
    """

    gist_json = fetch_gist_by_id(session, gist_id, timeout_seconds=timeout_seconds)
    filtered_files = filter_file_type(gist_json, file_type)

    owner = gist_json.get("owner").get("login", "_UNKNOWN_USER")
    file_contents: List[str] = []
    for file in filtered_files:
        truncated = file.get("truncated")
        if not truncated:
            # TODO: Size limit?
            file_contents.append(file.get("content"))
        else:
            print(f"Truncated file encountered: {gist_id}")

    return GistInfo(owner, file_contents)
