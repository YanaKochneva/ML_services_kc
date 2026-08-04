from sqlmodel import SQLModel, Field, Relationship
from typing import List
from .transaction import Transaction
from .balance import Balance
from .enums import TransactionType
from .user import User

class AdminService:
    """
    Сервис для администратора.
    """
    
    def __init__(self):
        self._pending_transactions: List[Transaction] = []
    
    def add_pending_transaction(self, transaction: Transaction) -> None:
        """Добавление транзакции на модерацию."""
        self._pending_transactions.append(transaction)
    
    def get_pending_transactions(self) -> List[Transaction]:
        """Получение всех транзакций, ожидающих модерации."""
        return [t for t in self._pending_transactions if t.status == "pending"]
    
    def approve_transaction(self, transaction: Transaction, user: User) -> None:
        """Подтверждение транзакции пополнения."""
        if transaction.transaction_type != TransactionType.DEPOSIT:
            raise ValueError("Only deposit transactions can be approved")
        transaction.approve()
        user.balance.deposit(Balance.rub_to_credits(transaction.amount))

    def reject_transaction(self, transaction: Transaction) -> None:
        """Отклонение транзакции."""
        transaction.reject()
    
    def get_all_transactions(self) -> List[Transaction]:
        """Получение всех транзакций."""
        return self._pending_transactions