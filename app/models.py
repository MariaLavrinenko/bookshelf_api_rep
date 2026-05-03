#Модели SQLAlchemy ORM для приложения Bookshelf.

# pylint: disable=missing-module-docstring, not-callable, too-few-public-methods
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
    DateTime,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# pylint: disable=not-callable, too-few-public-methods   ←←← ДОБАВЬ ЭТУ СТРОКУ

from app.database import Base


class User(Base):
    """Зарегистрированный пользователь приложения."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    reviews = relationship("Review", back_populates="author", cascade="all, delete-orphan")


class Book(Base):
    """Запись книги в каталоге."""

    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    author = Column(String(150), nullable=False)
    genre = Column(String(100), nullable=True)
    year = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    reviews = relationship("Review", back_populates="book", cascade="all, delete-orphan")


class Review(Base):
    """Отзыв пользователя на книгу с четырьмя параметрами оценки (1-5)."""

    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plot = Column(Float, nullable=False)        # 1–5: plot / story
    style = Column(Float, nullable=False)       # 1–5: author's writing style
    atmosphere = Column(Float, nullable=False)  # 1–5: atmosphere / mood
    characters = Column(Float, nullable=False)  # 1–5: characters
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    book = relationship("Book", back_populates="reviews")
    author = relationship("User", back_populates="reviews")
