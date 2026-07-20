"""
Startup validation utility to check required configurations and services.
Validates that all required environment variables and external services are available.
"""

import logging
from typing import Dict, List, Tuple
from app.core.config import settings
from app.core.redis_client import RedisClient

logger = logging.getLogger(__name__)


class StartupValidator:
    """Validates application configuration and dependencies at startup."""
    
    def __init__(self):
        self.validation_results: Dict[str, bool] = {}
        self.warnings: List[str] = []
        self.errors: List[str] = []
    
    def validate_all(self) -> Tuple[bool, List[str], List[str]]:
        """
        Run all startup validations.
        
        Returns:
            Tuple of (is_valid, warnings, errors)
        """
        logger.info("Running startup validations...")
        
        # Validate database configuration
        self._validate_database()
        
        # Validate storage configuration
        self._validate_storage()
        
        # Validate cache configuration
        self._validate_cache()
        
        # Validate authentication configuration
        self._validate_auth()
        
        # Validate AWS configuration (optional)
        self._validate_aws()
        
        # Log results
        self._log_results()
        
        # Return validation summary
        is_valid = len(self.errors) == 0
        return is_valid, self.warnings, self.errors
    
    def _validate_database(self) -> None:
        """Validate database configuration."""
        try:
            if not settings.DATABASE_URL:
                self.errors.append("DATABASE_URL is not configured")
                self.validation_results["database"] = False
                return
            
            # Check if using SQLite in production (warning)
            if not settings.DEBUG and settings.DATABASE_URL.startswith("sqlite"):
                self.warnings.append("SQLite is not recommended for production use")
            
            # Try to create engine (don't connect yet)
            from app.core.database import engine
            logger.info(f"Database configured: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'SQLite'}")
            self.validation_results["database"] = True
            
        except Exception as e:
            self.errors.append(f"Database validation failed: {str(e)}")
            self.validation_results["database"] = False
    
    def _validate_storage(self) -> None:
        """Validate storage provider configuration."""
        try:
            provider = settings.STORAGE_PROVIDER.lower()
            
            if provider == "minio":
                if not settings.MINIO_ENDPOINT:
                    self.errors.append("MINIO_ENDPOINT is required when using MinIO")
                    self.validation_results["storage"] = False
                    return
                
                if not settings.MINIO_ACCESS_KEY or not settings.MINIO_SECRET_KEY:
                    self.errors.append("MINIO_ACCESS_KEY and MINIO_SECRET_KEY are required")
                    self.validation_results["storage"] = False
                    return
                
                logger.info(f"Storage provider configured: MinIO at {settings.MINIO_ENDPOINT}")
                
            elif provider == "s3":
                if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
                    self.errors.append("AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are required for S3")
                    self.validation_results["storage"] = False
                    return
                
                logger.info(f"Storage provider configured: AWS S3 in {settings.AWS_REGION}")
                
            else:
                self.errors.append(f"Invalid STORAGE_PROVIDER: {provider}. Must be 'minio' or 's3'")
                self.validation_results["storage"] = False
                return
            
            self.validation_results["storage"] = True
            
        except Exception as e:
            self.errors.append(f"Storage validation failed: {str(e)}")
            self.validation_results["storage"] = False
    
    def _validate_cache(self) -> None:
        """Validate Redis cache configuration."""
        try:
            if not settings.REDIS_HOST:
                self.warnings.append("Redis not configured - caching will be disabled")
                self.validation_results["cache"] = False
                return
            
            # Try to connect to Redis
            try:
                is_connected = RedisClient.check_connection()
                if is_connected:
                    logger.info(f"Redis configured and connected: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
                    self.validation_results["cache"] = True
                else:
                    self.warnings.append("Redis configured but connection failed - caching will operate in degraded mode")
                    self.validation_results["cache"] = False
            except Exception as e:
                self.warnings.append(f"Redis connection check failed: {str(e)} - caching will operate in degraded mode")
                self.validation_results["cache"] = False
                
        except Exception as e:
            self.warnings.append(f"Cache validation failed: {str(e)}")
            self.validation_results["cache"] = False
    
    def _validate_auth(self) -> None:
        """Validate authentication configuration."""
        try:
            # Check JWT configuration
            from app.core.config import settings
            
            # Check if JWT secret is set (if using JWT)
            if hasattr(settings, 'JWT_SECRET_KEY'):
                if not settings.JWT_SECRET_KEY or settings.JWT_SECRET_KEY == "your-secret-key-here":
                    self.warnings.append("JWT_SECRET_KEY should be changed from default value in production")
            
            logger.info("Authentication configuration validated")
            self.validation_results["auth"] = True
            
        except Exception as e:
            self.errors.append(f"Authentication validation failed: {str(e)}")
            self.validation_results["auth"] = False
    
    def _validate_aws(self) -> None:
        """Validate AWS configuration (optional)."""
        try:
            # AWS is optional, only validate if credentials are provided
            if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
                logger.info(f"AWS credentials configured for region: {settings.AWS_REGION}")
                self.validation_results["aws"] = True
            else:
                logger.info("AWS credentials not configured (optional)")
                self.validation_results["aws"] = None  # Optional
                
        except Exception as e:
            self.warnings.append(f"AWS validation failed: {str(e)}")
            self.validation_results["aws"] = False
    
    def _log_results(self) -> None:
        """Log validation results."""
        logger.info("=" * 60)
        logger.info("Startup Validation Results:")
        logger.info("=" * 60)
        
        for component, result in self.validation_results.items():
            if result is True:
                status = "✓ PASSED"
            elif result is False:
                status = "✗ FAILED"
            else:
                status = "○ OPTIONAL"
            logger.info(f"{component.upper()}: {status}")
        
        if self.warnings:
            logger.warning(f"\nWarnings ({len(self.warnings)}):")
            for warning in self.warnings:
                logger.warning(f"  - {warning}")
        
        if self.errors:
            logger.error(f"\nErrors ({len(self.errors)}):")
            for error in self.errors:
                logger.error(f"  - {error}")
        
        logger.info("=" * 60)


def run_startup_validation() -> Tuple[bool, List[str], List[str]]:
    """
    Run startup validation and return results.
    
    Returns:
        Tuple of (is_valid, warnings, errors)
    """
    validator = StartupValidator()
    return validator.validate_all()
