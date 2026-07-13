from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with database, cache, and storage configuration"""
    
    # Application
    APP_NAME: str = "Data Observability Platform"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    
    # PostgreSQL Database
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "dop_user"
    POSTGRES_PASSWORD: str = "dop_password"
    POSTGRES_DB: str = "data_observability"
    # Use SQLite for local development (no Docker needed)
    DATABASE_URL: str = "sqlite:///./data_observability.db"
    # For PostgreSQL: "postgresql://dop_user:dop_password@localhost:5432/data_observability"
    
    # Redis Cache
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Storage Provider Configuration
    STORAGE_PROVIDER: str = "minio"  # Options: "minio" or "s3"
    
    # MinIO Object Storage (local development)
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin123"
    MINIO_SECURE: bool = False
    MINIO_BUCKET_RAW: str = "raw-data"
    MINIO_BUCKET_PROCESSED: str = "processed-data"
    MINIO_BUCKET_AUDIT: str = "audit-data"
    
    # AWS S3 Object Storage (production)
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_RAW: str = "dop-raw-data"
    S3_BUCKET_PROCESSED: str = "dop-processed-data"
    S3_BUCKET_AUDIT: str = "dop-audit-data"
    
    # Local PySpark Configuration
    SPARK_APP_NAME: str = "DataObservabilityPlatform"
    SPARK_MASTER: str = "local[*]"  # Use all available cores locally
    SPARK_DRIVER_MEMORY: str = "2g"
    SPARK_EXECUTOR_MEMORY: str = "2g"
    SPARK_LOG_LEVEL: str = "WARN"  # Reduce verbosity for local development
    
    # Execution Mode Configuration
    EXECUTION_MODE: str = "local"  # Options: "local" or "glue"
    
    # AWS Glue Configuration
    GLUE_JOB_NAME: str = ""  # e.g., "dop-dataset-ingestion-job"
    GLUE_IAM_ROLE: str = ""  # e.g., "arn:aws:iam::ACCOUNT_ID:role/GlueServiceRole"
    GLUE_SCRIPT_BUCKET: str = ""  # e.g., "dop-glue-scripts"
    GLUE_WORKER_TYPE: str = "G.1X"  # Options: G.1X, G.2X, Standard
    GLUE_NUMBER_OF_WORKERS: int = 2
    GLUE_TIMEOUT: int = 2880  # minutes (48 hours)
    GLUE_MAX_RETRIES: int = 1
    GLUE_SECURITY_CONFIGURATION: str = ""  # Optional
    GLUE_TEMP_DIR: str = ""  # e.g., "s3://dop-glue-temp/"
    
    # AWS CloudWatch Configuration
    CLOUDWATCH_ENABLED: bool = False  # Enable CloudWatch metrics and logs
    CLOUDWATCH_NAMESPACE: str = "DataObservabilityPlatform"
    CLOUDWATCH_LOG_GROUP: str = "/aws/dataobservability/application"
    
    # Snowflake Data Warehouse Configuration
    SNOWFLAKE_ACCOUNT: str = ""  # e.g., "xy12345.us-east-1"
    SNOWFLAKE_USER: str = ""
    SNOWFLAKE_PASSWORD: str = ""
    SNOWFLAKE_WAREHOUSE: str = ""  # e.g., "COMPUTE_WH"
    SNOWFLAKE_DATABASE: str = ""  # e.g., "DATA_OBSERVABILITY"
    SNOWFLAKE_SCHEMA: str = "PUBLIC"
    SNOWFLAKE_ROLE: str = ""  # e.g., "ACCOUNTADMIN"
    
    # Airflow AWS Connection Configuration
    AIRFLOW_AWS_CONN_ID: str = "aws_default"
    AIRFLOW_SNOWFLAKE_CONN_ID: str = "snowflake_default"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
