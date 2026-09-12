from pydantic_settings import BaseSettings, SettingsConfigDict
from zoneinfo import ZoneInfo
from datetime import datetime

class Settings(BaseSettings):
    database_url: str = 'postgresql+psycopg://pharmacy:pharmacy@localhost:5432/pharmacy'
    secret_key: str
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.8-flash"
    cors_origins: str = 'http://localhost:5173,http://127.0.0.1:5173'
    cookie_secure: bool = False
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

settings = Settings()
if len(settings.secret_key) < 32:
    raise ValueError('SECRET_KEY phải có ít nhất 32 ký tự. Chạy scripts/setup.py.')

def today():
    return datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).date()
