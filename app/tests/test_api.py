import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session
from models.enums import TransactionType, TaskStatus

def test_signup_and_login(client: TestClient):
    resp = client.post("/api/users/signup", json={
        "username": "apiuser",
        "email": "api@test.com",
        "password_hash": "pass"
    })
    assert resp.status_code == 201
    assert resp.json()["message"] == "User successfully registered"

    resp = client.post(
        "/api/auth/login",
        data={"username": "api@test.com", "password": "pass"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    assert token is not None


def test_signup_duplicate_email(client: TestClient):
    client.post("/api/users/signup", json={
        "username": "dup1", "email": "dup@test.com", "password_hash": "pass"
    })
    resp = client.post("/api/users/signup", json={
        "username": "dup2", "email": "dup@test.com", "password_hash": "pass"
    })
    assert resp.status_code == 409
    assert "already exists" in resp.text


def test_get_me(client: TestClient, auth_headers):
    resp = client.get("/api/users/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"].endswith("@example.com")
    assert data["username"].startswith("testuser_")


def test_get_balance(client: TestClient, auth_headers):
    resp = client.get("/api/balance/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["credits"] == 0.0


def test_deposit_credits(client: TestClient, auth_headers):
    resp = client.post("/api/balance/me/deposit", json={"credits": 10}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["credits"] == 10.0

    resp = client.get("/api/balance/me", headers=auth_headers)
    assert resp.json()["credits"] == 10.0


def test_withdraw_insufficient(client: TestClient, auth_headers):
    resp = client.post("/api/balance/me/withdraw", json={"credits": 5}, headers=auth_headers)
    assert resp.status_code == 400
    assert "Insufficient balance" in resp.text


def test_ml_task_success(client: TestClient, auth_headers, llm_config):
    client.post("/api/balance/me/deposit", json={"credits": 5}, headers=auth_headers)

    task_data = {
        "user_id": 0,
        "llm_config_id": llm_config.id,
        "input_data": {"prompt": "Расскажи стихотворение"},
    }
    resp = client.post("/api/ml-tasks/create", json=task_data, headers=auth_headers)
    assert resp.status_code == 201
    task = resp.json()
    assert task["status"] == TaskStatus.COMPLETED.value
    assert float(task["cost"]) == float(llm_config.cost_per_request)
    assert "output_data" in task

    bal = client.get("/api/balance/me", headers=auth_headers)
    assert bal.json()["credits"] == 4.0  # 5 - 1


def test_ml_task_insufficient_balance(client: TestClient, auth_headers, llm_config):
    task_data = {
        "user_id": 0,
        "llm_config_id": llm_config.id,
        "input_data": {"prompt": "test"},
    }
    resp = client.post("/api/ml-tasks/create", json=task_data, headers=auth_headers)
    assert resp.status_code == 400
    assert "Insufficient balance" in resp.text


def test_ml_task_validation_error(client: TestClient, auth_headers, llm_config):
   
    client.post("/api/balance/me/deposit", json={"credits": 1}, headers=auth_headers)

    task_data = {
        "user_id": 0,
        "llm_config_id": llm_config.id,
        "input_data": {"prompt": ""},
    }
    resp = client.post("/api/ml-tasks/create", json=task_data, headers=auth_headers)
    assert resp.status_code == 201
    task = resp.json()
    assert task["status"] == TaskStatus.VALIDATION_ERROR.value
    assert len(task["validation_errors"]) > 0

    bal = client.get("/api/balance/me", headers=auth_headers)
    assert bal.json()["credits"] == 1.0


def test_ml_task_missing_config(client: TestClient, auth_headers):
    client.post("/api/balance/me/deposit", json={"credits": 1}, headers=auth_headers)
    task_data = {
        "user_id": 0,
        "llm_config_id": 999,
        "input_data": {"prompt": "test"},
    }
    resp = client.post("/api/ml-tasks/create", json=task_data, headers=auth_headers)
    assert resp.status_code == 404
    assert "LLM config not found" in resp.text


def test_transaction_history(client: TestClient, auth_headers, llm_config):
    client.post("/api/balance/me/deposit", json={"credits": 10}, headers=auth_headers)
    client.post(
        "/api/ml-tasks/create",
        json={"user_id": 0, "llm_config_id": llm_config.id, "input_data": {"prompt": "history"}},
        headers=auth_headers,
    )

    resp = client.get("/api/transactions/me", headers=auth_headers)
    assert resp.status_code == 200
    txs = resp.json()
    assert len(txs) >= 2
    types = [t["transaction_type"] for t in txs]
    assert TransactionType.DEPOSIT.value in types
    assert TransactionType.WITHDRAW.value in types


def test_ml_task_history(client: TestClient, auth_headers, llm_config):
    client.post("/api/balance/me/deposit", json={"credits": 5}, headers=auth_headers)
    client.post(
        "/api/ml-tasks/create",
        json={"user_id": 0, "llm_config_id": llm_config.id, "input_data": {"prompt": "history test"}},
        headers=auth_headers,
    )

    resp = client.get("/api/ml-tasks/", headers=auth_headers)
    assert resp.status_code == 200
    tasks = resp.json()
    assert len(tasks) >= 1
    assert tasks[0]["input_data"]["prompt"] == "history test"