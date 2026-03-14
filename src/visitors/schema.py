from pydantic import BaseModel
from typing import Literal
import datetime


class MergeVisitorRequest(BaseModel):
    """Input for merge_visitor — enforces that device_id is required."""
    device_id: str
    user_id: str | None = None
    visitor_type: str = "new"


class VisitorModel(BaseModel):
    id: int | None = None
    visitor_type: Literal["new", "returning"]
    user_id: str | None = None
    device_id: str | None = None
    signup_date: datetime.datetime | None = None
    account_status: Literal["active", "inactive", "deleted"]
    portfolio_created_at: datetime.datetime | None = None
    user_type: Literal["guest", "user", "admin"]


class VisitorCreate(VisitorModel):
    pass


class VisitorUpdate(VisitorModel):
    pass


class VisitorDelete(VisitorModel):
    id: str
