from dataclasses import dataclass


@dataclass(slots=True)
class Book:
    id: int | None
    isbn: str
    title: str
    author: str
    total_count: int = 1
    available_count: int = 1
    category_id: int | None = None
    status: int = 1
