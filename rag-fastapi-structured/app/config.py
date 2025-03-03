from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    MODEL_NAME: str = "deepseek-r1:8b"
    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    DOCUMENT_PATH: str = "./document"
    PERSIST_DIR: str = "./data"  # ChromaDB 데이터 영구 저장 경로
    
    class Config:
        env_file = ".env"

settings = Settings()
