import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str
    webhook_secret: str | None
    log_level: str


def load_settings() -> Settings:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL must be set")

    return Settings(
        database_url=database_url,
        webhook_secret=os.getenv("WEBHOOK_SECRET"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )
