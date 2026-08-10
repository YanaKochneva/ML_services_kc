from sqlmodel import SQLModel, Field, Relationship
from dataclasses import dataclass, field
from typing import List, TYPE_CHECKING, Optional
from datetime import datetime
from .balance import Balance
from .base import BaseEntity
from .enums import UserRole, TransactionType
from .transaction import Transaction
from .ml_task import MLTask
import re

if TYPE_CHECKING:
    from .transaction import Transaction
    from .ml_task import MLTask
    from .balance import Balance

@dataclass
class User(SQLModel, table=True):
    """"
    Класс пользователя системы.
    
    Attributes:
        id (int): Primary key
        username (str): Имя пользователя
        email (str): Email пользователя
        password_hash (str): Хэш пароля
        role (str): Роль пользователя
        created_at (datetime): Дата создания
        is_active (bool): Активен ли пользователь
        balance (Balance): Баланс пользователя (one-to-one)
        transactions (List[Transaction]): Список транзакций
        ml_tasks (List[MLTask]): Список ML задач
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(
        ...,  
        unique=True,
        index=True,
        min_length=3,
        max_length=50
    )
    email: str = Field(
        ...,  
        unique=True,
        index=True,
        max_length=255
    )
    password_hash: str = Field(..., min_length=4, max_length=255)
    role: str = Field(default="USER", max_length=20)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
    balance: "Balance" = Relationship(
        back_populates="user",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "lazy": "selectin"
        }
    )
    
    transactions: List["Transaction"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "lazy": "selectin"
        }
    )
    
    ml_tasks: List["MLTask"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "lazy": "selectin"
        }
    )
    
    # def __post_init__(self) -> None:
    #     super().__post_init__()
    #     self.balance = Balance(id=self.id, user_id=self.id, credits=0)
    
    def validate(self) -> None:
        """Валидация данных пользователя."""
        self._validate_username()
        self._validate_email()
    
    def _validate_username(self) -> None:
        """Проверка имени пользователя."""
        if not self.username or len(self.username) < 3:
            raise ValueError("Username must be at least 3 characters")
        if not re.match(r'^[a-zA-Z0-9_]+$', self.username):
            raise ValueError("Username can only contain letters, numbers and underscore")
    
    def _validate_email(self) -> None:
        """Проверка email."""
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if not email_pattern.match(self.email):
            raise ValueError("Invalid email format")
    
    def add_transaction(self, transaction: 'Transaction') -> None:
        """Добавление транзакции."""
        self.transactions.append(transaction)
        if transaction.transaction_type == TransactionType.DEPOSIT:
            credits = Balance.rub_to_credits(transaction.amount)
            self.balance.deposit(credits)
        elif transaction.transaction_type == TransactionType.WITHDRAW:
            credits = Balance.rub_to_credits(transaction.amount)
            self.balance.withdraw(credits)
    
    def add_ml_task(self, task: 'MLTask') -> None:
        """Добавление ML задачи."""
        self.ml_tasks.append(task)
    
    def can_perform_task(self, cost: int) -> bool:
        return self.balance.has_enough(cost)