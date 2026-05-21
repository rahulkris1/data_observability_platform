from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Basic application settings"""
    
    # Application
    APP_NAME: str = "Data Observability Platform"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
