"""临近到期与逾期提醒查询。"""

from datetime import date, timedelta

from services.loan_service import list_loans


def due_reminders(days: int = 3, user_id: int | None = None,
                  current_date: date | None = None) -> list[dict]:
    current = current_date or date.today(); deadline = current + timedelta(days=days)
    rows = list_loans(user_id=user_id, current_date=current)
    reminders = []
    for row in rows:
        if row["status"] not in ("borrowed", "overdue"): continue
        due = date.fromisoformat(row["due_date"])
        if due <= deadline:
            item = dict(row); item["days_remaining"] = (due - current).days
            reminders.append(item)
    return sorted(reminders, key=lambda item: item["due_date"])
