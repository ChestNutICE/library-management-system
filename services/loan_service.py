"""借阅业务占位模块，后续集中实现借还事务。"""


def borrow_book(user_id: int, book_id: int) -> None:
    raise NotImplementedError("借书业务将在第三阶段实现")


def return_book(loan_id: int) -> None:
    raise NotImplementedError("还书业务将在第三阶段实现")
