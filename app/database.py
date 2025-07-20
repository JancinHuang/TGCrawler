from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.engine import Engine
from pydantic_settings import BaseSettings
from functools import lru_cache

# 配置类，读取 .env 文件
class Settings(BaseSettings):
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = "root"
    db_name: str = "telegram_crawler"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

Base = declarative_base()

_engine: Engine | None = None

def get_engine() -> Engine:
    global _engine
    if _engine is None:
        settings = get_settings()
        SQLALCHEMY_DATABASE_URL = (
            f"mysql+pymysql://{settings.db_user}:{settings.db_password}"
            f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
            "?charset=utf8mb4"
        )
        _engine = create_engine(
            SQLALCHEMY_DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False,
        )
    return _engine

# Session 工厂，绑定缓存的 engine
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())

# FastAPI 依赖注入数据库 Session
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
