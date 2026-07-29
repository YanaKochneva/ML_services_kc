from dataclasses import dataclass, field
from typing import List
from datetime import datetime
from .balance import Balance
from .base import BaseEntity
from .enums import UserRole, TransactionType
from .transaction import Transaction
from .ml_task import MLTask
import re


@dataclass
class User(BaseEntity):
    """
    Класс пользователя системы.
    """
    username: str
    email: str
    password_hash: str
    balance: Balance = field(init=False)
    role: UserRole = UserRole.USER
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    transactions: List['Transaction'] = field(default_factory=list)
    ml_tasks: List['MLTask'] = field(default_factory=list)

    def __post_init__(self) -> None:
        super().__post_init__()
        self.balance = Balance(id=self.id, user_id=self.id, credits=0)
    
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