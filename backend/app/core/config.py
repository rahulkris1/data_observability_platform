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
    DATABASE_URL: str = "postgresql://dop_user:dop_password@localhost:5432/data_observability"
    
    # Redis Cache
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # MinIO Object Storage
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin123"
    MINIO_SECURE: bool = False
    MINIO_BUCKET_RAW: str = "raw-data"
    MINIO_BUCKET_PROCESSED: str = "processed-data"
    MINIO_BUCKET_AUDIT: str = "audit-data"
    
    # Local PySpark Configuration
    SPARK_APP_NAME: str = "DataObservabilityPlatform"
    SPARK_MASTER: str = "local[*]"  # Use all available cores locally
    SPARK_DRIVER_MEMORY: str = "2g"
    SPARK_EXECUTOR_MEMORY: str = "2g"
    SPARK_LOG_LEVEL: str = "WARN"  # Reduce verbosity for local development
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
