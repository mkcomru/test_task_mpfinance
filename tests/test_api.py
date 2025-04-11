import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import json

from app.db.session import get_db
from app.main import app
from app.models.base import Base

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_secret():
    response = client.post(
        "/secret",
        json={"secret": "test_secret"}
    )
    assert response.status_code == 201
    assert "secret_key" in response.json()


def test_create_secret_with_passphrase():
    response = client.post(
        "/secret",
        json={"secret": "test_secret_with_passphrase", "passphrase": "test_passphrase"}
    )
    assert response.status_code == 201
    assert "secret_key" in response.json()


def test_create_secret_with_ttl():
    response = client.post(
        "/secret",
        json={"secret": "test_secret_with_ttl", "ttl_seconds": 3600}
    )
    assert response.status_code == 201
    assert "secret_key" in response.json()


def test_read_secret():
    create_response = client.post(
        "/secret",
        json={"secret": "test_read_secret"}
    )
    secret_key = create_response.json()["secret_key"]
    
    read_response = client.get(f"/secret/{secret_key}")
    assert read_response.status_code == 200
    assert read_response.json() == {"secret": "test_read_secret"}
    
    second_read_response = client.get(f"/secret/{secret_key}")
    assert second_read_response.status_code == 404


def test_delete_secret():
    create_response = client.post(
        "/secret",
        json={"secret": "test_delete_secret"}
    )
    secret_key = create_response.json()["secret_key"]
    
    delete_response = client.delete(f"/secret/{secret_key}")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"status": "secret_deleted"}
    
    read_response = client.get(f"/secret/{secret_key}")
    assert read_response.status_code == 404


def test_delete_secret_with_passphrase():
    create_response = client.post(
        "/secret",
        json={"secret": "test_delete_secret_with_passphrase", "passphrase": "test_passphrase"}
    )
    secret_key = create_response.json()["secret_key"]
    
    delete_response_without_passphrase = client.delete(f"/secret/{secret_key}")
    assert delete_response_without_passphrase.status_code == 403
    
    delete_response = client.delete(
        f"/secret/{secret_key}",
        headers={"Content-Type": "application/json"},
        content=json.dumps({"passphrase": "test_passphrase"})
    )
    assert delete_response.status_code == 200
    assert delete_response.json() == {"status": "secret_deleted"} 