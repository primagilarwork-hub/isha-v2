"""Input validation helpers."""
from lib.constants import MAX_EXPENSE_AMOUNT, MIN_EXPENSE_AMOUNT


def validate_amount(amount: float) -> tuple[bool, str]:
    """
    Validate expense amount.
    Returns (is_valid, error_message).
    """
    if amount <= MIN_EXPENSE_AMOUNT:
        return False, "Jumlah harus lebih dari 0."
    if amount > MAX_EXPENSE_AMOUNT:
        return False, f"Jumlah Rp {amount:,.0f} terlalu besar. Maksimal Rp {MAX_EXPENSE_AMOUNT:,.0f}."
    return True, ""


def validate_category(category: str, valid_categories: list[str]) -> tuple[bool, str]:
    """Validate category exists in valid list."""
    if not category:
        return False, "Kategori tidak boleh kosong."
    if category not in valid_categories:
        return False, f"Kategori '{category}' tidak ditemukan."
    return True, ""
