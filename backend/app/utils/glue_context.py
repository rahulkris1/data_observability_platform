"""AWS Glue context utilities for cloud-based Spark execution."""

import logging
import sys
from typing import Optional

logger = logging.getLogger(__name__)


class GlueContextManager:
    """
    Manager for AWS Glue context and GlueContext.
    
    Provides conditional Glue imports and context creation
    to support both local and AWS Glue execution environments.
    """
    
    _glue_context = None
    _spark_context = None
    
    @classmethod
    def is_glue_available(cls) -> bool:
        """
        Check if AWS Glue libraries are available.
        
        Returns:
            True if Glue libraries can be imported, False otherwise
        """
        try:
            import awsglue  # noqa: F401
            return True
        except ImportError:
            return False
    
    @classmethod
    def get_glue_context(cls, spark_session=None):
        """
        Get or create a GlueContext.
        
        Args:
            spark_session: Optional SparkSession to use for GlueContext
        
        Returns:
            GlueContext instance if running in Glue environment
            
        Raises:
            ImportError: If Glue libraries are not available
            RuntimeError: If context creation fails
        """
        if cls._glue_context is not None:
            return cls._glue_context
        
        if not cls.is_glue_available():
            raise ImportError(
                "AWS Glue libraries not available. "
                "Ensure you're running in an AWS Glue environment or "
                "install awsglue-local for local testing."
            )
        
        try:
            from awsglue.context import GlueContext
            from pyspark.context import SparkContext
            
            logger.info("Creating GlueContext...")
            
            if spark_session:
                sc = spark_session.sparkContext
            else:
                sc = SparkContext.getOrCreate()
            
            cls._spark_context = sc
            cls._glue_context = GlueContext(sc)
            
            logger.info("GlueContext created successfully")
            return cls._glue_context
            
        except Exception as e:
            logger.error(f"Failed to create GlueContext: {e}")
            raise RuntimeError(f"GlueContext creation failed: {e}")
    
    @classmethod
    def get_job_arguments(cls) -> dict:
        """
        Get Glue job arguments passed via --key value pairs.
        
        Returns:
            Dictionary of job arguments
        """
        if not cls.is_glue_available():
            logger.warning("Glue not available, returning empty job arguments")
            return {}
        
        try:
            from awsglue.utils import getResolvedOptions
            
            # Define expected job arguments
            expected_args = [
                'JOB_NAME',
                'S3_BUCKET_RAW',
                'S3_BUCKET_PROCESSED',
                'DATABASE_URL',
            ]
            
            # Get only the arguments that are provided
            args = {}
            for arg in expected_args:
                try:
                    resolved = getResolvedOptions(sys.argv, [arg])
                    args.update(resolved)
                except Exception:
                    # Argument not provided, skip it
                    pass
            
            logger.info(f"Retrieved {len(args)} job arguments")
            return args
            
        except Exception as e:
            logger.warning(f"Failed to get job arguments: {e}")
            return {}
    
    @classmethod
    def create_dynamic_frame(cls, glue_context, source_path: str, format_type: str = "json"):
        """
        Create a DynamicFrame from S3 source.
        
        Args:
            glue_context: GlueContext instance
            source_path: S3 path to data source
            format_type: Data format (json, csv, parquet, etc.)
        
        Returns:
            DynamicFrame
        """
        try:
            from awsglue.dynamicframe import DynamicFrame
            
            logger.info(f"Creating DynamicFrame from {source_path} ({format_type})")
            
            dynamic_frame = glue_context.create_dynamic_frame.from_options(
                connection_type="s3",
                connection_options={"paths": [source_path]},
                format=format_type,
                format_options={} if format_type != "csv" else {
                    "withHeader": True,
                    "separator": ","
                }
            )
            
            logger.info(f"DynamicFrame created with {dynamic_frame.count()} records")
            return dynamic_frame
            
        except Exception as e:
            logger.error(f"Failed to create DynamicFrame: {e}")
            raise
    
    @classmethod
    def dynamic_frame_to_dataframe(cls, dynamic_frame):
        """
        Convert DynamicFrame to Spark DataFrame.
        
        Args:
            dynamic_frame: GlueContext DynamicFrame
        
        Returns:
            Spark DataFrame
        """
        try:
            logger.info("Converting DynamicFrame to DataFrame")
            df = dynamic_frame.toDF()
            logger.info(f"Converted to DataFrame with {df.count()} records")
            return df
        except Exception as e:
            logger.error(f"Failed to convert DynamicFrame to DataFrame: {e}")
            raise
    
    @classmethod
    def dataframe_to_dynamic_frame(cls, glue_context, dataframe, name: str = "dynamic_frame"):
        """
        Convert Spark DataFrame to DynamicFrame.
        
        Args:
            glue_context: GlueContext instance
            dataframe: Spark DataFrame
            name: Name for the DynamicFrame
        
        Returns:
            DynamicFrame
        """
        try:
            from awsglue.dynamicframe import DynamicFrame
            
            logger.info(f"Converting DataFrame to DynamicFrame: {name}")
            dynamic_frame = DynamicFrame.fromDF(dataframe, glue_context, name)
            logger.info(f"Converted to DynamicFrame with {dynamic_frame.count()} records")
            return dynamic_frame
        except Exception as e:
            logger.error(f"Failed to convert DataFrame to DynamicFrame: {e}")
            raise
    
    @classmethod
    def write_dynamic_frame(cls, glue_context, dynamic_frame, target_path: str, 
                           format_type: str = "json", partition_keys: Optional[list] = None):
        """
        Write DynamicFrame to S3.
        
        Args:
            glue_context: GlueContext instance
            dynamic_frame: DynamicFrame to write
            target_path: S3 destination path
            format_type: Output format (json, parquet, csv, etc.)
            partition_keys: Optional list of partition column names
        """
        try:
            logger.info(f"Writing DynamicFrame to {target_path} ({format_type})")
            
            write_options = {
                "path": target_path,
            }
            
            if partition_keys:
                write_options["partitionKeys"] = partition_keys
            
            glue_context.write_dynamic_frame.from_options(
                frame=dynamic_frame,
                connection_type="s3",
                connection_options=write_options,
                format=format_type
            )
            
            logger.info("DynamicFrame written successfully")
            
        except Exception as e:
            logger.error(f"Failed to write DynamicFrame: {e}")
            raise
    
    @classmethod
    def stop_context(cls):
        """Stop the GlueContext and SparkContext."""
        if cls._glue_context is not None:
            logger.info("Stopping GlueContext...")
            cls._glue_context = None
        
        if cls._spark_context is not None:
            logger.info("Stopping SparkContext...")
            cls._spark_context.stop()
            cls._spark_context = None


def get_glue_context(spark_session=None):
    """
    Convenience function to get GlueContext.
    
    Args:
        spark_session: Optional SparkSession
    
    Returns:
        GlueContext instance
    """
    return GlueContextManager.get_glue_context(spark_session)


def is_running_in_glue() -> bool:
    """
    Detect if code is running in AWS Glue environment.
    
    Returns:
        True if running in Glue, False otherwise
    """
    # Check for Glue-specific environment variables
    import os
    return (
        os.environ.get('AWS_EXECUTION_ENV', '').startswith('AWS_ECS_FARGATE') or
        os.environ.get('GLUE_VERSION') is not None or
        GlueContextManager.is_glue_available()
    )
