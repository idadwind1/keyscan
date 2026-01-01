import os
import traceback
from typing import List

import requests

from src.args import parse_args
from src.pipeline import search_one_keyword
from src.util import create_directory, print_err
from src.scanned_db import ScannedDb
import config

session = requests.Session()
if config.GITHUB_SESSION_COOKIE:
    session.headers["_gh_sess"] = config.GITHUB_SESSION_COOKIE


def get_keywords(keywords_file: str) -> List[str]:
    keywords = []
    try:
        with open(keywords_file, "r") as file:
            for line in file:
                keyword = line.strip()
                if (
                    keyword
                    and not keyword.startswith("#")
                    and not keyword.startswith("//")
                ):
                    keywords.append(keyword)
        return keywords
    except FileNotFoundError as exception:
        print_err(f"Keywords file not found: {keywords_file}")
        raise exception


def main() -> int:
    args = parse_args()

    create_directory(os.path.dirname(args.output_path))

    database = ScannedDb(args.scanned_db)

    total_gists = 0

    try:
        keywords_list = get_keywords(args.keywords_file)
        for keyword in keywords_list:
            gists_processed = search_one_keyword(keyword, args, database, session)
            total_gists += gists_processed

    except KeyboardInterrupt:
        print("Interrupted.")
        print(f"Successfully processed {total_gists} gists.")
        return 130

    except Exception as exception:
        print_err(f"Error: {exception}")
        print_err(
            "".join(traceback.TracebackException.from_exception(exception).format())
        )
        print(f"Successfully processed {total_gists} gists.")
        return 1

    print(f"Successfully processed {total_gists} gists.")
    print("Search finished.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
