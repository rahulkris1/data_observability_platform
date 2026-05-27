"""SparkSession utility for local execution and data validation."""

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
    Singleton manager for local PySpark sessions.
    
    Provides a reusable SparkSession configured for local execution
    without distributed or cloud dependencies.
    """
    
    _instance: Optional[SparkSession] = None
    
    @classmethod
    def get_session(cls) -> SparkSession:
        """
        Get or create a local SparkSession.
        
        Returns:
            Configured SparkSession for local execution
        """
        if cls._instance is None:
            cls._instance = cls._create_session()
        return cls._instance
    
    @classmethod
    def _create_session(cls) -> SparkSession:
        """
        Create a new SparkSession with local configuration.
        
        Returns:
            Configured SparkSession instance
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
        
        logger.info(f"SparkSession created: {spark.version}")
        logger.info(f"Master: {settings.SPARK_MASTER}")
        logger.info(f"Driver Memory: {settings.SPARK_DRIVER_MEMORY}")
        
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


def get_spark() -> SparkSession:
    """
    Convenience function to get the current SparkSession.
    
    Returns:
        Active SparkSession instance
    """
    return SparkSessionManager.get_session()
