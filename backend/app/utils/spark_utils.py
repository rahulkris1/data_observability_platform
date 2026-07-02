"""SparkSession utility for local execution and AWS Glue cloud execution."""

import logging
import os
import sys
from typing import Optional
from pyspark.sql import SparkSession
from app.core.config import settings

logger = logging.getLogger(__name__)

# Set PySpark to use the current Python executable
os.environ['PYSPARK_PYTHON'] = sys.executable
os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable


class SparkSessionManager:
    """
    Singleton manager for PySpark sessions supporting both local and AWS Glue execution.
    
    Provides a reusable SparkSession configured based on EXECUTION_MODE:
    - "local": Local Spark with standalone configuration
    - "glue": AWS Glue-compatible Spark with cloud optimizations
    """
    
    _instance: Optional[SparkSession] = None
    
    @classmethod
    def get_session(cls) -> SparkSession:
        """
        Get or create a SparkSession based on execution mode.
        
        Returns:
            Configured SparkSession for local or Glue execution
        """
        if cls._instance is None:
            cls._instance = cls._create_session()
        return cls._instance
    
    @classmethod
    def _create_session(cls) -> SparkSession:
        """
        Create a new SparkSession based on EXECUTION_MODE.
        
        Returns:
            Configured SparkSession instance
        """
        execution_mode = settings.EXECUTION_MODE.lower()
        
        if execution_mode == "glue":
            return cls._create_glue_session()
        else:
            return cls._create_local_session()
    
    @classmethod
    def _create_local_session(cls) -> SparkSession:
        """
        Create a SparkSession for local execution.
        
        Returns:
            Configured SparkSession instance for local development
        """
        logger.info("Creating local SparkSession...")
        
        spark = (
            SparkSession.builder
            .appName(settings.SPARK_APP_NAME)
            .master(settings.SPARK_MASTER)
            .config("spark.driver.memory", settings.SPARK_DRIVER_MEMORY)
            .config("spark.executor.memory", settings.SPARK_EXECUTOR_MEMORY)
            .config("spark.sql.adaptive.enabled", "true")
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
            .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
            .config("spark.sql.execution.arrow.pyspark.enabled", "true")  # PyArrow optimization
            .config("spark.ui.enabled", "false")  # Disable Spark UI for local dev
            .getOrCreate()
        )
        
        # Set log level
        spark.sparkContext.setLogLevel(settings.SPARK_LOG_LEVEL)
        
        logger.info(f"Local SparkSession created: {spark.version}")
        logger.info(f"Master: {settings.SPARK_MASTER}")
        logger.info(f"Driver Memory: {settings.SPARK_DRIVER_MEMORY}")
        
        return spark
    
    @classmethod
    def _create_glue_session(cls) -> SparkSession:
        """
        Create a Glue-compatible SparkSession for AWS Glue execution.
        
        Returns:
            Configured SparkSession instance optimized for AWS Glue
        """
        logger.info("Creating Glue-compatible SparkSession...")
        
        builder = SparkSession.builder.appName(settings.SPARK_APP_NAME)
        
        # Glue-specific configurations
        builder = (
            builder
            .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
            .config("spark.sql.adaptive.enabled", "true")
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
            .config("spark.sql.hive.convertMetastoreParquet", "true")
            .config("spark.sql.parquet.enableVectorizedReader", "true")
            .config("spark.sql.parquet.mergeSchema", "false")
            .config("spark.sql.files.maxPartitionBytes", "134217728")  # 128MB
        )
        
        # Add S3 configurations if running in Glue
        if settings.AWS_REGION:
            builder = builder.config("spark.hadoop.fs.s3a.endpoint", f"s3.{settings.AWS_REGION}.amazonaws.com")
        
        # Set temp directory for Glue
        if settings.GLUE_TEMP_DIR:
            builder = builder.config("spark.sql.warehouse.dir", settings.GLUE_TEMP_DIR)
        
        spark = builder.getOrCreate()
        
        # Set log level
        spark.sparkContext.setLogLevel(settings.SPARK_LOG_LEVEL)
        
        logger.info(f"Glue-compatible SparkSession created: {spark.version}")
        logger.info(f"Execution Mode: AWS Glue")
        
        return spark
    
    @classmethod
    def stop_session(cls) -> None:
        """Stop the current SparkSession if it exists."""
        if cls._instance is not None:
            logger.info("Stopping SparkSession...")
            cls._instance.stop()
            cls._instance = None
    
    @classmethod
    def restart_session(cls) -> SparkSession:
        """
        Restart the SparkSession.
        
        Returns:
            New SparkSession instance
        """
        cls.stop_session()
        return cls.get_session()
    
    @classmethod
    def get_execution_mode(cls) -> str:
        """
        Get current execution mode.
        
        Returns:
            "local" or "glue"
        """
        return settings.EXECUTION_MODE.lower()


def get_spark() -> SparkSession:
    """
    Convenience function to get the current SparkSession.
    
    Returns:
        Active SparkSession instance
    """
    return SparkSessionManager.get_session()


def get_execution_mode() -> str:
    """
    Get current execution mode.
    
    Returns:
        "local" or "glue"
    """
    return SparkSessionManager.get_execution_mode()
