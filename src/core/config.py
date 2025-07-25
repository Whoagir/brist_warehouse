from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # PostgreSQL
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    DATABASE_URL: str

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str
    KAFKA_TOPIC: str

    # Redis
    REDIS_HOST: str
    REDIS_PORT: int

    class Config:
        env_file = "app.env"


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
