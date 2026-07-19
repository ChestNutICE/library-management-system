"""输入校验工具。"""


def require_text(value: str, field_name: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name}不能为空")
    return cleaned


def require_non_negative_int(value: int, field_name: str) -> int:
    if value < 0:
        raise ValueError(f"{field_name}不能为负数")
    return value


def require_isbn(value: str) -> str:
    cleaned = value.replace("-", "").replace(" ", "")
    if not cleaned.isdigit() or len(cleaned) not in (10, 13):
        raise ValueError("ISBN 必须是 10 位或 13 位数字")
    return cleaned


def validate_phone(value: str) -> str:
    cleaned = value.strip().replace(" ", "").replace("-", "")
    if cleaned and (not cleaned.isdigit() or len(cleaned) not in range(7, 12)):
        raise ValueError("电话号码必须是 7 至 11 位数字")
    return cleaned
