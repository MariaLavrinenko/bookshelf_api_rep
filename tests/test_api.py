"""Автоматические тесты для API Bookshelf с использованием FastAPI TestClient.."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db

TEST_DATABASE_URL = "sqlite:///./test_bookshelf.db"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    """Переопределяет зависимость get_db для использования тестовой БД."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


from app.main import app  # noqa: E402

app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def reset_db():
    """Пересоздаём таблицы перед каждым тестом для изоляции."""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


client = TestClient(app)


# ── Вспомогательные функции ───────────────────────────────────────────────────────────────────

def register_and_login(username="testuser", password="secret123"):
    """Регистрирует пользователя и возвращает JWT-токен."""
    client.post(
        "/auth/register",
        json={"username": username, "email": f"{username}@example.com", "password": password},
    )
    resp = client.post(
        "/auth/login",
        data={"username": username, "password": password},
    )
    return resp.json()["access_token"]


def auth_headers(token):
    """Возвращает заголовки с JWT-токеном для авторизованных запросов."""
    return {"Authorization": f"Bearer {token}"}


# ── Тесты аутентификации ────────────────────────────────────────────────────────────────

class TestAuth:
    def test_register_success(self):
        resp = client.post(
            "/auth/register",
            json={"username": "bob", "email": "bob@example.com", "password": "password1"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["username"] == "bob"
        assert "id" in data

    def test_register_duplicate_username(self):
        client.post(
            "/auth/register",
            json={"username": "bob", "email": "bob@example.com", "password": "password1"},
        )
        resp = client.post(
            "/auth/register",
            json={"username": "bob", "email": "bob2@example.com", "password": "password1"},
        )
        assert resp.status_code == 400

    def test_login_success(self):
        client.post(
            "/auth/register",
            json={"username": "carol", "email": "carol@example.com", "password": "pass1234"},
        )
        resp = client.post("/auth/login", data={"username": "carol", "password": "pass1234"})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_login_wrong_password(self):
        client.post(
            "/auth/register",
            json={"username": "dave", "email": "dave@example.com", "password": "rightpass"},
        )
        resp = client.post("/auth/login", data={"username": "dave", "password": "wrongpass"})
        assert resp.status_code == 401


# ── Тесты книг ────────────────────────────────────────────────────────────────

class TestBooks:
    def test_create_book_requires_auth(self):
        resp = client.post(
            "/books/",
            json={"title": "Test Book", "author": "Author"},
        )
        assert resp.status_code == 401

    def test_create_book(self):
        token = register_and_login()
        resp = client.post(
            "/books/",
            json={"title": "Dune", "author": "Frank Herbert", "year": 1965},
            headers=auth_headers(token),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Dune"
        assert data["author"] == "Frank Herbert"

    def test_list_books(self):
        token = register_and_login()
        client.post(
            "/books/",
            json={"title": "Book A", "author": "Author A"},
            headers=auth_headers(token),
        )
        resp = client.get("/books/")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_get_book_not_found(self):
        resp = client.get("/books/999")
        assert resp.status_code == 404

    def test_update_book(self):
        token = register_and_login()
        create_resp = client.post(
            "/books/",
            json={"title": "Old Title", "author": "Author"},
            headers=auth_headers(token),
        )
        book_id = create_resp.json()["id"]
        resp = client.put(
            f"/books/{book_id}",
            json={"title": "New Title"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "New Title"

    def test_delete_book(self):
        token = register_and_login()
        create_resp = client.post(
            "/books/",
            json={"title": "To Delete", "author": "Author"},
            headers=auth_headers(token),
        )
        book_id = create_resp.json()["id"]
        resp = client.delete(f"/books/{book_id}", headers=auth_headers(token))
        assert resp.status_code == 204
        assert client.get(f"/books/{book_id}").status_code == 404


# ── Тесты отзывов ──────────────────────────────────────────────────────────────

class TestReviews:
    def _create_book(self, token):
        """Создаёт тестовую книгу и возвращает её id."""
        resp = client.post(
            "/books/",
            json={"title": "Reviewed Book", "author": "Some Author"},
            headers=auth_headers(token),
        )
        return resp.json()["id"]

    def test_create_review(self):
        token = register_and_login()
        book_id = self._create_book(token)
        resp = client.post(
            f"/books/{book_id}/reviews/",
            json={"plot": 4.0, "style": 5.0, "atmosphere": 3.5, "characters": 4.5},
            headers=auth_headers(token),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["plot"] == 4.0

    def test_duplicate_review_rejected(self):
        token = register_and_login()
        book_id = self._create_book(token)
        client.post(
            f"/books/{book_id}/reviews/",
            json={"plot": 4.0, "style": 4.0, "atmosphere": 4.0, "characters": 4.0},
            headers=auth_headers(token),
        )
        resp = client.post(
            f"/books/{book_id}/reviews/",
            json={"plot": 3.0, "style": 3.0, "atmosphere": 3.0, "characters": 3.0},
            headers=auth_headers(token),
        )
        assert resp.status_code == 400

    def test_review_rating_out_of_range(self):
        token = register_and_login()
        book_id = self._create_book(token)
        resp = client.post(
            f"/books/{book_id}/reviews/",
            json={"plot": 6.0, "style": 4.0, "atmosphere": 4.0, "characters": 4.0},
            headers=auth_headers(token),
        )
        assert resp.status_code == 422


# ── Тесты рейтинга (бизнес-логика) ────────────────────────────────────────────

class TestRatings:
    def _setup(self):
        """Создаёт книгу и один отзыв для тестов рейтинга."""
        token = register_and_login()
        resp = client.post(
            "/books/",
            json={"title": "Great Book", "author": "Great Author"},
            headers=auth_headers(token),
        )
        book_id = resp.json()["id"]
        client.post(
            f"/books/{book_id}/reviews/",
            json={"plot": 4.0, "style": 5.0, "atmosphere": 3.0, "characters": 4.0},
            headers=auth_headers(token),
        )
        return book_id, token

    def test_book_rating_no_reviews(self):
        token = register_and_login()
        resp = client.post(
            "/books/",
            json={"title": "Unreviewed", "author": "Author"},
            headers=auth_headers(token),
        )
        book_id = resp.json()["id"]
        resp = client.get(f"/ratings/books/{book_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["review_count"] == 0
        assert data["overall_rating"] is None

    def test_book_rating_calculated(self):
        book_id, _ = self._setup()
        resp = client.get(f"/ratings/books/{book_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["review_count"] == 1
        # (4+5+3+4)/4 = 4.0
        assert data["overall_rating"] == pytest.approx(4.0, abs=0.01)

    def test_top_books(self):
        book_id, token = self._setup()
        resp = client.get("/ratings/top?min_reviews=1")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1
        assert resp.json()[0]["book_id"] == book_id

    def test_top_books_min_reviews_filter(self):
        """Книги с количеством рецензий меньше min_reviews должны быть исключены."""
        self._setup()  # book with 1 review
        resp = client.get("/ratings/top?min_reviews=2")
        assert resp.status_code == 200
        assert len(resp.json()) == 0