"""Expense data model."""
from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class Expense:
    amount: float
    category: str
    budget_group: str
    description: str
    expense_date: str
    cycle_id: str
    user_name: str = ""
    id: Optional[int] = None
    created_at: Optional[str] = None
    receipt_photo_url: Optional[str] = None

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}

    @classmethod
    def from_dict(cls, data: dict) -> "Expense":
        return cls(
            amount=float(data.get("amount", 0)),
            category=data.get("category", "misc"),
            budget_group=data.get("budget_group", "Lain-lain"),
            description=data.get("description", ""),
            expense_date=data.get("expense_date", date.today().strftime("%Y-%m-%d")),
            cycle_id=data.get("cycle_id", ""),
            user_name=data.get("user_name", ""),
            id=data.get("id"),
            created_at=data.get("created_at"),
        )
