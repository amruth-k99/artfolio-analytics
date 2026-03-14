

from sqlalchemy.orm import Session
from src.visitors.model import Visitors
from src.visitors.schema import VisitorModel, MergeVisitorRequest


def save_visitor_to_db(visitor_data: dict, db: Session) -> VisitorModel:
    try:
        new_visitor = Visitors(**visitor_data)
        db.add(new_visitor)
        db.commit()
        db.refresh(new_visitor)
        return VisitorModel(**new_visitor.__dict__)
    except Exception as e:
        db.rollback()
        raise e


async def get_visitor_by_user_id(user_id: str, db: Session) -> VisitorModel:
    try:
        visitor = db.query(Visitors).filter_by(user_id=user_id).first()
        if not visitor:
            raise Exception("Visitor not found")
        return VisitorModel(**visitor.__dict__)
    except Exception as e:
        raise e

async def create_visitor(visitor_data: dict, db: Session) -> VisitorModel:
    try:
        new_visitor = Visitors(**visitor_data)
        db.add(new_visitor)
        db.commit()
        db.refresh(new_visitor)
        return VisitorModel(**new_visitor.__dict__)
    except Exception as e:
        db.rollback()
        raise e

def merge_visitor(visitor_data: MergeVisitorRequest, db: Session) -> VisitorModel:
    """
    Upsert a visitor based on (device_id, user_id) unique constraint.

    Cases:
    1. Guest visit: device_id provided, user_id is None
       → Find by (device_id, user_id=None) or create
    2. Logged-in visit: both device_id and user_id provided
       → Find by (device_id, user_id) or create a new association
    3. Returning visit: existing (device_id, user_id) combo found
       → Update visitor_type to "returning" and return
    """
    try:
        # Look for existing visitor with this exact (device_id, user_id) combo
        existing = db.query(Visitors).filter_by(
            device_id=visitor_data.device_id,
            user_id=visitor_data.user_id
        ).first()

        if existing:
            # Returning visitor — same device, same user (or same device, still guest)
            if existing.visitor_type != "returning":
                existing.visitor_type = "returning"
                db.commit()
                db.refresh(existing)
            return VisitorModel(**existing.__dict__)

        # New combination — create a new visitor row
        new_visitor = Visitors(
            device_id=visitor_data.device_id,
            user_id=visitor_data.user_id,
            visitor_type=visitor_data.visitor_type,
            account_status="active",
            user_type="user" if visitor_data.user_id else "guest",
        )
        db.add(new_visitor)
        db.commit()
        db.refresh(new_visitor)
        return VisitorModel(**new_visitor.__dict__)

    except Exception as e:
        db.rollback()
        raise e