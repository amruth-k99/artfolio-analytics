from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.db import get_db
from src.events.model import EventModel, Events


router = APIRouter(
    prefix="/v1/events",
    tags=["Events"]
)


@router.get("/", description="Get all events", name="Get Events")
async def get_events(db: Session = Depends(get_db)) -> list[EventModel]:
    try:
        events = db.query(Events).all()
        return [EventModel(**event.__dict__) for event in events]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", description="Create a new event", name="Create Event")
async def create_event(event: EventModel, db: Session = Depends(get_db)) -> EventModel:
    try:
        print(f"Received event: {event}")
        new_event = Events(**event.model_dump_json())
        db.add(new_event)
        db.commit()
        db.refresh(new_event)
        return EventModel(**new_event.__dict__)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk", description="Create multiple events in bulk", name="Bulk Create Events")
async def bulk_create_events(events: list[EventModel], db: Session = Depends(get_db)) -> list[EventModel]:
    try:
        print(f"Received {len(events)} events for bulk creation")
        new_events = [Events(**event.model_dump_json()) for event in events]
        db.bulk_save_objects(new_events)
        db.commit()
        return [EventModel(**event.__dict__) for event in new_events]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
