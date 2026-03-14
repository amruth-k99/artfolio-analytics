from src.locations.schema import LocationModel, LocationFilterRequest
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.db import get_db
from src.locations.service import get_location_by_ip, search_locations, save_location_to_db


router = APIRouter(
    prefix="/v1/locations",
    tags=["Locations"]
)


@router.post("/search", description="Search for locations", name="Filter Locations")
async def search_locations_api(filters: LocationFilterRequest, db: Session = Depends(get_db)) -> list[LocationModel]:
    try:
        locations = await search_locations(filters, db)
        return locations
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", description="Create a new location", name="Create Location")
async def create_location_api(location: LocationModel, db: Session = Depends(get_db)) -> LocationModel:
    try:
        new_location = save_location_to_db(location.model_dump(), db)

        return new_location
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ip/{location_ip}", description="Get a location by IP", name="Get Location by IP")
async def get_location_by_ip_api(location_ip: str, db: Session = Depends(get_db)) -> dict:
    try:
        # make async http request to make it non-blocking
        # validate IP address format before making the request
        location_ip = location_ip.strip()

        if not location_ip:
            raise HTTPException(
                status_code=400, detail="Invalid IP address format")

        response = await get_location_by_ip(location_ip, db)

        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
