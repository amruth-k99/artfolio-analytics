from pydantic import BaseModel, Field
import datetime


# --- Nested models for the client ingestion payload ---

class VisitorPayload(BaseModel):
    """Visitor identity from the client."""
    user_id: str | None = Field(
        None, description="Logged-in user's email or ID. Null for guests.")
    device_id: str = Field(
        ..., description="Persistent device UUID (generated and stored on client)")
    visitor_type: str = Field("new", description="'new' or 'returning'")


class DevicePayload(BaseModel):
    """Device/browser info collected from the client (navigator/user-agent)."""
    os: str = Field(...,
                    description="Operating system, e.g. 'Windows', 'macOS', 'Android'")
    browser: str = Field(...,
                         description="Browser name, e.g. 'Chrome', 'Microsoft Edge'")
    device_type: str = Field(
        "desktop", description="'desktop', 'mobile', or 'tablet'")


class PagePayload(BaseModel):
    """Page the event occurred on."""
    page_name: str = Field(
        ..., description="Portfolio owner's name or page identifier, e.g. 'username'")
    url: str = Field(...,
                     description="Full URL, e.g. 'https://www.artfolio.tech/username'")
    full_path: str = Field(..., description="URL path only, e.g. '/username'")


class ReferralPayload(BaseModel):
    """Where the visitor came from."""
    source: str = Field(
        "direct", description="Referral source name, e.g. 'google', 'bing', 'direct'")
    referrer_url: str | None = Field(
        None, description="Full referrer URL from document.referrer")
    category: str = Field(
        "direct", description="'search', 'social', 'email', 'direct', or 'other'")


# --- Main client payload ---

class EventIngestionPayload(BaseModel):
    """
    The JSON payload the client (browser) sends to the ingestion API.

    Location is NOT included — the server resolves it from ip_address
    using the existing get_location_by_ip service.

    The ingestion service will:
    1. Resolve location from ip_address
    2. Upsert each dimension (visitor, location, device, page, referral, date)
    3. Create the fact event with the resolved FK IDs
    """
    event_type: str = Field(...,
                            description="Type of event: 'page_view', 'click', etc.")
    session_id: str = Field(
        ..., description="Client-generated session UUID, persisted per browser session")
    timestamp: datetime.datetime = Field(
        ..., description="Client-side timestamp when the event occurred")
    ip_address: str = Field(
        ..., description="Client IP address — server resolves to location via iplocation.com")
    # we do NOT store IP addresses in the database. We use it to resolve location and delete it.

    visitor: VisitorPayload
    device: DevicePayload
    page: PagePayload
    referral: ReferralPayload = Field(default_factory=ReferralPayload)


# --- Response models for dimension tables ---

class DateResponse(BaseModel):
    id: int
    date: datetime.datetime
    minute: int
    hour: int
    day: int
    day_of_week: int
    month: int
    quarter: int
    year: int

    class Config:
        from_attributes = True


class DeviceTypeResponse(BaseModel):
    id: int
    os: str
    device_type: str
    browser: str

    class Config:
        from_attributes = True


class VisitorResponse(BaseModel):
    id: int
    visitor_type: str
    user_id: str | None = None
    device_id: str | None = None
    signup_date: datetime.datetime | None = None
    account_status: str
    portfolio_created_at: datetime.datetime | None = None
    user_type: str

    class Config:
        from_attributes = True


class LocationResponse(BaseModel):
    id: int
    city: str
    state: str
    country: str

    class Config:
        from_attributes = True


class PageResponse(BaseModel):
    id: int
    page_name: str
    url: str
    full_path: str
    host: str

    class Config:
        from_attributes = True


class ReferralResponse(BaseModel):
    id: int
    source: str
    referrer_url: str | None = None
    category: str

    class Config:
        from_attributes = True


class EventTypeResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


# --- Existing fact table read/write model ---
class EventModel(BaseModel):
    """Pydantic model for the f_events fact table (after dimension resolution)."""
    id: int | None = None
    date_id: int
    device_type_id: int
    visitor_id: int
    location_id: int
    referral_id: int
    datetime: datetime.datetime
    session_id: str
    page_id: int
    event_type_id: int
    properties: str | None = None

    # Resolved dimension data
    device_type: DeviceTypeResponse | None = None
    visitor: VisitorResponse | None = None
    location: LocationResponse | None = None
    page: PageResponse | None = None
    referral: ReferralResponse | None = None
    event_type: EventTypeResponse | None = None

    class Config:
        from_attributes = True


class BatchIngestionPayload(BaseModel):
    """Payload for batch event ingestion from the frontend analytics pipeline."""
    events: list[EventIngestionPayload]

