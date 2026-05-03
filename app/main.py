#Bookshelf — REST API для каталога книг на FastAPI.

# pylint: disable=missing-module-docstring
from fastapi import FastAPI

from app.database import Base, engine
from app.routers import auth, books, ratings, reviews

# Создаём все таблицы при запуске (SQLite автоматически создаёт файл БД)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Bookshelf API",
    description=(
        "Каталог книг с пользовательскими рецензиями. "
        "Поддерживает CRUD-операции, JWT-аутентификацию "
        "и многомерный алгоритм расчёта рейтинга книг."
    ),
    version="1.0.0",
)

app.include_router(auth.router)
app.include_router(books.router)
app.include_router(reviews.router)
app.include_router(ratings.router)


@app.get("/", tags=["health"])
def health_check():
    """Простая проверка работоспособности сервиса."""
    return {"status": "ok", "service": "Bookshelf API"}
