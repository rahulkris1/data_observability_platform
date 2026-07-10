"""
Production Configuration Module
Optimized settings for production deployment using Docker Compose
"""
from pydantic_settings import BaseSettings
from typing import Optional
import secrets


class ProductionSettings(BaseSettings):
    """
    Production-specific settings with security hardening and performance optimization.
    These settings override the base config when ENVIRONMENT=production
    """
    
    # Application
    APP_NAME: str = "Data Observability Platform"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    
    # Security
    SECRET_KEY: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS Settings (Production)
    CORS_ORIGINS: list = ["http://localhost:3000", "http://frontend:3000"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: list = ["GET", "POST", "PUT", "DELETE", "PATCH"]
    CORS_HEADERS: list = ["*"]
    
    # PostgreSQL Database (Production)
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DATABASE_URL: str
    
    # Database Connection Pool (Production Optimized)
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 40
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600
    DB_POOL_PRE_PING: bool = True
    DB_ECHO: bool = False
    
    # Redis Cache (Production)
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str
    REDIS_URL: str
    
    # Redis Connection Pool (Production)
    REDIS_MAX_CONNECTIONS: int = 50
    REDIS_SOCKET_TIMEOUT: int = 5
    REDIS_SOCKET_CONNECT_TIMEOUT: int = 5
    REDIS_SOCKET_KEEPALIVE: bool = True
    REDIS_HEALTH_CHECK_INTERVAL: int = 30
    
    # Storage Provider Configuration
    STORAGE_PROVIDER: str = "minio"  # "minio" for Docker, "s3" for AWS
    
    # MinIO Object Storage (Docker Production)
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_SECURE: bool = False
    MINIO_BUCKET_RAW: str = "raw-data-prod"
    MINIO_BUCKET_PROCESSED: str = "processed-data-prod"
    MINIO_BUCKET_AUDIT: str = "audit-data-prod"
    
    # AWS S3 (for future AWS deployment)
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_RAW: Optional[str] = None
    S3_BUCKET_PROCESSED: Optional[str] = None
    S3_BUCKET_AUDIT: Optional[str] = None
    
    # AWS CloudWatch (Optional)
    AWS_CLOUDWATCH_ENABLED: bool = False
    AWS_CLOUDWATCH_LOG_GROUP: Optional[str] = None
    AWS_CLOUDWATCH_LOG_STREAM: Optional[str] = None
    
    # AWS Glue (Optional)
    AWS_GLUE_ENABLED: bool = False
    AWS_GLUE_DATABASE: Optional[str] = None
    AWS_GLUE_CRAWLER_NAME: Optional[str] = None
    
    # Celery Task Queue (Production)
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: list = ["json"]
    CELERY_TIMEZONE: str = "UTC"
    CELERY_ENABLE_UTC: bool = True
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = 4
    CELERY_WORKER_MAX_TASKS_PER_CHILD: int = 1000
    CELERY_TASK_ACKS_LATE: bool = True
    CELERY_TASK_REJECT_ON_WORKER_LOST: bool = True
    
    # Airflow Integration (Production)
    AIRFLOW_API_URL: str = "http://airflow-webserver:8080/api/v1"
    AIRFLOW_USERNAME: str = "admin"
    AIRFLOW_PASSWORD: str
    
    # PySpark Configuration (Local Production)
    SPARK_APP_NAME: str = "DataObservabilityPlatform-Production"
    SPARK_MASTER: str = "local[*]"
    SPARK_DRIVER_MEMORY: str = "4g"
    SPARK_EXECUTOR_MEMORY: str = "4g"
    SPARK_LOG_LEVEL: str = "WARN"
    
    # Execution Mode
    EXECUTION_MODE: str = "local"
    
    # Snowflake Data Warehouse (Optional)
    SNOWFLAKE_ACCOUNT: Optional[str] = None
    SNOWFLAKE_USER: Optional[str] = None
    SNOWFLAKE_PASSWORD: Optional[str] = None
    SNOWFLAKE_DATABASE: Optional[str] = None
    SNOWFLAKE_SCHEMA: str = "PUBLIC"
    SNOWFLAKE_WAREHOUSE: Optional[str] = None
    SNOWFLAKE_ROLE: Optional[str] = None
    
    # Logging Configuration (Production)
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: str = "/app/logs/production.log"
    LOG_MAX_BYTES: int = 10485760  # 10MB
    LOG_BACKUP_COUNT: int = 5
    
    # Performance Settings
    UVICORN_WORKERS: int = 4
    UVICORN_LIMIT_CONCURRENCY: int = 1000
    UVICORN_LIMIT_MAX_REQUESTS: int = 10000
    UVICORN_TIMEOUT_KEEP_ALIVE: int = 5
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Health Check Settings
    HEALTH_CHECK_TIMEOUT: int = 5
    
    class Config:
        env_file = ".env.production"
        case_sensitive = True


def get_production_settings() -> ProductionSettings:
    """
    Factory function to create production settings instance.
    Validates all required production settings are present.
    """
    return ProductionSettings()


# Singleton instance
production_settings: Optional[ProductionSettings] = None


def get_settings() -> ProductionSettings:
    """Get or create production settings singleton"""
    global production_settings
    if production_settings is None:
        production_settings = get_production_settings()
    return production_settings


def validate_production_config() -> dict:
    """
    Validate production configuration and return status.
    Checks for insecure defaults and missing required settings.
    """
    settings = get_settings()
    issues = []
    warnings = []
    
    # Check for insecure defaults
    insecure_patterns = [
        "CHANGE_THIS",
        "changeme",
        "password",
        "secret",
        "admin",
        "default",
    ]
    
    # Validate SECRET_KEY
    if any(pattern.lower() in settings.SECRET_KEY.lower() for pattern in insecure_patterns):
        issues.append("SECRET_KEY appears to use an insecure default value")
    
    # Validate JWT_SECRET_KEY
    if any(pattern.lower() in settings.JWT_SECRET_KEY.lower() for pattern in insecure_patterns):
        issues.append("JWT_SECRET_KEY appears to use an insecure default value")
    
    # Validate database password
    if any(pattern.lower() in settings.POSTGRES_PASSWORD.lower() for pattern in insecure_patterns):
        warnings.append("POSTGRES_PASSWORD appears to use a weak password")
    
    # Validate Redis password
    if any(pattern.lower() in settings.REDIS_PASSWORD.lower() for pattern in insecure_patterns):
        warnings.append("REDIS_PASSWORD appears to use a weak password")
    
    # Validate MinIO credentials
    if any(pattern.lower() in settings.MINIO_ACCESS_KEY.lower() for pattern in insecure_patterns):
        warnings.append("MINIO_ACCESS_KEY appears to use an insecure default value")
    
    # Check DEBUG is disabled
    if settings.DEBUG:
        issues.append("DEBUG mode is enabled in production - this is a security risk")
    
    # Check ENVIRONMENT
    if settings.ENVIRONMENT != "production":
        warnings.append(f"ENVIRONMENT is set to '{settings.ENVIRONMENT}' but expected 'production'")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "settings_loaded": True,
        "environment": settings.ENVIRONMENT,
        "debug_mode": settings.DEBUG,
    }


if __name__ == "__main__":
    # Validate configuration when run directly
    import json
    
    try:
        validation = validate_production_config()
        print("Production Configuration Validation:")
        print(json.dumps(validation, indent=2))
        
        if not validation["valid"]:
            print("\n❌ Configuration validation FAILED")
            exit(1)
        elif validation["warnings"]:
            print("\n⚠️  Configuration has warnings")
            exit(0)
        else:
            print("\n✅ Configuration validation PASSED")
            exit(0)
    except Exception as e:
        print(f"❌ Error validating configuration: {e}")
        exit(1)
