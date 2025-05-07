from pydantic_settings import BaseSettings

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
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

