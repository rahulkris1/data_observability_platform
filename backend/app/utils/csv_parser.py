"""CSV parser utilities for local dataset ingestion."""
import io
from typing import Any, Dict, List

import pandas as pd


def parse_csv_bytes(data: bytes, encoding: str = "utf-8") -> List[Dict[str, Any]]:
    """Parse CSV bytes into a list of records."""
    buffer = io.StringIO(data.decode(encoding))
    dataframe = pd.read_csv(buffer)
    if dataframe.empty:
        return []

    dataframe = dataframe.where(pd.notnull(dataframe), None)
    return dataframe.to_dict(orient="records")
