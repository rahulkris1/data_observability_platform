"""Ingestion service for local dataset uploads and MinIO storage."""
import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4
from typing import Any, Dict

from app.core.ingestion_config import IngestionConfig
from app.storage.minio_client import minio_client
from app.utils.csv_parser import parse_csv_bytes
from app.utils.json_parser import parse_json_bytes


class IngestionService:
    """Service layer for ingesting datasets into MinIO and parsing data."""

    def __init__(self) -> None:
        self.config = IngestionConfig()

    def _get_content_type(self, file_type: str) -> str:
        if file_type == "csv":
            return "text/csv"
        if file_type == "json":
            return "application/json"
        return "application/octet-stream"

    def _validate_file_type(self, filename: str) -> str:
        file_type = Path(filename).suffix.lower().lstrip(".")
        if file_type not in self.config.supported_file_types:
            raise ValueError(
                f"Unsupported file type '{file_type}'. Supported formats: {', '.join(self.config.supported_file_types)}"
            )
        return file_type

    def _build_object_name(self, prefix: str, filename: str) -> str:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_name = Path(filename).name
        return f"{prefix}{timestamp}_{uuid4().hex}_{safe_name}"

    def ingest_dataset(self, filename: str, data: bytes, content_type: str | None = None) -> Dict[str, Any]:
        """Upload a local dataset to MinIO and parse it into processed storage."""
        file_type = self._validate_file_type(filename)
        object_name = self._build_object_name(self.config.raw_prefix, filename)
        raw_content_type = content_type or self._get_content_type(file_type)

        uploaded = minio_client.upload_object(
            bucket_type="raw",
            object_name=object_name,
            data=data,
            content_type=raw_content_type,
        )
        if not uploaded:
            raise RuntimeError("Failed to upload raw dataset to MinIO")

        if file_type == "csv":
            parsed_data = parse_csv_bytes(data)
        else:
            parsed_data = parse_json_bytes(data)

        processed_object = self._build_object_name(self.config.processed_prefix, f"{Path(filename).stem}.json")
        processed_payload = json.dumps(parsed_data, default=str).encode("utf-8")
        processed_uploaded = minio_client.upload_object(
            bucket_type="processed",
            object_name=processed_object,
            data=processed_payload,
            content_type="application/json",
        )

        if not processed_uploaded:
            raise RuntimeError("Failed to upload processed dataset to MinIO")

        return {
            "filename": filename,
            "raw_object_name": object_name,
            "processed_object_name": processed_object,
            "record_count": len(parsed_data) if isinstance(parsed_data, list) else 1,
            "preview": parsed_data[:5] if isinstance(parsed_data, list) else parsed_data,
        }

    def load_processed_dataset(self, object_name: str) -> Any:
        """Read a processed dataset from MinIO and return parsed content."""
        raw_bytes = minio_client.download_object("processed", object_name)
        if raw_bytes is None:
            raise FileNotFoundError(f"Processed object not found: {object_name}")
        return parse_json_bytes(raw_bytes)

    def load_raw_dataset(self, object_name: str) -> bytes:
        """Read a raw dataset from MinIO."""
        raw_bytes = minio_client.download_object("raw", object_name)
        if raw_bytes is None:
            raise FileNotFoundError(f"Raw object not found: {object_name}")
        return raw_bytes
