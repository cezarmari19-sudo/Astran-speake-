from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """
    Configurare centralizată via variabile de mediu.
    lru_cache garantează o singură instanță (Singleton pattern).
    """
    database_url: str = "sqlite+aiosqlite:///./astran_dev.db"
    secret_key: str = "dev-secret-change-in-production"
    environment: str = "development"
    
    # Constante arhitecturale Zero-Knowledge
    full_id_length: int = 20
    display_id_length: int = 7
    message_expiry_days: int = 14
    media_queue_max_mb: int = 700
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
