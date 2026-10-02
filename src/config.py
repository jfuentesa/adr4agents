import os
from pathlib import Path


def load_config():
    root = Path(__file__).resolve().parent.parent
    return {
        "DATABASE": os.environ.get(
            "ADR4AGENTS_DATABASE", str(root / "instance" / "adr4agents.sqlite3")
        ),
        "MAX_CONTENT_LENGTH": 1_048_576,
    }
