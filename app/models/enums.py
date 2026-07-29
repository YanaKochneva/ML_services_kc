from enum import Enum

class UserRole(Enum):
    """Роли пользователей в системе."""
    USER = "user"
    ADMIN = "admin"

class TransactionType(Enum):
    """Типы транзакций."""
    DEPOSIT = "deposit"
    WITHDRAW = "withdraw"

class TaskStatus(Enum):
    """Статусы ML задач."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    VALIDATION_ERROR = "validation_error"