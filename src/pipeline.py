from typing import List, Set, TypedDict, cast

import requests

from src.processing import ALL_FILE_TYPES, GIST_FILE_TYPE, extract_verifiable_value, preprocess_contents
from src.args import Arguments
from src.storage import ScannedDb, save_processing_state, save_record
from src.verify import verify, VALIDITY
from src.gists import GistInfo, get_gist_info, search_gists
from src.classify import (
    CONFIDENCE_LEVELS_TYPE,
    ClassificationResponse,
    classify_lines,
)


class ProcessGistResult(TypedDict):
    path: str
    owner: str
    gist_id: str
    confidence: CONFIDENCE_LEVELS_TYPE
    validity: VALIDITY
    line: str


def process_gist(
    gist_id: str,
    file_type: GIST_FILE_TYPE,
    model: str,
    output_dir: str,
    session: requests.Session,
) -> List[ProcessGistResult]:
    """
    Process a single gist: fetch contents, filter, classify, verify, and save.

    Note: Save a record when verification result is "UNKNOWN" or "VALID".
    """
    gist_info: GistInfo = get_gist_info(session, gist_id, file_type)

    lines: List[str] = preprocess_contents(gist_info.file_contents, file_type)

    classifications: List[ClassificationResponse] = classify_lines(lines, model)

    # Track already-verified keys to avoid duplicate checks per gist
    checked_values: Set[str] = set()

    result: List[ProcessGistResult] = []

    for classification_response in classifications:
        confidence, provider, line = (
            classification_response.confidence,
            classification_response.provider,
            classification_response.line,
        )

        if confidence == None or provider == None:
            continue
        if confidence == "NONE":
            continue

        value = extract_verifiable_value(line, file_type)

        if value == None:
            continue

        if value in checked_values:
            continue

        checked_values.add(value)

        validity: VALIDITY = verify(provider, value)

        if (
            validity == "VALID"
            or confidence in ["MEDIUM", "HIGH"]
        ):
            path = save_record(
                output_dir=output_dir,
                gist_id=gist_id,
                owner=gist_info.owner,
                provider=provider,
                confidence=confidence,
                validity=validity,
                line=line,
            )
            result.append(
                {
                    "path": path,
                    "owner": gist_info.owner,
                    "gist_id": gist_id,
                    "confidence": confidence,
                    "validity": validity,
                    "line": line,
                }
            )

    return result


def search_one_keyword(keyword: str, args: Arguments, database: ScannedDb, session: requests.Session) -> int:
    """
    Search all gists given a file type matching a keyword.

    Returns the total number of gists processed.
    """
    processed_gists = 0
    
    file_type = args.file_type
    if not file_type in ALL_FILE_TYPES:
        raise Exception(f"Unsupported file type {file_type}. Please add processing functions for the new file type in src/processing.py.")
    file_type = cast(GIST_FILE_TYPE, file_type)

    for page_number, gist_ids in search_gists(
        keyword,
        file_type=args.file_type,
        delay_seconds=args.delay,
    ):
        print(f"Keyword '{keyword}' — Page {page_number}:")
        print(f"Gists found: {gist_ids}")

        for gist_id in gist_ids:
            if database.seen(gist_id):
                print(f"Skipping already scanned gist: {gist_id}")
                continue

            print(f'Processing gist "{gist_id}"...')
            results = process_gist(
                session=session,
                gist_id=gist_id,
                file_type=file_type,
                model=args.model,
                output_dir=args.output_path,
            )
            processed_gists += 1
            if len(results) > 0:
                print(f"Processed {gist_id}: {len(results)} record(s) saved.")
                for result in results:
                    print(result)

            database.add(gist_id)

        save_processing_state(args.output_path, keyword, page_number)

    return processed_gists
