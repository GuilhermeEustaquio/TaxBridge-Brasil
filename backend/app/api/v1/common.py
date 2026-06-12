from typing import Annotated

from fastapi import Depends, Query
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session


class PageParams:
    def __init__(
        self,
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=20, ge=1, le=200),
    ):
        self.page = page
        self.page_size = page_size


PageDep = Annotated[PageParams, Depends(PageParams)]


def paginate(db: Session, query: Select, params: PageParams) -> dict:
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = db.scalars(query.offset((params.page - 1) * params.page_size).limit(params.page_size)).all()
    return {"items": items, "total": total, "page": params.page, "page_size": params.page_size}
