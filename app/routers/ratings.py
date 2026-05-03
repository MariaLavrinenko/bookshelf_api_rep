"""
Каждая рецензия оценивает книгу по четырём параметрам по шкале от 1 до 5:
  - plot – качество сюжета / истории
  - style – стиль письма автора
  - atmosphere – атмосфера и настроение произведения
  - characters – проработка персонажей

Общий (итоговый) рейтинг книги рассчитывается по формуле:

    overall = mean(avg_plot, avg_style, avg_atmosphere, avg_characters)

где каждое avg_* — это среднее арифметическое соответствующего параметра
по всем рецензиям.
Книги без рецензий возвращаются с пустыми (null) полями рейтинга.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Book, Review
from app.schemas import BookRating

router = APIRouter(prefix="/ratings", tags=["ratings"])


def _compute_rating(
    book: Book, db: Session
) -> BookRating:
    """Возвращает агрегированные данные рейтинга для книги."""
    row = (
        db.query(
            func.count(Review.id).label("review_count"),  # pylint: disable=not-callable
            func.avg(Review.plot).label("avg_plot"),
            func.avg(Review.style).label("avg_style"),
            func.avg(Review.atmosphere).label("avg_atmosphere"),
            func.avg(Review.characters).label("avg_characters"),
        )
        .filter(Review.book_id == book.id)
        .one()
    )

    review_count: int = row.review_count or 0
    avg_plot: Optional[float] = round(row.avg_plot, 2) if row.avg_plot else None
    avg_style: Optional[float] = round(row.avg_style, 2) if row.avg_style else None
    avg_atmosphere: Optional[float] = (
        round(row.avg_atmosphere, 2) if row.avg_atmosphere else None
    )
    avg_characters: Optional[float] = (
        round(row.avg_characters, 2) if row.avg_characters else None
    )

    if review_count > 0:
        overall = round(
            (avg_plot + avg_style + avg_atmosphere + avg_characters) / 4, 2
        )
    else:
        overall = None

    return BookRating(
        book_id=book.id,
        title=book.title,
        author=book.author,
        review_count=review_count,
        avg_plot=avg_plot,
        avg_style=avg_style,
        avg_atmosphere=avg_atmosphere,
        avg_characters=avg_characters,
        overall_rating=overall,
    )


@router.get("/books/{book_id}", response_model=BookRating)
def get_book_rating(book_id: int, db: Session = Depends(get_db)):
    """
    Возвращает агрегированный рейтинг для одной книги.

    Общий рейтинг — это среднее арифметическое четырёх средних значений параметров
    (plot, style, atmosphere, characters), каждое из которых усреднено по всем рецензиям.
    """
    book = db.query(Book).filter(Book.id == book_id).first()
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Книга не найдена")
    return _compute_rating(book, db)


@router.get("/top", response_model=List[BookRating])
def get_top_books(
    limit: int = Query(10, ge=1, le=100),
    min_reviews: int = Query(1, ge=1),
    db: Session = Depends(get_db),
):
    """
    Возвращает топ книг, отсортированных по убыванию общего рейтинга.

    В результат включаются только книги, у которых не менее *min_reviews* рецензий.
    Этот эндпоинт реализует основную бизнес-логику проекта — ранжирование каталога
    по многомерному вычисляемому рейтингу.
    """
    books = db.query(Book).all()

    ratings = [_compute_rating(book, db) for book in books]

    # Фильтр книг, которые имеют достаточное количество рецензий
    # и поддающийся вычислению рейтинг
    qualified = [
        r for r in ratings
        if r.review_count >= min_reviews and r.overall_rating is not None
    ]

    # Сортировка по общему рейтингу в порядке убывания,
    # затем в алфавитном порядке для стабильного результата
    qualified.sort(key=lambda r: (-r.overall_rating, r.title))

    return qualified[:limit]
