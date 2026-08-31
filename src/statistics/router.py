from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from src.db import get_db
from src.statistics.service import (
    get_dashboard_statistics,
    get_live_events,
    get_portfolio_statistics,
)


router = APIRouter(
    prefix="/v1/statistics",
    tags=["Statistics"],
)


@router.get(
    "/dashboard",
    description="Get aggregated dashboard statistics for the analytics overview",
    name="Dashboard Statistics",
)
async def dashboard_statistics(
    request: Request,
    db: Session = Depends(get_db),
) -> dict:
    try:
        days = int(request.query_params.get("days", 7))
        if days not in (7, 30, 90):
            days = 7
        data = get_dashboard_statistics(db, days=days)
        return {"data": data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/live-events",
    description="Get recent events with full dimension data for the live events view",
    name="Live Events",
)
async def live_events(
    request: Request,
    db: Session = Depends(get_db),
) -> dict:
    try:
        time_range = request.query_params.get("time_range", "today")
        search = request.query_params.get("search", "")
        limit = int(request.query_params.get("limit", 100))
        if limit > 500:
            limit = 500
        data = get_live_events(db, time_range=time_range, search=search, limit=limit)
        return {"data": data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/portfolio",
    description="Get statistics for a single portfolio, identified by its page name (username)",
    name="Portfolio Statistics",
)
async def portfolio_statistics(
    request: Request,
    db: Session = Depends(get_db),
) -> dict:
    try:
        page_name = (request.query_params.get("page_name") or "").strip()
        if not page_name:
            raise HTTPException(
                status_code=422, detail="page_name is required")

        days = int(request.query_params.get("days", 7))
        if days not in (1, 7, 14, 30, 90):
            days = 7

        data = get_portfolio_statistics(db, page_name=page_name, days=days)
        return {"data": data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
