import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # LLM
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "gemma3:12b"
    OLLAMA_CHAT_MODEL: str = "mistral:latest"
    OLLAMA_WIKI_MODEL: str = "gemma3:12b"
    OLLAMA_TIMEOUT_SECONDS: int = 180
    OLLAMA_CHAT_TIMEOUT_SECONDS: int = 45
    
    # Embedding
    EMBEDDING_MODEL: str = "keepitreal/vietnamese-sbert"
    
    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION_DOCS: str = "legal_docs"
    QDRANT_COLLECTION_WIKI: str = "legal_wiki"
    
    # LangSmith
    LANGCHAIN_TRACING_V2: str = "false"
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = "legalai-vietnam"
    
    class Config:
        env_file = str(Path(__file__).resolve().parents[1] / ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()

# Set up LangSmith automatically if enabled
if settings.LANGCHAIN_TRACING_V2.lower() == "true":
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    if settings.LANGCHAIN_API_KEY:
        os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT
