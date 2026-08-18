import pytest
from decimal import Decimal
from sqlmodel import Session
from models.user import User
from models.transaction import Transaction
from models.ml_task import MLTask
from models.llm_config import LLMConfig
from models.enums import TransactionType, TaskStatus
from services.crud import user as user_crud
from services.crud import balance as balance_crud
from services.crud import transaction as transaction_crud
from services.crud import ml_task as ml_task_crud
from services.auth.auth import get_password_hash

def test_create_user(session: Session):
    user = User(
        username="john",
        email="john@doe.com",
        password_hash=get_password_hash("pass"),
    )
    created = user_crud.create_user(user, session)
    assert created.id is not None
    assert created.balance is not None
    assert created.balance.credits == Decimal("0")

def test_get_user_by_email(session: Session):
    user = User(username="jane", email="jane@doe.com", password_hash="hash")
    session.add(user)
    session.commit()
    found = user_crud.get_user_by_email("jane@doe.com", session)
    assert found is not None
    assert found.username == "jane"

def test_deposit_credits(session: Session, test_user: User):
    updated = balance_crud.deposit_credits(test_user.id, Decimal("10"), session)
    assert updated is not None
    assert updated.credits == Decimal("10")

def test_withdraw_credits(session: Session, test_user: User):
    balance_crud.deposit_credits(test_user.id, Decimal("5"), session)
    updated = balance_crud.withdraw_credits(test_user.id, Decimal("3"), session)
    assert updated.credits == Decimal("2")
    with pytest.raises(ValueError, match="Insufficient credits"):
        balance_crud.withdraw_credits(test_user.id, Decimal("10"), session)

def test_create_transaction(session: Session, test_user: User):
    tx = Transaction(
        user_id=test_user.id,
        amount=Decimal("100"),
        transaction_type=TransactionType.DEPOSIT,
        description="Test deposit",
    )
    created = transaction_crud.create_transaction(tx, session)
    assert created.id is not None
    assert created.status == "pending"

def test_approve_transaction(session: Session, test_user: User):
    balance_crud.create_balance(test_user.id, session)
    tx = Transaction(
        user_id=test_user.id,
        amount=Decimal("100"),
        transaction_type=TransactionType.DEPOSIT,
        description="Test",
    )
    session.add(tx)
    session.commit()
    approved = transaction_crud.approve_transaction(tx.id, session)
    assert approved.status == "approved"
    balance = balance_crud.get_balance_by_user_id(test_user.id, session)
    assert balance.credits == Decimal("3")

def test_create_ml_task(session: Session, test_user: User, llm_config: LLMConfig):
    task = MLTask(
        user_id=test_user.id,
        llm_config_id=llm_config.id,
        input_data={"prompt": "Hello"},
        cost=llm_config.cost_per_request,
    )
    created = ml_task_crud.create_ml_task(task, session)
    assert created.id is not None
    assert created.status == TaskStatus.PENDING.value

def test_complete_ml_task(session: Session, test_user: User, llm_config: LLMConfig):
    task = MLTask(
        user_id=test_user.id,
        llm_config_id=llm_config.id,
        input_data={"prompt": "Test"},
        cost=llm_config.cost_per_request,
        status=TaskStatus.PENDING.value,
    )
    session.add(task)
    session.commit()
    balance_crud.deposit_credits(test_user.id, Decimal("5"), session)
    result = {"response": "OK"}
    completed = ml_task_crud.complete_ml_task(task.id, result, session)
    assert completed.status == TaskStatus.COMPLETED.value
    assert completed.output_data == result

def test_get_tasks_by_user(session: Session, test_user: User, llm_config: LLMConfig):
    for i in range(3):
        task = MLTask(
            user_id=test_user.id,
            llm_config_id=llm_config.id,
            input_data={"prompt": f"Task {i}"},
            cost=llm_config.cost_per_request,
        )
        session.add(task)
    session.commit()
    tasks = ml_task_crud.get_tasks_by_user(test_user.id, session)
    assert len(tasks) == 3