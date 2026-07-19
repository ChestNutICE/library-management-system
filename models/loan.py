from dataclasses import dataclass


@dataclass(slots=True)
class Loan:
    id: int | None
    user_id: int
    book_id: int
    borrow_date: str
    due_date: str
    return_date: str | None = None
    status: str = "borrowed"
    fine: float = 0.0
