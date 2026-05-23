from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "ContentPulse"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # OpenAI
    OPENAI_API_KEY: str

    # LangSmith
    LANGCHAIN_API_KEY: str
    LANGCHAIN_TRACING_V2: str = "true"
    LANGCHAIN_PROJECT: str = "contentpulse"

    # Database
    DATABASE_URL: str

    # Model paths
    SENTIMENT_MODEL_PATH: str = "saved_models/sentiment_model"
    FAISS_INDEX_PATH: str = "faiss_index/content_index"

    # HuggingFace
    HF_MODEL_REPO: str = "Venkata1236/contentpulse-sentiment"

    # Recommender weights
    TFIDF_WEIGHT: float = 0.6
    SENTIMENT_WEIGHT: float = 0.4
    SENTIMENT_BOOST_THRESHOLD: float = 0.75
    SENTIMENT_BOOST_MULTIPLIER: float = 1.2
    SENTIMENT_PENALTY_THRESHOLD: float = 0.35
    SENTIMENT_PENALTY_MULTIPLIER: float = 0.8
    HIDDEN_GEM_SENTIMENT_THRESHOLD: float = 0.80

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()