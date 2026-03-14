from src.events.schema import EventIngestionPayload
from src.events.model import Events
from sqlalchemy.orm import Session


def ingest_event(event: EventIngestionPayload, db: Session) -> EventIngestionPayload:
    try:
        # dissect the event and create all the necessary foreign keys
        print(
            f"Processing event: {event.event_type} for user: {event.ip_address}", event.model_dump_json(indent=2))

        # all of these should be done in a transaction, if any of them fail, the entire transaction should be rolled back
        # they should be done in parallel to speed up the ingestion process, as we want to be able to ingest a large number of events in a short amount of time
        # implement a local caching layer to cache the results of the foreign key lookups, so that we don't have to hit the database for every event
        # moreover, we can use a message queue to process the events asynchronously, so that we can handle spikes in traffic without overwhelming the database
        # we can also use a batch processing approach, where we collect a batch of events and then process them together, which can help reduce the number of database transactions and improve performance
        # we can also use a combination of these approaches, for example, we can use a message queue to process the events asynchronously and then use a batch processing approach to process the events in batches, 
        # which can help improve performance and reduce the load on the database
        # each of the below operation's code should be in their separate functions in their folder structure, which can be called in parallel using asyncio.gather or similar approach

        # find the location of the event based on the IP address and create a new Location object if it doesn't exist
        # find the visitor based on the user_id, device_id and create a new Visitor object if it doesn't exist
        # find the the page based on the url and create a new Page object if it doesn't exist
        # find device type based on os, browser, device type and create a new Device object if it doesn't exist
        # find the referrer based on the referrer url and create a new Referrer object if it doesn't exist
        # find event type based on the event_type and create a new EventType object if it doesn't exist

        # after getting all foreign keys, create the event
        return event
    except Exception as e:
        db.rollback()
        raise e

def automate_event_ingestion(events: list[EventIngestionPayload], db: Session) -> list[EventIngestionPayload]:
    try:
        print(f"Received {len(events)} events for bulk creation")
        return []
    except Exception as e:
        db.rollback()
        raise e


def save_events_to_db(events: list[EventIngestionPayload], db: Session) -> list[EventIngestionPayload]:
    try:
        new_events = [Events(**event.dict()) for event in events]
        db.bulk_save_objects(new_events)
        db.commit()
        return [EventIngestionPayload(**event.__dict__) for event in new_events]
    except Exception as e:
        db.rollback()
        raise e
