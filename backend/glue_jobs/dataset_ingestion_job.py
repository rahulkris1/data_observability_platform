"""
Dataset Ingestion Job: Supports both Local and AWS Glue execution

This job ingests datasets from storage (local/MinIO for local mode, S3 for Glue mode),
validates them, and writes processed data back to storage.

Execution modes:
- Local: Uses local SparkSession and MinIO
- Glue: Uses AWS Glue DynamicFrames and S3
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.ingestion_service import IngestionService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def is_glue_environment() -> bool:
    """Check if running in AWS Glue environment."""
    try:
        import awsglue  # noqa: F401
        return True
    except ImportError:
        return False


def ingest_local_dataset(source_path: str) -> dict:
    """
    Ingest a local file into MinIO using the ingestion service.
    
    Args:
        source_path: Path to local file
    
    Returns:
        Ingestion result metadata
    """
    logger.info(f"Local ingestion mode: {source_path}")
    
    source_file = Path(source_path)
    if not source_file.exists() or not source_file.is_file():
        raise FileNotFoundError(f"Input file not found: {source_path}")

    file_bytes = source_file.read_bytes()
    service = IngestionService()
    result = service.ingest_dataset(source_file.name, file_bytes)
    
    logger.info(f"Successfully ingested {result.get('record_count', 0)} records")
    return result


def ingest_glue_dataset(job_args: Dict[str, str]) -> dict:
    """
    Ingest dataset using AWS Glue DynamicFrames.
    
    Args:
        job_args: Glue job arguments
    
    Returns:
        Ingestion result metadata
    """
    try:
        from awsglue.context import GlueContext
        from awsglue.utils import getResolvedOptions
        from awsglue.job import Job
        from awsglue.dynamicframe import DynamicFrame
        from pyspark.context import SparkContext
        from pyspark.sql.functions import current_timestamp, lit
        
        logger.info("Glue ingestion mode")
        
        # Initialize Glue context
        sc = SparkContext()
        glue_context = GlueContext(sc)
        spark = glue_context.spark_session
        job = Job(glue_context)
        job.init(job_args['JOB_NAME'], job_args)
        
        # Extract parameters
        s3_bucket_raw = job_args['S3_BUCKET_RAW']
        s3_bucket_processed = job_args['S3_BUCKET_PROCESSED']
        source_path = job_args.get('SOURCE_PATH', f"s3://{s3_bucket_raw}/")
        file_format = job_args.get('FILE_FORMAT', 'json')
        output_format = job_args.get('OUTPUT_FORMAT', 'parquet')
        
        logger.info(f"Reading from {source_path} ({file_format})")
        
        # Read raw data using DynamicFrame
        format_options = {}
        if file_format == "csv":
            format_options = {"withHeader": True, "separator": ","}
        
        raw_dynamic_frame = glue_context.create_dynamic_frame.from_options(
            connection_type="s3",
            connection_options={"paths": [source_path]},
            format=file_format,
            format_options=format_options
        )
        
        record_count = raw_dynamic_frame.count()
        logger.info(f"Read {record_count} records")
        
        # Convert to DataFrame for transformations
        df = raw_dynamic_frame.toDF()
        
        # Add metadata columns
        df = df.withColumn("processed_at", current_timestamp())
        df = df.withColumn("processing_job", lit("glue_dataset_ingestion"))
        
        # Convert back to DynamicFrame
        processed_frame = DynamicFrame.fromDF(df, glue_context, "processed_frame")
        
        # Write to S3
        output_path = f"s3://{s3_bucket_processed}/processed/{datetime.utcnow().strftime('%Y/%m/%d')}/"
        logger.info(f"Writing to {output_path} ({output_format})")
        
        glue_context.write_dynamic_frame.from_options(
            frame=processed_frame,
            connection_type="s3",
            connection_options={"path": output_path},
            format=output_format
        )
        
        # Commit job
        job.commit()
        
        result = {
            "source_path": source_path,
            "output_path": output_path,
            "record_count": record_count,
            "file_format": file_format,
            "output_format": output_format,
            "execution_mode": "glue"
        }
        
        logger.info("Glue ingestion completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Glue ingestion failed: {e}")
        raise


def main() -> None:
    """Main execution entry point."""
    
    if is_glue_environment():
        # AWS Glue execution mode
        try:
            from awsglue.utils import getResolvedOptions
            
            args = getResolvedOptions(sys.argv, [
                'JOB_NAME',
                'S3_BUCKET_RAW',
                'S3_BUCKET_PROCESSED'
            ])
            
            # Optional parameters
            optional_args = ['SOURCE_PATH', 'FILE_FORMAT', 'OUTPUT_FORMAT', 'DATABASE_URL']
            for arg in optional_args:
                try:
                    optional = getResolvedOptions(sys.argv, [arg])
                    args.update(optional)
                except:
                    pass
            
            result = ingest_glue_dataset(args)
            print(json.dumps(result, indent=2, default=str))
            
        except Exception as e:
            logger.error(f"Glue job failed: {e}")
            sys.exit(1)
    else:
        # Local execution mode
        parser = argparse.ArgumentParser(
            description="Run dataset ingestion job (Local or Glue mode)"
        )
        parser.add_argument(
            "source_path", 
            help="Path to the local dataset file (CSV or JSON)"
        )
        args = parser.parse_args()
        
        try:
            result = ingest_local_dataset(args.source_path)
            print(json.dumps(result, indent=2))
        except Exception as e:
            logger.error(f"Local ingestion failed: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
