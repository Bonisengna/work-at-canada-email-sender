import os
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-with-at-least-32-characters")
os.environ.setdefault("USER_SECRETS_ENCRYPTION_KEY", "test-only-placeholder")

from fastapi.testclient import TestClient
from app.core.database import Base, engine
from app.main import app

Base.metadata.create_all(bind=engine)
client = TestClient(app)

def test_register_and_login() -> None:
    credentials = {"email": "pessoa@example.com", "password": "senha-segura"}
    registered = client.post("/api/v1/auth/register", json=credentials)
    assert registered.status_code == 201
    assert registered.json()["access_token"]
    logged_in = client.post("/api/v1/auth/login", json=credentials)
    assert logged_in.status_code == 200
    assert logged_in.json()["user"]["email"] == credentials["email"]

def test_duplicate_and_invalid_password_are_rejected() -> None:
    credentials = {"email": "outra@example.com", "password": "senha-segura"}
    assert client.post("/api/v1/auth/register", json=credentials).status_code == 201
    assert client.post("/api/v1/auth/register", json=credentials).status_code == 409
    invalid = {**credentials, "password": "senha-errada"}
    assert client.post("/api/v1/auth/login", json=invalid).status_code == 401
