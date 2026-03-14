from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.db import get_db
from src.locations.model import LocationModel, Locations
import http.client
import json


router = APIRouter(
    prefix="/v1/locations",
    tags=["Locations"]
)


@router.get("/", description="Get all locations", name="Get Locations")
async def get_locations(db: Session = Depends(get_db)) -> list[LocationModel]:
    try:
        locations = db.query(Locations).all()
        return [LocationModel(**location.__dict__) for location in locations]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", description="Create a new location", name="Create Location")
async def create_location(location: LocationModel, db: Session = Depends(get_db)) -> LocationModel:
    try:
        print(f"Received location: {location}")
        new_location = Locations(**location.dict())
        db.add(new_location)
        db.commit()
        db.refresh(new_location)
        return LocationModel(**new_location.__dict__)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk", description="Create multiple locations in bulk", name="Bulk Create Locations")
async def bulk_create_locations(locations: list[LocationModel], db: Session = Depends(get_db)) -> list[LocationModel]:
    try:
        print(f"Received {len(locations)} locations for bulk creation")
        new_locations = [Locations(**location.dict())
                         for location in locations]
        db.bulk_save_objects(new_locations)
        db.commit()
        return [LocationModel(**location.__dict__) for location in new_locations]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{location_id}", description="Get a location by ID", name="Get Location by ID")
async def get_location_by_id(location_id: int, db: Session = Depends(get_db)) -> LocationModel:
    try:
        location = db.query(Locations).filter(
            Locations.id == location_id).first()
        if location is None:
            raise HTTPException(status_code=404, detail="Location not found")
        return LocationModel(**location.__dict__)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ip/{location_ip}", description="Get a location by IP", name="Get Location by IP")
async def get_location_by_ip(location_ip: str, db: Session = Depends(get_db)) -> dict:
    try:
        # make async http request to make it non-blocking
        conn = http.client.HTTPSConnection("iplocation.com")
        payload = f'ip={location_ip}'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        conn.request("POST", "/", payload, headers)
        res = conn.getresponse()
        data = res.read()
        location_data = json.loads(data.decode("utf-8"))

        if "found" in location_data and not location_data["found"]:
            raise HTTPException(status_code=404, detail="Location not found")

        if location_data is None:
            raise HTTPException(status_code=404, detail="Location not found")

        return location_data
    except Exception as e:
        print(f"Error fetching location data for IP {location_ip}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
