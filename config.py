from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str
    tavily_api_key: str
    manager_model: str = "claude-sonnet-4-6"
    worker_model: str = "claude-haiku-4-5"
    synthesis_model: str = "claude-sonnet-4-6"
    chroma_db_path: str = "./chroma_db"
    max_subtopics: int = 5
    similarity_threshold: float = 0.85

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
