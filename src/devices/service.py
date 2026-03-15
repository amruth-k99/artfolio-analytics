"""
Device type dimension service — resolves device info into d_device_types rows.
"""

from sqlalchemy.orm import Session
from src.devices.model import DeviceTypes
from src.events.schema import DevicePayload


def resolve_device_type(device: DevicePayload, db: Session) -> int:
    """
    Upsert device type by (os, browser, device_type) unique constraint.
    Returns the device_type_id.
    """

    existing = db.query(DeviceTypes).filter_by(
        os=device.os,
        browser=device.browser,
        device_type=device.device_type
    ).first()

    if existing:
        return existing.id

    new_device = DeviceTypes(
        os=device.os,
        browser=device.browser,
        device_type=device.device_type
    )

    db.add(new_device)
    db.flush()
    return new_device.id
