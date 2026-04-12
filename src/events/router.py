import json
from src.db import get_db
from sqlalchemy.orm import Session, joinedload
from src.events.model import Events
from src.events.schema import EventModel, EventIngestionPayload, BatchIngestionPayload
from fastapi import APIRouter, Depends, HTTPException, Request
from src.events.service import ingest_event, automate_event_ingestion


router = APIRouter(
    prefix="/v1/events",
    tags=["Events"]
)


@router.get("/", description="Get all events", name="Get Events")
async def get_events(request: Request, db: Session = Depends(get_db)) -> dict:
    try:
        # pagination
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        events = (
            db.query(Events)
            .options(
                joinedload(Events.device_type),
                joinedload(Events.visitor),
                joinedload(Events.location),
                joinedload(Events.page),
                joinedload(Events.referral),
                joinedload(Events.event_type),
            )
            .order_by(Events.datetime.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return {
            "data": {
                "events": [EventModel.model_validate(event) for event in events],
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": db.query(Events).count()
                }
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", description="Create a new event", name="Create Event")
async def create_event(request: Request, event: EventIngestionPayload, db: Session = Depends(get_db)) -> EventModel:
    try:
        # Extract client IP from request headers (the frontend does not send it)
        client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "0.0.0.0")
        if "," in client_ip:
            client_ip = client_ip.split(",")[0].strip()

        # Inject the server-resolved IP into the event payload
        event_dict = event.model_dump()
        event_dict["ip_address"] = client_ip
        
        new_event = ingest_event(event_dict, db)
        return EventModel(**new_event.__dict__)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/automate", description="Pull events from the queue and save them to the database", name="Automate Events")
def automate_events(_: Request, db: Session = Depends(get_db)) -> dict[str, list]:
    try:
        with open("scripts/mock_events.json", "r") as f:
            events = json.load(f)
            results = automate_event_ingestion(events, db)
        return results
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch", description="Ingest a batch of events from the frontend analytics pipeline", name="Batch Ingest Events")
async def batch_ingest_events(request: Request, payload: BatchIngestionPayload, db: Session = Depends(get_db)) -> dict:
    try:
        # Extract client IP from request headers (the frontend does not send it)
        client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "0.0.0.0")
        if "," in client_ip:
            client_ip = client_ip.split(",")[0].strip()

        # Inject the server-resolved IP into each event payload
        events_with_ip = []
        for event in payload.events:
            event_dict = event.model_dump()
            event_dict["ip_address"] = client_ip
            events_with_ip.append(event_dict)

        results = automate_event_ingestion(events_with_ip, db)
        return results
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
