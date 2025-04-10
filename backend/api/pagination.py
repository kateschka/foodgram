"""Настройки пагинации для API."""

from rest_framework.pagination import PageNumberPagination
from backend.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


class PaginatorWithLimit(PageNumberPagination):
    """Пагинатор с лимитом на количество элементов."""

    page_size = DEFAULT_PAGE_SIZE
    page_size_query_param = "limit"
    max_page_size = MAX_PAGE_SIZE
