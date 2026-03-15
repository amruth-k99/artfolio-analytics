from sqlalchemy.orm import Session

from src.events.schema import EventIngestionPayload
from src.events.model import Events

# Domain services (each owns its own upsert logic)
from src.dates.service import resolve_date
from src.devices.service import resolve_device_type
from src.pages.service import resolve_page
from src.referrals.service import resolve_referral
from src.locations.service import get_location_by_ip
from src.visitors.service import merge_visitor
from src.visitors.schema import MergeVisitorRequest

# Global registry (event type IDs cached in memory)
from src.db.registry import registry


def ingest_event(event: EventIngestionPayload, db: Session) -> Events:
    """
    Ingest a single event: resolve all dimension FKs and create the fact row.

    All dimension upserts use db.flush() (not commit) so they share
    a single transaction. If anything fails, the entire batch is rolled back.
    """

    try:
        # 1. Resolve all dimension FKs (each call is a clean service function)
        date_id = resolve_date(event.timestamp, db)
        device_type_id = resolve_device_type(event.device, db)
        visitor_id = merge_visitor(
            MergeVisitorRequest(
                device_id=event.visitor.device_id,
                user_id=event.visitor.user_id,
                visitor_type=event.visitor.visitor_type
            ),
            db
        ).id
        location_id = get_location_by_ip(event.ip_address, db)
        page_id = resolve_page(event.page, db)
        referral_id = resolve_referral(event.referral, db)
        event_type_id = registry.get_event_type_id(event.event_type.upper())

        # 2. Create the fact row
        new_event = Events(
            date_id=date_id,
            device_type_id=device_type_id,
            visitor_id=visitor_id,
            location_id=location_id,
            page_id=page_id,
            referral_id=referral_id,
            event_type_id=event_type_id,
            datetime=event.timestamp,
            session_id=event.session_id,
            properties=None,
        )

        db.add(new_event)
        db.commit()
        db.refresh(new_event)
        print(f"\n\nIngested event: {new_event.id}\n\n")
        return new_event

    except Exception as e:
        db.rollback()
        print(f"\n\nError ingesting event: {e}\n\n")
        raise e


def automate_event_ingestion(events: list[dict], db: Session) -> dict[str, list]:
    """
    Process a batch of raw event dicts (e.g. from mock_events.json).
    Each dict is validated as EventIngestionPayload, then ingested.

    Future: batch processing, message queue, parallel resolution.
    """

    results = []
    errors = []

    for i, raw_event in enumerate(events):
        try:
            print(f"\nProcessing event {i + 1}/{len(events)}")
            event = EventIngestionPayload(**raw_event)
            result = ingest_event(event, db)
            results.append(result.id)  # or store full result as needed
        except Exception as e:
            print(f"Event {i + 1} failed: {e}")
            # or store error details as needed
            errors.append({"event": raw_event, "err": str(e)})

            continue  # skip failed events, don't break the batch

    print(f"Ingested {len(results)}/{len(events)} events successfully")
    print(f"Failed to ingest {len(errors)} events")
    return {"results": results, "errors": errors}
