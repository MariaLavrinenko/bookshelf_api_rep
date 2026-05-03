#Pydantic-схемы для валидации запросов и ответов.

# pylint: disable=missing-module-docstring, missing-class-docstring, missing-function-docstring
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


# ── Аутентификация ──────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    """Схема для регистрации пользователя."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserOut(BaseModel):
    """Ответ после регистрации."""
    id: int
    username: str
    email: str

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """JWT-токен."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None


# ── Книги ─────────────────────────────────────────────────────────────────────

class BookCreate(BaseModel):
    """Схема создания книги."""
    title: str = Field(..., min_length=1, max_length=200)
    author: str = Field(..., min_length=1, max_length=150)
    genre: Optional[str] = Field(None, max_length=100)
    year: Optional[int] = Field(None, ge=0, le=2100)
    description: Optional[str] = None


class BookUpdate(BaseModel):
    """Схема обновления книги."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    author: Optional[str] = Field(None, min_length=1, max_length=150)
    genre: Optional[str] = Field(None, max_length=100)
    year: Optional[int] = Field(None, ge=0, le=2100)
    description: Optional[str] = None


class BookOut(BaseModel):
    """Ответ с информацией о книге."""
    id: int
    title: str
    author: str
    genre: Optional[str]
    year: Optional[int]
    description: Optional[str]

    model_config = {"from_attributes": True}


# ── Отзывы ───────────────────────────────────────────────────────────────────

def _validate_rating(value: float) -> float:
    """Проверяет, что оценка находится в диапазоне 1–5."""
    if not 1.0 <= value <= 5.0:
        raise ValueError("Оценка должна быть от 1 до 5")
    return value


class ReviewCreate(BaseModel):
    """Схема создания отзыва."""
    plot: float
    style: float
    atmosphere: float
    characters: float
    comment: Optional[str] = None

    @field_validator("plot", "style", "atmosphere", "characters")
    @classmethod
    def check_rating(cls, value: float) -> float:
        return _validate_rating(value)


class ReviewOut(BaseModel):
    """Ответ с данными отзыва."""
    id: int
    book_id: int
    user_id: int
    plot: float
    style: float
    atmosphere: float
    characters: float
    comment: Optional[str]

    model_config = {"from_attributes": True}


# ── Рейтинг ────────────────────────────────────────────────────────────

class BookRating(BaseModel):
    """Схема ответа с рейтингом книги."""
    book_id: int
    title: str
    author: str
    review_count: int
    avg_plot: Optional[float]
    avg_style: Optional[float]
    avg_atmosphere: Optional[float]
    avg_characters: Optional[float]
    overall_rating: Optional[float]
