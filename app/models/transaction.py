from dataclasses import dataclass, field
from .base import BaseEntity
from .enums import TransactionType
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from decimal import Decimal

if TYPE_CHECKING:
    from .user import User

@dataclass
class Transaction(SQLModel, table=True):
    """
    Класс транзакции (пополнение или списание).
    
    Attributes:
        id (int): Primary key
        user_id (int): Foreign key to User
        amount (Decimal): Сумма транзакции
        transaction_type (TransactionType): Тип транзакции
        description (str): Описание транзакции
        created_at (datetime): Дата создания
        status (str): Статус транзакции (pending, approved, rejected)
        user (User): Связанный пользователь
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    amount: Decimal = Field(..., max_digits=10, decimal_places=2)
    transaction_type: TransactionType = Field(...)
    description: str = Field(default="", max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="pending", max_length=20)
    
    user: "User" = Relationship(back_populates="transactions")
    
    def validate(self) -> None:
        """Валидация транзакции."""
        if self.amount <= 0:
            raise ValueError("Transaction amount must be positive")
        if self.user_id <= 0:
            raise ValueError("Invalid user ID")
    
    def approve(self) -> None:
        """Подтверждение транзакции (для администратора)."""
        if self.status != "pending":
            raise ValueError("Transaction already processed")
        self.status = "approved"
    
    def reject(self) -> None:
        """Отклонение транзакции (для администратора)."""
        if self.status != "pending":
            raise ValueError("Transaction already processed")
        self.status = "rejected"