from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import re
from abc import ABC, abstractmethod

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


@dataclass
class BaseEntity(ABC):
    """
    Абстрактный базовый класс для всех сущностей системы.
    Обеспечивает единый интерфейс для валидации и представления.
    """
    id: int
    
    @abstractmethod
    def validate(self) -> None:
        """Абстрактный метод валидации. Должен быть реализован в наследниках."""
        pass
    
    def __post_init__(self) -> None:
        """Автоматическая валидация после инициализации."""
        self.validate()


@dataclass
class User(BaseEntity):
    """
    Класс пользователя системы.
    """
    username: str
    email: str
    password_hash: str
    balance: float = 0.0
    role: UserRole = UserRole.USER
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    transactions: List['Transaction'] = field(default_factory=list)
    ml_tasks: List['MLTask'] = field(default_factory=list)
    
    def validate(self) -> None:
        """Валидация данных пользователя."""
        self._validate_username()
        self._validate_email()
        self._validate_balance()
    
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
    
    def _validate_balance(self) -> None:
        """Проверка баланса."""
        if self.balance < 0:
            raise ValueError("Balance cannot be negative")
    
    def add_transaction(self, transaction: 'Transaction') -> None:
        """Добавление транзакции."""
        self.transactions.append(transaction)
        if transaction.transaction_type == TransactionType.DEPOSIT:
            self.balance += transaction.amount
        elif transaction.transaction_type == TransactionType.WITHDRAW:
            if self.balance < transaction.amount:
                raise ValueError("Insufficient balance")
            self.balance -= transaction.amount
    
    def add_ml_task(self, task: 'MLTask') -> None:
        """Добавление ML задачи."""
        self.ml_tasks.append(task)
    
    def can_perform_task(self, cost: float) -> bool:
        """Проверка, достаточно ли средств для выполнения задачи."""
        return self.balance >= cost


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


@dataclass
class LLMConfig(BaseEntity):
    """
    Конфигурация LLM модели.
    
    Attributes:
        name: Название модели
        version: Версия модели
        cost_per_request: Стоимость одного запроса в кредитах
        description: Описание модели
        max_prompt_length: Максимальная длина запроса
        is_active: Доступна ли модель для использования
    """
    name: str = "Qwen3-8B"
    version: str = "1.0"
    cost_per_request: float = 10.0
    description: str = "Language model for text generation"
    max_prompt_length: int = 4000
    is_active: bool = True
    
    def validate(self) -> None:
        """Валидация конфигурации."""
        if not self.name:
            raise ValueError("Model name is required")
        if self.cost_per_request < 0:
            raise ValueError("Cost cannot be negative")
        if not self.version:
            raise ValueError("Version is required")
        if self.max_prompt_length <= 0:
            raise ValueError("Max prompt length must be positive")


@dataclass
class MLTask(BaseEntity):
    """
    Класс задачи для LLM сервиса.
    
    Attributes:
        id: Уникальный идентификатор
        user_id: ID пользователя
        input_data: Запрос к LLM
        output_data: Результат генерации
        status: Статус задачи
        cost: Стоимость выполнения
        created_at: Дата создания
        completed_at: Дата завершения
        error_message: Сообщение об ошибке
        validation_errors: Ошибки валидации данных
    """
    user_id: int
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    status: TaskStatus = TaskStatus.PENDING
    cost: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    validation_errors: List[str] = field(default_factory=list)
    
    def validate(self) -> None:
        """Валидация ML задачи."""
        if self.user_id <= 0:
            raise ValueError("Invalid user ID")
        if not self.input_data:
            raise ValueError("Input data is required")
        if 'prompt' not in self.input_data:
            raise ValueError("Prompt is required")
    
    def complete(self, result: Dict[str, Any]) -> None:
        """Завершение задачи с результатом."""
        self.status = TaskStatus.COMPLETED
        self.output_data = result
        self.completed_at = datetime.now()
    
    def fail(self, error: str) -> None:
        """Отметка о провале задачи."""
        self.status = TaskStatus.FAILED
        self.error_message = error
        self.completed_at = datetime.now()
    
    def add_validation_error(self, error: str) -> None:
        """Добавление ошибки валидации."""
        self.validation_errors.append(error)
        self.status = TaskStatus.VALIDATION_ERROR


class LLMServiceInterface(ABC):
    """
    Абстрактный интерфейс для LLM сервисов.
    """
    
    @abstractmethod
    def validate_data(self, data: Dict[str, Any], config: LLMConfig) -> List[str]:
        """
        Валидация входных данных с учетом конфигурации.
        """
        pass
    
    @abstractmethod
    def generate(self, data: Dict[str, Any], config: LLMConfig) -> Dict[str, Any]:
        """
        Генерация ответа LLM.
        """
        pass
    
    @abstractmethod
    def get_model_info(self, config: LLMConfig) -> Dict[str, Any]:
        """
        Получение информации о модели.
        """
        pass



class DefaultLLMService(LLMServiceInterface):
    """
    Реализация LLM сервиса.
    """
    
    def validate_data(self, data: Dict[str, Any], config: LLMConfig) -> List[str]:
        """Валидация данных для LLM."""
        errors = []
        
        if 'prompt' not in data:
            errors.append("Missing 'prompt' field")
        elif not isinstance(data['prompt'], str):
            errors.append("'prompt' must be a string")
        elif len(data['prompt'].strip()) == 0:
            errors.append("'prompt' cannot be empty")
        
        if 'prompt' in data and isinstance(data['prompt'], str):
            if len(data['prompt']) > config.max_prompt_length:
                errors.append(f"'prompt' exceeds maximum length of {config.max_prompt_length} characters")
        
        return errors
    
    def generate(self, data: Dict[str, Any], config: LLMConfig) -> Dict[str, Any]:
        """Генерация ответа LLM."""
        prompt = data.get('prompt', '')
        
        response = f"[{config.name}] Ответ на ваш запрос: '{prompt[:50]}...'"
        
        return {
            'response': response,
            'model_name': config.name,
            'model_version': config.version,
            'tokens_used': len(prompt.split()) + len(response.split()),
            'finish_reason': 'stop'
        }
    
    def get_model_info(self, config: LLMConfig) -> Dict[str, Any]:
        """Получение информации о модели."""
        return {
            'name': config.name,
            'version': config.version,
            'description': config.description,
            'max_prompt_length': config.max_prompt_length,
            'cost_per_request': config.cost_per_request,
            'capabilities': ['text_generation', 'chat_completion']
        }


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
        user.balance += transaction.amount
    
    def reject_transaction(self, transaction: Transaction) -> None:
        """Отклонение транзакции."""
        transaction.reject()
    
    def get_all_transactions(self) -> List[Transaction]:
        """Получение всех транзакций."""
        return self._pending_transactions


def main() -> None:
    try:
        user = User(
            id=1,
            username="yana_kochneva",
            email="test@mail.ru",
            password_hash="secure_password123"
        )
        
        transaction = Transaction(
            id=1,
            user_id=user.id,
            amount=10.0,
            transaction_type=TransactionType.DEPOSIT,
            description="Initial deposit"
        )
        user.add_transaction(transaction)
       
        config = LLMConfig(
            name="Qwen3-8B",
            version="1.0.0",
            cost_per_request=10.0,
            description="Language model for text generation"
        )
        
        task = MLTask(
            id=1,
            user_id=user.id,
            config=config,
            input_data={'prompt': 'Write a short poem'},
            cost=config.cost_per_request
        )
        user.add_ml_task(task)
        
        print(f"Created user: {user.username}")
        print(f"User balance: {user.balance} credits")
        print(f"Number of transactions: {len(user.transactions)}")
        print(f"Number of ML tasks: {len(user.ml_tasks)}")
        print(f"ML task status: {task.status.value}")
        
    except ValueError as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    main()