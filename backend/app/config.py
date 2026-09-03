from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DATABASE_URL: str = "sqlite+aiosqlite:///./engineering_docs.db"
    UPLOAD_DIR: str = "./uploads"
    REPORTS_DIR: str = "./reports"
    DEFAULT_ADMIN_LOGIN: str = "admin"
    DEFAULT_ADMIN_PASSWORD: str = "Admin@123"
    MAX_FILE_SIZE_MB: int = 100
    ALLOWED_EXTENSIONS: List[str] = ["xls", "xlsx", "doc", "docx", "pdf", "dwg"]

    class Config:
        env_file = ".env"


settings = Settings()
