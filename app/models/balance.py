from dataclasses import dataclass
from .base import BaseEntity

@dataclass
class Balance(BaseEntity):
    """
    Баланс пользователя в кредитах.
    1 кредит = фиксированная стоимость в рублях.
    """
    user_id: int
    credits: int = 0
    
    CREDIT_PRICE_RUB: float = 30.0

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
        return int(rub_amount / cls.CREDIT_PRICE_RUB)
    