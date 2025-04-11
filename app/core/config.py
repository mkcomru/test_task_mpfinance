import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

class Settings:
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "secret_service")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    
    DATABASE_URL: str = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: str = os.getenv("REDIS_PORT", "6379")
    REDIS_URL: str = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "insecure_key_change_me")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    
    TTL_DEFAULT: int = int(os.getenv("TTL_DEFAULT", "3600"))
    CACHE_MIN_TTL: int = int(os.getenv("CACHE_MIN_TTL", "300"))

settings = Settings() 