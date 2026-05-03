"""CRUD-эндпоинты для отзывов на книги."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Book, Review, User
from app.schemas import ReviewCreate, ReviewOut

router = APIRouter(prefix="/books/{book_id}/reviews", tags=["reviews"])


def _get_book_or_404(book_id: int, db: Session) -> Book:
    """Возвращает книгу или вызывает 404."""
    book = db.query(Book).filter(Book.id == book_id).first()
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Книга не найдена")
    return book


@router.get("/", response_model=List[ReviewOut])
def list_reviews(book_id: int, db: Session = Depends(get_db)):
    """Возвращает все отзывы к книге."""
    _get_book_or_404(book_id, db)
    return db.query(Review).filter(Review.book_id == book_id).all()


@router.post("/", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def create_review(
    book_id: int,
    payload: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Создаёт новый отзыв к книге (требуется авторизация)."""
    _get_book_or_404(book_id, db)
    existing = (
        db.query(Review)
        .filter(Review.book_id == book_id, Review.user_id == current_user.id)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Вы уже оставляли отзыв на эту книгу",
        )
    review = Review(book_id=book_id, user_id=current_user.id, **payload.model_dump())
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    book_id: int,
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Удаляет отзыв (только свой)."""
    review = (
        db.query(Review)
        .filter(Review.id == review_id, Review.book_id == book_id)
        .first()
    )
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Отзыв не найден")
    if review.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нельзя удалять чужой отзыв",
        )
    db.delete(review)
    db.commit()
