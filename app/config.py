from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_ENV_FILE), env_file_encoding="utf-8")

    appwrite_endpoint:   str
    appwrite_project_id: str
    appwrite_api_key:    str
    database_id:         str = "roomie_db"
    groq_api_key:        str = ""
    recovery_secret:      str = ""

settings = Settings()  # type: ignore[call-arg]