from pydantic import BaseModel
import datetime


class EventModel(BaseModel):
    id: int | None = None
    date_id: int
    device_type_id: int
    visitor_id: int
    location_id: int
    referral_id: int
    datetime: datetime.datetime
    page_id: int
    event_type_id: int
    properties: str | None = None