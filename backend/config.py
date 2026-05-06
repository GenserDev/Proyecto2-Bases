import os
from pydantic_settings import BaseSettings, SettingsConfigDict

_HERE = os.path.dirname(os.path.abspath(__file__))
_ENV_FILE = os.path.join(_HERE, ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, env_file_encoding="utf-8")

    NEO4J_URI: str = "neo4j+s://0baab995.databases.neo4j.io"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = ""
    NEO4J_DATABASE: str = "neo4j"


settings = Settings()
