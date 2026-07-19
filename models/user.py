from dataclasses import dataclass


@dataclass(slots=True)
class User:
    id: int | None
    username: str
    real_name: str
    role: str
    phone: str | None = None
    status: int = 1
