import os
from typing import Any, Dict, List, Optional

from pydantic_settings import BaseSettings
from pydantic import validator, field_validator


class Settings(BaseSettings):
    GOOGLE_API_KEY: Optional[str] = None
    # Configuración general
    APP_NAME: str = "NutriVeci"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8080
    
    # Seguridad
    SECRET_KEY: str = "development_secret_key"  # Cambiar en producción
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ACCESS_TOKEN_EXPIRE_DAYS: int = 30
    
    # CORS
    CORS_ORIGINS: Optional[List[str]] = []

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def split_cors_origins(cls, v):
        if v is None or v == "":
            return []
        if isinstance(v, str):
            # Soporta cadenas separadas por comas o una sola URL
            if v.startswith("[") and v.endswith("]"):  # JSON
                import json
                return json.loads(v)
            return [i.strip() for i in v.split(",") if i.strip()]
        return v
    
    # HuggingFace
    HF_TOKEN: Optional[str] = None

    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_JWT_SECRET: Optional[str] = None
    
    # Telegram
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    
    # Sesiones
    SESSION_COOKIE_NAME: str = "nutriveci_session"
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "lax"
    
    # WhatsApp (opcional)
    WHATSAPP_ENABLED: bool = False
    WHATSAPP_TWILIO_ACCOUNT_SID: Optional[str] = None
    WHATSAPP_TWILIO_AUTH_TOKEN: Optional[str] = None
    WHATSAPP_PHONE_NUMBER: Optional[str] = None
    
    @validator("ENVIRONMENT")
    def environment_must_be_valid(cls, v: str) -> str:
        valid_environments = ["development", "staging", "production"]
        if v.lower() not in valid_environments:
            raise ValueError(f"Environment must be one of {valid_environments}")
        return v.lower()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Instancia de configuración global
settings = Settings()


def get_settings() -> Settings:
    return settings 