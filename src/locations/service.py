

import httpx
from sqlalchemy.orm import Session
from src.locations.model import Locations
from src.locations.schema import LocationModel, LocationFilterRequest


async def get_location_by_ip(location_ip: str, db: Session) -> dict:
    try:
        # make async http request to make it non-blocking
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        payload = {
            'ip': location_ip
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://iplocation.com",
                data=payload,
                headers=headers
            )
            data = response.json()

            if "found" in data and not data["found"]:
                raise Exception(
                    "Location not found. IP address may be invalid or not in the database.")

            save_location_to_db({
                "city": data.get("city"),
                "state": data.get("region_name"),
                "country": data.get("country_name")
            }, db)

            return data
    except Exception as e:
        raise Exception(f"Error fetching location data: {str(e)}")


def save_location_to_db(location_data: dict, db: Session) -> LocationModel:
    try:

        new_location = Locations(
            city=location_data.get("city"),
            state=location_data.get("state"),
            country=location_data.get("country")
        )

        existing_location = db.query(Locations).filter_by(
            city=new_location.city,
            state=new_location.state,
            country=new_location.country
        ).first()

        if existing_location:
            print("Location already exists in the database. Skipping save.")
            return LocationModel(**existing_location.__dict__)
        else:
            db.add(new_location)
            db.commit()
            db.refresh(new_location)

        return LocationModel(**new_location.__dict__)

    except Exception as e:
        db.rollback()
        raise e


async def search_locations(filters: LocationFilterRequest, db: Session) -> list[LocationModel]:
    try:
        page = filters.page or 1
        page_size = filters.page_size or 10
        search_text = filters.search_text or ""

        locations = db.query(Locations).where(
            (Locations.city.ilike(f"%{search_text}%")) |
            (Locations.state.ilike(f"%{search_text}%")) |
            (Locations.country.ilike(f"%{search_text}%"))
        ).offset((page - 1) * page_size).limit(page_size).all()

        return [LocationModel(**location.__dict__) for location in locations]
    except Exception as e:
        raise Exception(f"Error fetching locations: {str(e)}")
