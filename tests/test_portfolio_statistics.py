"""
Tests for the per-portfolio statistics endpoint.

The portfolio owner's analytics page previously had no measured source for
"unique visitors" - a different service sent `visits * 0.6` under that label.
These tests pin the behaviour that replaced it: every number is scoped to one
portfolio and derived from real events.
"""

from datetime import datetime, timedelta

import pytest

from src.dates.model import Dates
from src.devices.model import DeviceTypes
from src.events.model import Events, EventTypes
from src.locations.model import Locations
from src.pages.model import Page
from src.referrals.model import ReferralSources
from src.statistics.service import get_portfolio_statistics
from src.visitors.model import Visitors


# ── Fixture builders ───────────────────────────────────────────────────

def _seed_dimensions(db):
    """Create the shared dimension rows every event needs."""
    page_view = EventTypes(name="PAGE_VIEW")
    click = EventTypes(name="CLICK")
    device = DeviceTypes(os="macOS", device_type="desktop", browser="Chrome")
    referral = ReferralSources(
        source="google", referrer_url="https://google.com", category="search"
    )
    direct = ReferralSources(
        source="direct", referrer_url=None, category="direct"
    )
    india = Locations(city="Bengaluru", state="Karnataka", country="India")
    usa = Locations(
        city="Ashburn", state="Virginia", country="United States of America"
    )
    date_row = Dates(
        date=datetime.utcnow(), minute=0, hour=0, day=1,
        day_of_week=1, month=1, quarter=1, year=2026,
    )
    db.add_all(
        [page_view, click, device, referral, direct, india, usa, date_row]
    )
    db.commit()

    return {
        "page_view": page_view,
        "click": click,
        "device": device,
        "google": referral,
        "direct": direct,
        "india": india,
        "usa": usa,
        "date": date_row,
    }


def _make_page(db, page_name: str) -> Page:
    page = Page(
        page_name=page_name,
        url=f"https://artfolio.tech/{page_name}",
        full_path=f"/{page_name}",
        host="artfolio.tech",
    )
    db.add(page)
    db.commit()
    return page


def _make_visitor(db, device_id: str) -> Visitors:
    visitor = Visitors(
        visitor_type="new",
        user_id=None,
        device_id=device_id,
        account_status="active",
        user_type="guest",
    )
    db.add(visitor)
    db.commit()
    return visitor


def _make_event(db, dims, page, visitor, *, when=None, event_type=None,
                location=None, referral=None, session_id="s1"):
    event = Events(
        date_id=dims["date"].id,
        device_type_id=dims["device"].id,
        visitor_id=visitor.id,
        location_id=(location or dims["india"]).id,
        page_id=page.id,
        referral_id=(referral or dims["direct"]).id,
        event_type_id=(event_type or dims["page_view"]).id,
        datetime=when or datetime.utcnow(),
        session_id=session_id,
        properties=None,
    )
    db.add(event)
    db.commit()
    return event


# ── Tests ──────────────────────────────────────────────────────────────

def test_counts_distinct_visitors_not_events(test_db):
    """Three page views from one visitor is one unique visitor."""
    dims = _seed_dimensions(test_db)
    page = _make_page(test_db, "amruth")
    visitor = _make_visitor(test_db, "device-a")

    for _ in range(3):
        _make_event(test_db, dims, page, visitor)

    result = get_portfolio_statistics(test_db, page_name="amruth", days=7)

    assert result["unique_visitors"] == 1
    assert result["page_views"] == 3


def test_separate_visitors_are_counted_separately(test_db):
    dims = _seed_dimensions(test_db)
    page = _make_page(test_db, "amruth")

    for device_id in ("device-a", "device-b", "device-c"):
        _make_event(test_db, dims, page, _make_visitor(test_db, device_id))

    result = get_portfolio_statistics(test_db, page_name="amruth", days=7)

    assert result["unique_visitors"] == 3


def test_another_portfolios_traffic_is_excluded(test_db):
    """The whole point of the endpoint: one owner never sees another's numbers."""
    dims = _seed_dimensions(test_db)
    mine = _make_page(test_db, "amruth")
    theirs = _make_page(test_db, "someone-else")

    _make_event(test_db, dims, mine, _make_visitor(test_db, "device-a"))
    for device_id in ("device-b", "device-c", "device-d"):
        _make_event(test_db, dims, theirs, _make_visitor(test_db, device_id))

    result = get_portfolio_statistics(test_db, page_name="amruth", days=7)

    assert result["unique_visitors"] == 1
    assert result["page_views"] == 1


def test_page_views_exclude_non_pageview_events(test_db):
    dims = _seed_dimensions(test_db)
    page = _make_page(test_db, "amruth")
    visitor = _make_visitor(test_db, "device-a")

    _make_event(test_db, dims, page, visitor)
    _make_event(test_db, dims, page, visitor, event_type=dims["click"])
    _make_event(test_db, dims, page, visitor, event_type=dims["click"])

    result = get_portfolio_statistics(test_db, page_name="amruth", days=7)

    assert result["page_views"] == 1
    assert result["unique_visitors"] == 1


def test_events_outside_the_window_are_excluded(test_db):
    dims = _seed_dimensions(test_db)
    page = _make_page(test_db, "amruth")

    _make_event(test_db, dims, page, _make_visitor(test_db, "recent"))
    _make_event(
        test_db, dims, page, _make_visitor(test_db, "old"),
        when=datetime.utcnow() - timedelta(days=40),
    )

    week = get_portfolio_statistics(test_db, page_name="amruth", days=7)
    quarter = get_portfolio_statistics(test_db, page_name="amruth", days=90)

    assert week["unique_visitors"] == 1
    assert quarter["unique_visitors"] == 2


def test_countries_come_from_resolved_locations(test_db):
    dims = _seed_dimensions(test_db)
    page = _make_page(test_db, "amruth")

    _make_event(
        test_db, dims, page, _make_visitor(test_db, "in-1"),
        location=dims["india"],
    )
    _make_event(
        test_db, dims, page, _make_visitor(test_db, "in-2"),
        location=dims["india"],
    )
    _make_event(
        test_db, dims, page, _make_visitor(test_db, "us-1"),
        location=dims["usa"],
    )

    result = get_portfolio_statistics(test_db, page_name="amruth", days=7)
    by_country = {row["country"]: row for row in result["countries"]}

    assert by_country["India"]["percentage"] == "67%"
    assert by_country["United States of America"]["percentage"] == "33%"
    assert by_country["India"]["flag"] == "🇮🇳"


def test_countries_are_scoped_to_the_portfolio(test_db):
    dims = _seed_dimensions(test_db)
    mine = _make_page(test_db, "amruth")
    theirs = _make_page(test_db, "someone-else")

    _make_event(
        test_db, dims, mine, _make_visitor(test_db, "in-1"),
        location=dims["india"],
    )
    _make_event(
        test_db, dims, theirs, _make_visitor(test_db, "us-1"),
        location=dims["usa"],
    )

    result = get_portfolio_statistics(test_db, page_name="amruth", days=7)
    countries = [row["country"] for row in result["countries"]]

    assert countries == ["India"]


def test_referrers_are_scoped_to_the_portfolio(test_db):
    dims = _seed_dimensions(test_db)
    mine = _make_page(test_db, "amruth")
    theirs = _make_page(test_db, "someone-else")

    _make_event(
        test_db, dims, mine, _make_visitor(test_db, "a"),
        referral=dims["google"],
    )
    _make_event(
        test_db, dims, theirs, _make_visitor(test_db, "b"),
        referral=dims["direct"],
    )

    result = get_portfolio_statistics(test_db, page_name="amruth", days=7)

    assert [row["domain"] for row in result["referrers"]] == ["google"]
    assert result["referrers"][0]["visitors"] == 1


def test_chart_data_covers_every_day_in_the_window(test_db):
    _seed_dimensions(test_db)
    _make_page(test_db, "amruth")

    result = get_portfolio_statistics(test_db, page_name="amruth", days=7)

    # Inclusive of both endpoints, so a 7-day lookback spans 8 calendar days.
    assert len(result["chart_data"]) == 8
    assert all(point["visitors"] == 0 for point in result["chart_data"])


def test_unknown_portfolio_reports_zero_rather_than_site_totals(test_db):
    dims = _seed_dimensions(test_db)
    page = _make_page(test_db, "somebody")
    _make_event(test_db, dims, page, _make_visitor(test_db, "device-a"))

    result = get_portfolio_statistics(test_db, page_name="nobody", days=7)

    assert result["unique_visitors"] == 0
    assert result["page_views"] == 0
    assert result["countries"] == []
    assert result["referrers"] == []


def test_site_wide_dashboard_is_unaffected_by_the_page_filter(test_db):
    """Regression: the admin dashboard must still see every portfolio."""
    from src.statistics.service import get_dashboard_statistics

    dims = _seed_dimensions(test_db)
    mine = _make_page(test_db, "amruth")
    theirs = _make_page(test_db, "someone-else")

    _make_event(test_db, dims, mine, _make_visitor(test_db, "a"))
    _make_event(test_db, dims, theirs, _make_visitor(test_db, "b"))

    result = get_dashboard_statistics(test_db, days=7)
    visitors = next(s for s in result["stats"] if s["label"] == "Visitors")

    assert visitors["value"] == "2"


# ── HTTP surface ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_endpoint_returns_scoped_stats(async_client, test_db):
    dims = _seed_dimensions(test_db)
    page = _make_page(test_db, "amruth")
    _make_event(test_db, dims, page, _make_visitor(test_db, "device-a"))

    res = await async_client.get(
        "/analytics/v1/statistics/portfolio?page_name=amruth&days=7"
    )

    assert res.status_code == 200
    data = res.json()["data"]
    assert data["page_name"] == "amruth"
    assert data["unique_visitors"] == 1


@pytest.mark.asyncio
async def test_endpoint_rejects_a_missing_page_name(async_client, test_db):
    _seed_dimensions(test_db)

    res = await async_client.get("/analytics/v1/statistics/portfolio")

    assert res.status_code == 422


@pytest.mark.asyncio
async def test_endpoint_falls_back_to_seven_days_for_an_odd_range(
    async_client, test_db
):
    _seed_dimensions(test_db)
    _make_page(test_db, "amruth")

    res = await async_client.get(
        "/analytics/v1/statistics/portfolio?page_name=amruth&days=999"
    )

    assert res.status_code == 200
    assert res.json()["data"]["days"] == 7
