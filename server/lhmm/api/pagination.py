from typing import Tuple


def parse_pagination(page: int = 1, per_page: int = 50, max_per_page: int = 100) -> Tuple[int, int]:
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 1
    if per_page > max_per_page:
        per_page = max_per_page
    offset = (page - 1) * per_page
    return offset, per_page
