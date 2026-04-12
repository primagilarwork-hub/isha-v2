"""
Handlers package — business logic per domain.
Import semua public functions dari sini untuk backward compatibility.
"""
from lib.handlers.expense import handle_expense, handle_edit, handle_delete, confirm_delete
from lib.handlers.budget import (
    handle_check_budget, handle_view_budgets, handle_edit_budget,
    handle_add_category, handle_remove_category, handle_create_budget_group,
    handle_remove_budget_group, handle_reset_budget, handle_apply_budget,
    check_budget_alert, check_total_budget_vs_income, suggest_budget_reallocation,
)
from lib.handlers.report import handle_report, generate_weekly_summary, generate_system_review
from lib.handlers.reminder import generate_reminder_message, generate_new_cycle_message
from lib.handlers.income import handle_income
from lib.handlers.receipt import handle_receipt
from lib.handlers.setup import handle_setup_budget_help, handle_unknown_category
from lib.handlers.sync import handle_sync_sheets
from lib.handlers.router import handle_message

__all__ = [
    "handle_message",
    "handle_expense", "handle_edit", "handle_delete", "confirm_delete",
    "handle_check_budget", "handle_view_budgets", "handle_edit_budget",
    "handle_add_category", "handle_remove_category", "handle_create_budget_group",
    "handle_remove_budget_group", "handle_reset_budget", "handle_apply_budget",
    "check_budget_alert", "check_total_budget_vs_income", "suggest_budget_reallocation",
    "handle_report", "generate_weekly_summary", "generate_system_review",
    "generate_reminder_message", "generate_new_cycle_message",
    "handle_income", "handle_receipt", "handle_setup_budget_help",
    "handle_unknown_category", "handle_sync_sheets",
]
