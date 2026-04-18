import os
os.environ.setdefault("RATELIMIT_ENABLED", "False")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from app.main import app
from app.db.base import Base
from app.db.session import get_db

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    # Seed admin diretamente na sessão de teste (antes do startup event)
    from app.modules.auth.models import RoleEnum
    from app.modules.auth.repository import create_usuario
    from app.modules.auth.schemas import UsuarioCreate
    create_usuario(db, UsuarioCreate(username="admin", password="admin123", role=RoleEnum.ADMIN))

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def auth_headers(client):
    """Token de ADMIN."""
    resp = client.post("/auth/token", data={"username": "admin", "password": "admin123"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def atendente_headers(client, db):
    """Token de ATENDENTE."""
    from app.modules.auth.models import RoleEnum
    from app.modules.auth.repository import create_usuario
    from app.modules.auth.schemas import UsuarioCreate
    create_usuario(db, UsuarioCreate(username="atendente", password="atend123", role=RoleEnum.ATENDENTE))
    resp = client.post("/auth/token", data={"username": "atendente", "password": "atend123"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
