from dataclasses import dataclass, field
from .base import BaseEntity
from .enums import TransactionType
from datetime import datetime

@dataclass
class Transaction(BaseEntity):
    """
    Класс транзакции (пополнение или списание).
    """
    user_id: int
    amount: float
    transaction_type: TransactionType
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "pending"  
    
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