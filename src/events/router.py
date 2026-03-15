import json
from src.db import get_db
from sqlalchemy.orm import Session
from src.events.model import Events
from src.events.schema import EventModel
from src.events.schema import EventIngestionPayload
from fastapi import APIRouter, Depends, HTTPException
from src.events.service import ingest_event, automate_event_ingestion


router = APIRouter(
    prefix="/v1/events",
    tags=["Events"]
)


@router.get("/", description="Get all events", name="Get Events")
async def get_events(db: Session = Depends(get_db)) -> list[EventModel]:
    try:
        events = db.query(Events).all()
        return [EventModel(**event.__dict__) for event in events]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", description="Create a new event", name="Create Event")
async def create_event(event: EventIngestionPayload, db: Session = Depends(get_db)) -> EventModel:
    try:
        new_event = ingest_event(event, db)
        return EventModel(**new_event.__dict__)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/automate", description="Pull events from the queue and save them to the database", name="Automate Events")
def automate_events(db: Session = Depends(get_db)) -> list[EventModel]:
    try:
        with open("scripts/mock_events.json", "r") as f:
            events = json.load(f)
            results = automate_event_ingestion(events, db)
        return [EventModel(**event.__dict__) for event in results]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
