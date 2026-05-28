from dataclasses import dataclass

from app.core.config import settings


@dataclass(frozen=True)
class IngestionConfig:
    """Central ingestion configuration for local dataset processing."""

    raw_bucket: str = settings.MINIO_BUCKET_RAW
    processed_bucket: str = settings.MINIO_BUCKET_PROCESSED
    audit_bucket: str = settings.MINIO_BUCKET_AUDIT
    raw_prefix: str = "raw/"
    processed_prefix: str = "processed/"
    audit_prefix: str = "audit/"
    supported_file_types = ("csv", "json")
