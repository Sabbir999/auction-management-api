from typing import Any

from ninja import Field, Schema
from ninja.pagination import PaginationBase


class CustomPagination(PaginationBase):
    class Input(Schema):
        page: int = Field(default=1, ge=1)
        page_size: int = Field(default=20, ge=1, le=100)

    class Output(Schema):
        items: list[Any]
        total: int
        page: int
        page_size: int
        total_pages: int

    def paginate_queryset(self, queryset, pagination: Input, **params):
        page = pagination.page
        page_size = pagination.page_size

        total = queryset.count()

        start = (page - 1) * page_size
        end = start + page_size

        total_pages = (
            (total + page_size - 1) // page_size
            if total
            else 0
        )

        return {
            "items": queryset[start:end],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }