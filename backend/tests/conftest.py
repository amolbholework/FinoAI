import os
import uuid

os.environ["DATABASE_URL"] = f"sqlite:///./test_{uuid.uuid4().hex}.db"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.core.database import Base, get_db
from app.main import app

settings = get_settings()
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def _create_schema():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    db_path = settings.database_url.replace("sqlite:///", "")
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture()
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def _override_get_db():
    def _get_test_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture()
def client():
    with TestClient(app) as c:  # triggers the startup event (system category seeding)
        yield c


@pytest.fixture()
def test_user(db_session):
    from app.models.user import User

    # Unique per invocation — the schema is created once per test session
    # (not rolled back between tests), so a fixed google_sub would collide
    # the moment more than one test in a file uses this fixture.
    unique = uuid.uuid4().hex[:8]
    user = User(google_sub=f"test-google-sub-{unique}", email=f"test-{unique}@example.com", name="Test User")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def auth_client(client, test_user):
    """A TestClient carrying a valid session cookie for `test_user` — for
    exercising routes that require `get_current_user`."""
    from app.core.security import create_access_token

    client.cookies.set("fp_access", create_access_token(test_user))
    return client
