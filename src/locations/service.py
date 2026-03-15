

import httpx
from sqlalchemy.orm import Session
from src.locations.model import Locations
from src.locations.schema import LocationModel, LocationFilterRequest


def get_location_by_ip(location_ip: str, db: Session) -> int:
    try:
        # make async http request to make it non-blocking
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        payload = {
            'ip': location_ip
        }

        response = httpx.post(
            "https://iplocation.com",
            data=payload,
            headers=headers
        )
        data = response.json()

        if "found" in data and not data["found"]:
            print(
                f"Location not found. IP address {location_ip} may be invalid or not in the database.")
            data = {
                "city": "Unknown",
                "region_name": "Unknown",
                "country_name": location_ip
            }

        location = save_location_to_db({
            "city": data.get("city"),
            "state": data.get("region_name"),
            "country": data.get("country_name")
        }, db)

        return location
    except Exception as e:
        raise Exception(f"Error fetching location data: {str(e)}")


def save_location_to_db(location_data: dict, db: Session) -> int:
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
            return existing_location.id
        else:
            db.add(new_location)
            db.commit()
            db.refresh(new_location)

        return new_location.id

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


async def resolve_location(ip_address: str, db: Session) -> int:
    """
    Resolve location from IP address and return the location_id.

    Calls external IP geolocation API (sync), then upserts into d_locations.
    Falls back to "Unknown" if the API fails, so ingestion never breaks.
    """

    try:
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        payload = {'ip': ip_address}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://iplocation.com",
                data=payload,
                headers=headers
            )
            data = response.json()

            if "found" in data and not data["found"]:
                location_data = {
                    "city": "Unknown",
                    "state": "Unknown",
                    "country": ip_address
                }
            else:
                location_data = {
                    "city": data.get("city", "Unknown"),
                    "state": data.get("region_name", "Unknown"),
                    "country": data.get("country_name", ip_address)
                }
    except Exception:
        # External API failed — use placeholder so ingestion doesn't break
        location_data = {
            "city": "Unknown",
            "state": "Unknown",
            "country": ip_address
        }

    result = save_location_to_db(location_data, db)
    return result
