from dataclasses import dataclass
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING, ClassVar
from decimal import Decimal

if TYPE_CHECKING:
    from .user import User

@dataclass
class Balance(SQLModel, table=True):
    """
    Баланс пользователя в кредитах.
    1 кредит = фиксированная стоимость в рублях.
    
    Attributes:
        id (int): Primary key
        user_id (int): Foreign key to User
        credits (Decimal): Текущий баланс в кредитах
        user (User): Связанный пользователь
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True)
    credits: Decimal = Field(default=0, max_digits=15, decimal_places=2)
    
    user: "User" = Relationship(back_populates="balance")
    CREDIT_PRICE_RUB: ClassVar[Decimal] = Decimal('30.0')
    
    def validate(self) -> None:
        if self.user_id <= 0:
            raise ValueError("Invalid user ID")
        if self.credits < 0:
            raise ValueError("Credits cannot be negative")

    def deposit(self, credits: int) -> None:
        if credits <= 0:
            raise ValueError("Deposit amount must be positive")
        self.credits += credits

    def withdraw(self, credits: int) -> None:
        if credits <= 0:
            raise ValueError("Withdraw amount must be positive")
        if self.credits < credits:
            raise ValueError("Insufficient credits")
        self.credits -= credits

    def has_enough(self, credits: int) -> bool:
        return self.credits >= credits

    def to_rubles(self) -> float:
        """Перевод кредитов в рубли."""
        return self.credits * self.CREDIT_PRICE_RUB

    @classmethod
    def rub_to_credits(cls, rub_amount: float) -> int:
        """Перевод рублей в кредиты."""
        if rub_amount <= 0:
            raise ValueError("Amount must be positive")
        return int(Decimal(str(rub_amount)) / cls.CREDIT_PRICE_RUB)

    @classmethod
    def credits_to_rub(cls, credits: Decimal) -> Decimal:
        if credits < 0:
            raise ValueError("Credits cannot be negative")
        return credits * cls.CREDIT_PRICE_RUB
    