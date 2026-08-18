import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool

from api import app
from database.database import get_session
from models.user import User
from models.llm_config import LLMConfig
from services.auth.auth import get_password_hash

@pytest.fixture(scope="function")
def session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(scope="function")
def client(session: Session):
    def override_get_session():
        yield session
    app.dependency_overrides[get_session] = override_get_session
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def auth_headers(client: TestClient, session: Session):
    import time
    unique = str(int(time.time() * 1000))
    username = f"testuser_{unique}"
    email = f"test_{unique}@example.com"
    password = "secret123"
    signup_data = {"username": username, "email": email, "password_hash": password}
    response = client.post("/api/users/signup", json=signup_data)
    assert response.status_code == 201, response.text
    login_data = {"username": email, "password": password}
    response = client.post("/api/auth/login", data=login_data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
def llm_config(session: Session):
    from models.llm_config import LLMConfig
    config = LLMConfig(
        name="Qwen2.5-1.5B-Instruct",
        version="1.0",
        cost_per_request=1,
        is_active=True,
        max_prompt_length=4000,
    )
    session.add(config)
    session.commit()
    session.refresh(config)
    return config

@pytest.fixture(scope="function")
def test_user(session: Session):
    user = User(
        username="dbuser",
        email="db@example.com",
        password_hash=get_password_hash("dbpass"),
        role="USER",
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user