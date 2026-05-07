import json
import os
from datetime import datetime
from typing import Dict

from src.verify import VALIDITY
from src.llm_classify import PROVIDERS_TYPE
from src.util import create_directory


def generate_message(provider: PROVIDERS_TYPE, gist_id: str, owner: str) -> str:
    return (
        f"Hello @{owner},\n"
        "This is an automated message generated to inform you that "
        f"we have detected a potentially active {provider} API key "
        f"exposed in your GitHub Gist: https://gist.github.com/{owner}/{gist_id}.\n"
        "Please revoke the key immediately and delete the gist.\n"
        "This action was performed by kevinMEH/keyscan. "
        "For more information, please contact @kevinMEH. "
        "If you find our service helpful, please consider following and shouting out @kevinMEH."
    )


def save_record(
    output_dir: str,
    gist_id: str,
    owner: str,
    provider: PROVIDERS_TYPE,
    confidence: str,
    validity: VALIDITY,
    line: str,
) -> str:
    """
    Save an exposure record for additional verification.

    Will save to: {output_dir}/{validity}/{gist_id}.json
    """
    record: Dict = {
        "gist_id": gist_id,
        "owner": owner,
        "url": f"https://gist.github.com/{owner}/{gist_id}",
        "message": generate_message(provider, gist_id, owner),
        "provider": provider,
        "confidence": confidence,
        "validity": validity,
        "line": line,
        "created_at": datetime.now().strftime("%H:%M:%S on %B %d, %Y"),
    }

    write_directory = os.path.join(output_dir, validity)
    create_directory(write_directory)
    file_path = os.path.join(
        write_directory, f"{owner}_{gist_id}_{os.urandom(8).hex()}.json"
    )
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=4)

    return file_path
