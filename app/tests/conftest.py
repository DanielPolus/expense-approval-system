import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.api.dependencies import get_db
from app.core.config import settings
from app.db.base import Base
from app.main import app
from app import models


assert settings.test_database_url is not None

test_engine = create_engine(settings.test_database_url)

TestSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    expire_on_commit=False,
)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(autouse=True)
def clean_database():
    yield

    with test_engine.begin() as connection:
        connection.execute(text("""
            TRUNCATE TABLE
                expense_audits,
                expenses,
                users
            RESTART IDENTITY CASCADE
        """))


@pytest.fixture
def db():
    session = TestSessionLocal()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    def override_get_db():
        db = TestSessionLocal()

        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()