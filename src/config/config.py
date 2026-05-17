from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    """Configuracion de la aplicacion leida desde variables de entorno."""

    log_level: LogLevel = "INFO"
    app_host: str = "127.0.0.1"
    app_port: int = 8050
    app_debug: bool = False

    @field_validator("log_level", mode="before")
    @classmethod
    def normalize_log_level(cls, value: object) -> object:
        """Normaliza el nivel de logs a mayusculas."""
        if isinstance(value, str):
            return value.upper()

        return value

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
