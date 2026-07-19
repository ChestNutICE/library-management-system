from datetime import date

from utils.date_utils import default_due_date


def test_default_due_date_is_30_days_later() -> None:
    assert default_due_date(date(2026, 7, 19)) == date(2026, 8, 18)
