#Настройка подключения к базе данных и сессий.

# pylint: disable=missing-module-docstring, invalid-name
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./bookshelf.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Создаёт и возвращает сессию БД."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
