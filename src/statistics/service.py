"""
Statistics service — computes all aggregated analytics data from the star schema.

Each function queries the f_events fact table joined to the appropriate
dimension tables and returns data shaped exactly as the frontend expects.
"""

from datetime import datetime, timedelta
from sqlalchemy import func, distinct, case, literal, select
from sqlalchemy.orm import Session

from src.events.model import Events, EventTypes
from src.devices.model import DeviceTypes
from src.visitors.model import Visitors
from src.locations.model import Locations
from src.pages.model import Page
from src.referrals.model import ReferralSources


# ── Country → flag-emoji map (ISO-style names) ─────────────────────────
_COUNTRY_FLAGS: dict[str, str] = {
    "India": "🇮🇳",
    "United States": "🇺🇸",
    "United States of America": "🇺🇸",
    "Egypt": "🇪🇬",
    "Pakistan": "🇵🇰",
    "Nigeria": "🇳🇬",
    "United Kingdom": "🇬🇧",
    "Germany": "🇩🇪",
    "Canada": "🇨🇦",
    "Australia": "🇦🇺",
    "France": "🇫🇷",
    "Brazil": "🇧🇷",
    "Japan": "🇯🇵",
    "South Korea": "🇰🇷",
    "China": "🇨🇳",
    "Russia": "🇷🇺",
    "Mexico": "🇲🇽",
    "Indonesia": "🇮🇩",
    "Turkey": "🇹🇷",
    "Italy": "🇮🇹",
    "Spain": "🇪🇸",
    "Netherlands": "🇳🇱",
    "Saudi Arabia": "🇸🇦",
    "South Africa": "🇿🇦",
    "Argentina": "🇦🇷",
    "Bangladesh": "🇧🇩",
    "Philippines": "🇵🇭",
    "Vietnam": "🇻🇳",
    "Thailand": "🇹🇭",
    "Ukraine": "🇺🇦",
    "Poland": "🇵🇱",
    "Malaysia": "🇲🇾",
    "Singapore": "🇸🇬",
    "Sri Lanka": "🇱🇰",
    "Nepal": "🇳🇵",
    "Kenya": "🇰🇪",
    "Ghana": "🇬🇭",
    "UAE": "🇦🇪",
    "United Arab Emirates": "🇦🇪",
    "Israel": "🇮🇱",
    "Sweden": "🇸🇪",
    "Norway": "🇳🇴",
    "Denmark": "🇩🇰",
    "Finland": "🇫🇮",
    "Ireland": "🇮🇪",
    "New Zealand": "🇳🇿",
    "Portugal": "🇵🇹",
    "Belgium": "🇧🇪",
    "Switzerland": "🇨🇭",
    "Austria": "🇦🇹",
    "Colombia": "🇨🇴",
    "Chile": "🇨🇱",
    "Peru": "🇵🇪",
    "Unknown": "🌐",
}

# Referrer domain → emoji favicon
_REFERRER_FAVICONS: dict[str, str] = {
    "google": "🔍",
    "google.com": "🔍",
    "bing": "🔎",
    "bing.com": "🔎",
    "linkedin": "💼",
    "linkedin.com": "💼",
    "com.linkedin.android": "💼",
    "facebook": "📘",
    "facebook.com": "📘",
    "m.facebook.com": "📘",
    "instagram": "📷",
    "t.instagram.com": "📷",
    "twitter": "🐦",
    "twitter.com": "🐦",
    "x.com": "🐦",
    "reddit": "🤖",
    "reddit.com": "🤖",
    "github": "🐙",
    "github.com": "🐙",
    "youtube": "▶️",
    "youtube.com": "▶️",
    "direct": "🔗",
    "localhost": "🖥️",
}


def _format_number(n: int) -> str:
    """Format a number with comma separators: 3336 → '3,336'."""
    return f"{n:,}"


def _pct_change(current: int | float, previous: int | float) -> tuple[float, str]:
    """Return (change%, changeType) comparing current vs previous period."""
    if previous == 0:
        if current > 0:
            return 100.0, "positive"
        return 0.0, "positive"
    change = ((current - previous) / previous) * 100
    change_type = "positive" if change >= 0 else "negative"
    return round(abs(change), 1), change_type


def _period_bounds(days: int) -> tuple[datetime, datetime, datetime]:
    """Return (current_start, previous_start, now) for the given lookback."""
    now = datetime.utcnow()
    current_start = now - timedelta(days=days)
    previous_start = current_start - timedelta(days=days)
    return current_start, previous_start, now


def _window(
    start: datetime,
    end: datetime,
    page_name: str | None = None,
    inclusive_end: bool = True,
) -> list:
    """
    The WHERE conditions shared by every statistics query.

    `page_name` narrows the result to a single portfolio. d_pages.page_name is
    the first path segment of the URL (the portfolio username), so filtering on
    it scopes to that portfolio and any sub-path under it. Passing None keeps
    the site-wide behaviour the admin dashboard relies on.
    """
    end_condition = Events.datetime <= end if inclusive_end else Events.datetime < end
    conditions = [Events.datetime >= start, end_condition]

    if page_name:
        conditions.append(
            Events.page_id.in_(
                select(Page.id).where(Page.page_name == page_name)
            )
        )

    return conditions


# ═══════════════════════════════════════════════════════════════════════
# Public API — called by the router
# ═══════════════════════════════════════════════════════════════════════

def get_dashboard_statistics(db: Session, days: int = 7) -> dict:
    """
    Compute all dashboard statistics for the given time window.
    Returns a dict shaped exactly like the frontend expects.
    """
    current_start, previous_start, now = _period_bounds(days)

    stats = _compute_stats(db, current_start, previous_start, now)
    chart_data = _compute_chart_data(db, current_start, now)
    top_pages = _compute_top_pages(db, current_start, now)
    referrers = _compute_referrers(db, current_start, now)
    countries = _compute_countries(db, current_start, now)
    devices = _compute_devices(db, current_start, now)
    browsers = _compute_browsers(db, current_start, now)
    operating_systems = _compute_os(db, current_start, now)

    return {
        "stats": stats,
        "chart_data": chart_data,
        "top_pages": top_pages,
        "referrers": referrers,
        "countries": countries,
        "devices": devices,
        "browsers": browsers,
        "operating_systems": operating_systems,
    }


def get_portfolio_statistics(
    db: Session, page_name: str, days: int = 7
) -> dict:
    """
    The same measurements as the dashboard, scoped to a single portfolio.

    This exists because the portfolio owner's own analytics page had no source
    of truth for visitor counts: it was served `visits * 0.6` from a different
    service and labelled "Distinct users". Every number here is measured -
    `unique_visitors` is COUNT(DISTINCT visitor_id) over that portfolio's
    events, and countries come from the location resolved at ingestion.
    """
    current_start, previous_start, now = _period_bounds(days)

    unique_visitors = (
        db.query(func.count(distinct(Events.visitor_id)))
        .filter(*_window(current_start, now, page_name))
        .scalar()
    ) or 0

    previous_visitors = (
        db.query(func.count(distinct(Events.visitor_id)))
        .filter(
            *_window(previous_start, current_start, page_name, inclusive_end=False)
        )
        .scalar()
    ) or 0

    page_view_type_id = (
        db.query(EventTypes.id).filter(EventTypes.name == "PAGE_VIEW").scalar()
    )
    page_views = 0
    if page_view_type_id is not None:
        page_views = (
            db.query(func.count(Events.id))
            .filter(
                *_window(current_start, now, page_name),
                Events.event_type_id == page_view_type_id,
            )
            .scalar()
        ) or 0

    change, change_type = _pct_change(unique_visitors, previous_visitors)

    return {
        "page_name": page_name,
        "days": days,
        "unique_visitors": unique_visitors,
        "page_views": page_views,
        "visitors_change": change,
        "visitors_change_type": change_type,
        "chart_data": _compute_chart_data(db, current_start, now, page_name),
        "referrers": _compute_referrers(db, current_start, now, page_name=page_name),
        "countries": _compute_countries(db, current_start, now, page_name=page_name),
    }


# ═══════════════════════════════════════════════════════════════════════
# Private helpers
# ═══════════════════════════════════════════════════════════════════════

def _compute_stats(
    db: Session,
    current_start: datetime,
    previous_start: datetime,
    now: datetime,
) -> list[dict]:
    """Visitors, Page Views, Bounce Rate — current vs previous period."""

    # ── Unique visitors ──
    cur_visitors = (
        db.query(func.count(distinct(Events.visitor_id)))
        .filter(Events.datetime >= current_start, Events.datetime <= now)
        .scalar()
    ) or 0
    prev_visitors = (
        db.query(func.count(distinct(Events.visitor_id)))
        .filter(Events.datetime >= previous_start, Events.datetime < current_start)
        .scalar()
    ) or 0
    v_change, v_type = _pct_change(cur_visitors, prev_visitors)

    # ── Page views (event_type = PAGE_VIEW) ──
    page_view_type_id = (
        db.query(EventTypes.id).filter(EventTypes.name == "PAGE_VIEW").scalar()
    )

    cur_views = 0
    prev_views = 0
    if page_view_type_id is not None:
        cur_views = (
            db.query(func.count(Events.id))
            .filter(
                Events.datetime >= current_start,
                Events.datetime <= now,
                Events.event_type_id == page_view_type_id,
            )
            .scalar()
        ) or 0
        prev_views = (
            db.query(func.count(Events.id))
            .filter(
                Events.datetime >= previous_start,
                Events.datetime < current_start,
                Events.event_type_id == page_view_type_id,
            )
            .scalar()
        ) or 0
    pv_change, pv_type = _pct_change(cur_views, prev_views)

    # ── Bounce rate ──
    cur_bounce = _bounce_rate(db, current_start, now)
    prev_bounce = _bounce_rate(db, previous_start, current_start)
    # For bounce rate, a decrease is positive (good)
    br_raw_change = cur_bounce - prev_bounce
    br_change = round(abs(br_raw_change), 1)
    # Lower bounce rate is better, so a decrease is "positive"
    br_type = "positive" if br_raw_change <= 0 else "negative"

    return [
        {
            "label": "Visitors",
            "value": _format_number(cur_visitors),
            "change": v_change,
            "changeType": v_type,
        },
        {
            "label": "Page Views",
            "value": _format_number(cur_views),
            "change": pv_change,
            "changeType": pv_type,
        },
        {
            "label": "Bounce Rate",
            "value": f"{round(cur_bounce)}%",
            "change": br_change,
            "changeType": br_type,
        },
    ]


def _bounce_rate(db: Session, start: datetime, end: datetime) -> float:
    """
    Bounce rate = sessions with only 1 page-view / total sessions × 100.
    A "session" is identified by session_id.
    """
    page_view_type_id = (
        db.query(EventTypes.id).filter(EventTypes.name == "PAGE_VIEW").scalar()
    )
    if page_view_type_id is None:
        return 0.0

    # Count page views per session in the period
    session_pv = (
        db.query(
            Events.session_id,
            func.count(Events.id).label("pv_count"),
        )
        .filter(
            Events.datetime >= start,
            Events.datetime < end,
            Events.event_type_id == page_view_type_id,
        )
        .group_by(Events.session_id)
        .subquery()
    )

    total_sessions = db.query(func.count()).select_from(session_pv).scalar() or 0
    if total_sessions == 0:
        return 0.0

    bounced = (
        db.query(func.count())
        .select_from(session_pv)
        .filter(session_pv.c.pv_count == 1)
        .scalar()
    ) or 0

    return (bounced / total_sessions) * 100


def _compute_chart_data(
    db: Session, start: datetime, end: datetime, page_name: str | None = None
) -> list[dict]:
    """Daily visitors and page views for the chart."""
    page_view_type_id = (
        db.query(EventTypes.id).filter(EventTypes.name == "PAGE_VIEW").scalar()
    )

    # Generate all dates in the range
    results = []
    current = start.date()
    end_date = end.date()

    while current <= end_date:
        day_start = datetime.combine(current, datetime.min.time())
        day_end = datetime.combine(current, datetime.max.time())

        visitors = (
            db.query(func.count(distinct(Events.visitor_id)))
            .filter(*_window(day_start, day_end, page_name))
            .scalar()
        ) or 0

        page_views = 0
        if page_view_type_id is not None:
            page_views = (
                db.query(func.count(Events.id))
                .filter(
                    *_window(day_start, day_end, page_name),
                    Events.event_type_id == page_view_type_id,
                )
                .scalar()
            ) or 0

        results.append({
            "date": current.strftime("%b %-d"),
            "visitors": visitors,
            "pageViews": page_views,
        })
        current += timedelta(days=1)

    return results


def _compute_top_pages(
    db: Session, start: datetime, end: datetime, limit: int = 10
) -> list[dict]:
    """Top pages by unique visitors."""
    rows = (
        db.query(
            Page.full_path,
            func.count(distinct(Events.visitor_id)).label("visitors"),
        )
        .join(Events, Events.page_id == Page.id)
        .filter(Events.datetime >= start, Events.datetime <= end)
        .group_by(Page.full_path)
        .order_by(func.count(distinct(Events.visitor_id)).desc())
        .limit(limit)
        .all()
    )
    return [{"path": row.full_path, "visitors": row.visitors} for row in rows]


def _compute_referrers(
    db: Session,
    start: datetime,
    end: datetime,
    limit: int = 10,
    page_name: str | None = None,
) -> list[dict]:
    """Top referral sources by unique visitors."""
    rows = (
        db.query(
            ReferralSources.source,
            func.count(distinct(Events.visitor_id)).label("visitors"),
        )
        .join(Events, Events.referral_id == ReferralSources.id)
        .filter(*_window(start, end, page_name))
        .group_by(ReferralSources.source)
        .order_by(func.count(distinct(Events.visitor_id)).desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "domain": row.source,
            "favicon": _REFERRER_FAVICONS.get(row.source, "🌐"),
            "visitors": row.visitors,
        }
        for row in rows
    ]


def _compute_countries(
    db: Session,
    start: datetime,
    end: datetime,
    limit: int = 10,
    page_name: str | None = None,
) -> list[dict]:
    """Country breakdown as percentages of unique visitors."""
    total_visitors = (
        db.query(func.count(distinct(Events.visitor_id)))
        .filter(*_window(start, end, page_name))
        .scalar()
    ) or 1  # avoid division by zero

    rows = (
        db.query(
            Locations.country,
            func.count(distinct(Events.visitor_id)).label("visitors"),
        )
        .join(Events, Events.location_id == Locations.id)
        .filter(*_window(start, end, page_name))
        .group_by(Locations.country)
        .order_by(func.count(distinct(Events.visitor_id)).desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "country": row.country,
            "flag": _COUNTRY_FLAGS.get(row.country, "🌐"),
            "percentage": f"{round((row.visitors / total_visitors) * 100)}%",
        }
        for row in rows
    ]


def _compute_devices(
    db: Session, start: datetime, end: datetime
) -> list[dict]:
    """Device type breakdown (desktop/mobile/tablet) as percentages."""
    total = (
        db.query(func.count(distinct(Events.visitor_id)))
        .filter(Events.datetime >= start, Events.datetime <= end)
        .scalar()
    ) or 1

    rows = (
        db.query(
            DeviceTypes.device_type,
            func.count(distinct(Events.visitor_id)).label("visitors"),
        )
        .join(Events, Events.device_type_id == DeviceTypes.id)
        .filter(Events.datetime >= start, Events.datetime <= end)
        .group_by(DeviceTypes.device_type)
        .order_by(func.count(distinct(Events.visitor_id)).desc())
        .all()
    )
    return [
        {
            "device": row.device_type.capitalize(),
            "percentage": _format_pct(row.visitors, total),
        }
        for row in rows
    ]


def _compute_browsers(
    db: Session, start: datetime, end: datetime
) -> list[dict]:
    """Browser breakdown as percentages."""
    total = (
        db.query(func.count(distinct(Events.visitor_id)))
        .filter(Events.datetime >= start, Events.datetime <= end)
        .scalar()
    ) or 1

    rows = (
        db.query(
            DeviceTypes.browser,
            func.count(distinct(Events.visitor_id)).label("visitors"),
        )
        .join(Events, Events.device_type_id == DeviceTypes.id)
        .filter(Events.datetime >= start, Events.datetime <= end)
        .group_by(DeviceTypes.browser)
        .order_by(func.count(distinct(Events.visitor_id)).desc())
        .limit(10)
        .all()
    )
    return [
        {
            "browser": row.browser,
            "percentage": _format_pct(row.visitors, total),
        }
        for row in rows
    ]


def _compute_os(
    db: Session, start: datetime, end: datetime
) -> list[dict]:
    """Operating system breakdown as percentages."""
    total = (
        db.query(func.count(distinct(Events.visitor_id)))
        .filter(Events.datetime >= start, Events.datetime <= end)
        .scalar()
    ) or 1

    rows = (
        db.query(
            DeviceTypes.os,
            func.count(distinct(Events.visitor_id)).label("visitors"),
        )
        .join(Events, Events.device_type_id == DeviceTypes.id)
        .filter(Events.datetime >= start, Events.datetime <= end)
        .group_by(DeviceTypes.os)
        .order_by(func.count(distinct(Events.visitor_id)).desc())
        .limit(10)
        .all()
    )
    return [
        {
            "os": row.os,
            "percentage": _format_pct(row.visitors, total),
        }
        for row in rows
    ]


def _format_pct(count: int, total: int) -> str:
    """Format a count/total as a percentage string."""
    pct = (count / total) * 100
    if pct < 0.5 and pct > 0:
        return "<0.5%"
    return f"{round(pct)}%"


# ═══════════════════════════════════════════════════════════════════════
# Live Events
# ═══════════════════════════════════════════════════════════════════════

_TIME_RANGE_DAYS: dict[str, int] = {
    "today": 0,       # special: start of today
    "yesterday": 1,   # special: yesterday only
    "7d": 7,
    "30d": 30,
    "3m": 90,
    "6m": 180,
    "12m": 365,
}


def _time_range_to_bounds(time_range: str) -> tuple[datetime, datetime]:
    """Convert a frontend time-range key to (start, end) datetimes."""
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    if time_range == "today":
        return today_start, now
    elif time_range == "yesterday":
        yesterday_start = today_start - timedelta(days=1)
        return yesterday_start, today_start
    else:
        days = _TIME_RANGE_DAYS.get(time_range, 7)
        return now - timedelta(days=days), now


def _relative_time(event_dt: datetime) -> str:
    """Format a datetime as a human-readable relative time string."""
    now = datetime.utcnow()
    delta = now - event_dt

    seconds = int(delta.total_seconds())
    if seconds < 60:
        return f"{seconds} seconds ago"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    days = hours // 24
    return f"{days} day{'s' if days != 1 else ''} ago"


def get_live_events(
    db: Session,
    time_range: str = "today",
    search: str = "",
    limit: int = 100,
) -> dict:
    """
    Fetch recent events with all dimension data, shaped as the frontend
    LiveEvent interface expects.
    """
    from sqlalchemy.orm import joinedload

    start, end = _time_range_to_bounds(time_range)

    query = (
        db.query(Events)
        .options(
            joinedload(Events.device_type),
            joinedload(Events.visitor),
            joinedload(Events.location),
            joinedload(Events.page),
            joinedload(Events.referral),
            joinedload(Events.event_type),
        )
        .filter(Events.datetime >= start, Events.datetime <= end)
        .order_by(Events.datetime.desc())
    )

    # Get total count before limiting
    total_count = (
        db.query(func.count(Events.id))
        .filter(Events.datetime >= start, Events.datetime <= end)
        .scalar()
    ) or 0

    events = query.limit(limit).all()

    # Transform into frontend shape
    live_events = []
    for event in events:
        # Build the event name from event_type
        event_name = f"[Auto] {_format_event_type(event.event_type.name)}" if event.event_type else "Unknown"

        # Build distinct ID: prefer user_id, fall back to device_id
        distinct_id = "(anonymous)"
        if event.visitor:
            if event.visitor.user_id:
                distinct_id = event.visitor.user_id
            elif event.visitor.device_id:
                distinct_id = f"$device:{event.visitor.device_id[:20]}..."

        # Current URL from page
        current_url = ""
        if event.page:
            current_url = event.page.url
            if len(current_url) > 40:
                current_url = current_url[:37] + "..."

        # Initial referrer
        initial_referrer = "$direct"
        if event.referral and event.referral.source != "direct":
            initial_referrer = event.referral.referrer_url or event.referral.source

        # OS
        operating_system = event.device_type.os if event.device_type else "Unknown"

        # URL search — not stored, so "(not set)"
        url_search = "(not set)"

        # Format time
        time_str = event.datetime.strftime("%-I:%M:%S %p")

        # Build properties list
        properties = _build_event_properties(event)

        # Apply search filter on event name, distinctId, or currentUrl
        if search:
            search_lower = search.lower()
            searchable = f"{event_name} {distinct_id} {current_url} {operating_system}".lower()
            if search_lower not in searchable:
                continue

        live_events.append({
            "id": event.id,
            "eventName": event_name,
            "time": time_str,
            "timeRelative": _relative_time(event.datetime),
            "distinctId": distinct_id,
            "urlSearch": url_search,
            "operatingSystem": operating_system,
            "currentUrl": current_url,
            "initialReferrer": initial_referrer,
            "properties": properties,
        })

    return {
        "events": live_events,
        "totalMatches": total_count,
        "shownCount": len(live_events),
    }


def _format_event_type(name: str) -> str:
    """Convert 'PAGE_VIEW' → 'Page View', 'ELEMENT_CLICK' → 'Element Click'."""
    return name.replace("_", " ").title()


def _build_event_properties(event: Events) -> list[dict[str, str]]:
    """Build a list of key-value property dicts from all dimension data."""
    import json as _json

    props: list[dict[str, str]] = []

    # Browser / Device info
    if event.device_type:
        props.append({"key": "Browser", "value": event.device_type.browser})
        props.append({"key": "Operating System", "value": event.device_type.os})
        props.append({"key": "Device Type", "value": event.device_type.device_type.capitalize()})

    # Location info
    if event.location:
        props.append({"key": "City", "value": event.location.city})
        props.append({"key": "State", "value": event.location.state})
        props.append({"key": "Country", "value": event.location.country})

    # Page info
    if event.page:
        props.append({"key": "Current URL", "value": event.page.url})
        props.append({"key": "URL Path", "value": event.page.full_path})
        props.append({"key": "Page Name", "value": event.page.page_name})
        props.append({"key": "Current Domain", "value": event.page.host})

    # Referral info
    if event.referral:
        props.append({"key": "Referrer Source", "value": event.referral.source})
        if event.referral.referrer_url:
            props.append({"key": "Referrer URL", "value": event.referral.referrer_url})
        props.append({"key": "Referrer Category", "value": event.referral.category})

    # Visitor info
    if event.visitor:
        if event.visitor.user_id:
            props.append({"key": "User ID", "value": event.visitor.user_id})
        if event.visitor.device_id:
            props.append({"key": "Device ID", "value": event.visitor.device_id})
        props.append({"key": "Visitor Type", "value": event.visitor.visitor_type})
        props.append({"key": "User Type", "value": event.visitor.user_type})
        props.append({"key": "Account Status", "value": event.visitor.account_status})

    # Event metadata
    props.append({"key": "Event Type", "value": event.event_type.name if event.event_type else "Unknown"})
    props.append({"key": "Session ID", "value": event.session_id})
    props.append({"key": "Time", "value": event.datetime.strftime("%-I:%M:%S.%f %p, %a, %b %-d, %Y")[:-3]})

    # Custom properties (stored as JSON string)
    if event.properties:
        try:
            custom = _json.loads(event.properties)
            if isinstance(custom, dict):
                for k, v in custom.items():
                    props.append({"key": k, "value": str(v)})
        except (ValueError, TypeError):
            props.append({"key": "Properties", "value": event.properties})

    return props

