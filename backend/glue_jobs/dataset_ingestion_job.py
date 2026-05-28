import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.ingestion_service import IngestionService


def ingest_local_dataset(source_path: str) -> dict:
    """Ingest a local file into MinIO using the ingestion service."""
    source_file = Path(source_path)
    if not source_file.exists() or not source_file.is_file():
        raise FileNotFoundError(f"Input file not found: {source_path}")

    file_bytes = source_file.read_bytes()
    service = IngestionService()
    return service.ingest_dataset(source_file.name, file_bytes)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a local dataset ingestion job into MinIO")
    parser.add_argument("source_path", help="Path to the local CSV or JSON dataset file")
    args = parser.parse_args()

    result = ingest_local_dataset(args.source_path)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
