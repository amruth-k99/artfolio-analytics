from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from src.db import get_db
from src.statistics.service import get_dashboard_statistics


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
