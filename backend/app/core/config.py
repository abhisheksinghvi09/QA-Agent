import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "QA Agent API"
    API_V1_STR: str = "/api"
    
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:8501", "http://127.0.0.1:8501"]
    
    GROQ_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    ASSETS_DIR: str = os.path.join(BASE_DIR, "../assets")
    UPLOAD_DIR: str = os.path.join(BASE_DIR, "uploads")
    VECTOR_DB_PATH: str = os.path.join(BASE_DIR, "vector_store_data")

    SESSION_TIMEOUT_MINUTES: int = 60

    BACKEND_ROOT: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    PROJECT_ROOT: str = os.path.dirname(BACKEND_ROOT)
    
    ASSETS_DIR: str = os.path.join(PROJECT_ROOT, "assets")

    class Config:
        env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "../.env")
        extra = "ignore"

settings = Settings()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.VECTOR_DB_PATH, exist_ok=True)