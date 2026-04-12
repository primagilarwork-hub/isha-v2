"""Budget data models."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BudgetGroup:
    name: str
    amount: float
    categories: list[str] = field(default_factory=list)
    is_custom: bool = False
    is_overridden: bool = False

    @property
    def category_count(self) -> int:
        return len(self.categories)

    @classmethod
    def from_dict(cls, data: dict) -> "BudgetGroup":
        return cls(
            name=data["name"],
            amount=float(data["amount"]),
            categories=data.get("categories", []),
            is_custom=data.get("is_custom", False),
            is_overridden=data.get("is_overridden", False),
        )
