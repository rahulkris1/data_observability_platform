"""JSON parser utilities for local dataset ingestion."""
import json
from typing import Any


def parse_json_bytes(data: bytes, encoding: str = "utf-8") -> Any:
    """Parse JSON bytes into a Python object."""
    return json.loads(data.decode(encoding))
