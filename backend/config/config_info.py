from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # 数据库配置
    MYSQL_IP: str
    MYSQL_PORT: str
    MYSQL_BASE: str
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    
    # JWT配置
    SECRET_KEY: str
    
    # LLM API配置
    AIHUBMIX_API_KEY: str
    AIHUBMIX_BASE_URL: str = "https://aihubmix.com/v1"
    AIHUBMIX_MODEL: str = "Qwen/Qwen3-30B-A3B"
    
    # Milvus配置
    MILVUS_HOST: str = "127.0.0.1"
    MILVUS_PORT: str = "19530"
    MILVUS_DATABASE: str = "default"
    MILVUS_COLLECTION: str = "RAG"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings()

