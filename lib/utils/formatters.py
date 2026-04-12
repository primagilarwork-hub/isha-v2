"""Pure formatting helpers — no side effects, no external calls."""
from datetime import date, datetime


def format_idr(amount: float) -> str:
    """Format number as Indonesian Rupiah string."""
    return f"Rp {amount:,.0f}".replace(",", ".")


def format_date(d: date | str, fmt: str = "%d %b %Y") -> str:
    """Format date to human-readable string."""
    if isinstance(d, str):
        d = datetime.fromisoformat(d).date()
    return d.strftime(fmt)


def format_pct(value: float, total: float) -> int:
    """Calculate percentage, safe division."""
    if total <= 0:
        return 0
    return int(value / total * 100)


def format_cycle_label(start: date, end: date) -> str:
    """Format cycle as '25 Mar - 24 Apr 2026'."""
    return f"{start.strftime('%d %b')} - {end.strftime('%d %b %Y')}"
