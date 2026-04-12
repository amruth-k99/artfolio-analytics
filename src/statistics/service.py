"""
Statistics service — computes all aggregated analytics data from the star schema.

Each function queries the f_events fact table joined to the appropriate
dimension tables and returns data shaped exactly as the frontend expects.
"""

from datetime import datetime, timedelta
from sqlalchemy import func, distinct, case, literal
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
    db: Session, start: datetime, end: datetime
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
            .filter(Events.datetime >= day_start, Events.datetime <= day_end)
            .scalar()
        ) or 0

        page_views = 0
        if page_view_type_id is not None:
            page_views = (
                db.query(func.count(Events.id))
                .filter(
                    Events.datetime >= day_start,
                    Events.datetime <= day_end,
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
    db: Session, start: datetime, end: datetime, limit: int = 10
) -> list[dict]:
    """Top referral sources by unique visitors."""
    rows = (
        db.query(
            ReferralSources.source,
            func.count(distinct(Events.visitor_id)).label("visitors"),
        )
        .join(Events, Events.referral_id == ReferralSources.id)
        .filter(Events.datetime >= start, Events.datetime <= end)
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
    db: Session, start: datetime, end: datetime, limit: int = 10
) -> list[dict]:
    """Country breakdown as percentages of unique visitors."""
    total_visitors = (
        db.query(func.count(distinct(Events.visitor_id)))
        .filter(Events.datetime >= start, Events.datetime <= end)
        .scalar()
    ) or 1  # avoid division by zero

    rows = (
        db.query(
            Locations.country,
            func.count(distinct(Events.visitor_id)).label("visitors"),
        )
        .join(Events, Events.location_id == Locations.id)
        .filter(Events.datetime >= start, Events.datetime <= end)
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
