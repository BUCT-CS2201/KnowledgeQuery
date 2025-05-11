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
    AIHUBMIX_API_KEY: str = "your-api-key"
    AIHUBMIX_BASE_URL: str = "your-base-url"
    AIHUBMIX_MODEL: str = "your-model"
    
    # Milvus配置
    MILVUS_HOST: str = ""
    MILVUS_PORT: str = ""
    MILVUS_DATABASE: str = ""
    MILVUS_COLLECTION: str = ""

    # Neo4j配置
    NEO4J_URI: str = ""
    NEO4J_USERNAME: str = ""
    NEO4J_PASSWORD: str = ""
    NEO4J_MAX_CONNECTION_LIFETIME: int = 3600
    NEO4J_MAX_CONNECTION_POOL_SIZE: int = 50
    NEO4J_CONNECTION_TIMEOUT: int = 30
    
    # 并行处理配置
    TOKENIZERS_PARALLELISM: bool = False  # 控制HuggingFace tokenizers并行性

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings()

# 设置环境变量以解决警告
import os
os.environ["GRPC_ENABLE_FORK_SUPPORT"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = str(settings.TOKENIZERS_PARALLELISM).lower()

