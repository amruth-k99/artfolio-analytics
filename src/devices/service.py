"""
Device type dimension service — resolves device info into d_device_types rows.
"""

from sqlalchemy.orm import Session
from src.devices.model import DeviceTypes
from src.events.schema import DevicePayload
from src.cache import cache_manager


def resolve_device_type(device: DevicePayload, db: Session) -> int:
    """
    Upsert device type by (os, browser, device_type) unique constraint.

    Cache layer: (os, browser, device_type) tuple → device_type_id.
    Returns the device_type_id.
    """
    device_cache = cache_manager.get_cache("device_types")
    cache_key = f"{device.os}|{device.browser}|{device.device_type}"

    # Cache hit — skip DB query
    cached = device_cache.get(cache_key)
    if cached is not None:
        return cached

    existing = db.query(DeviceTypes).filter_by(
        os=device.os,
        browser=device.browser,
        device_type=device.device_type
    ).first()

    if existing:
        device_cache.put(cache_key, existing.id)
        return existing.id

    new_device = DeviceTypes(
        os=device.os,
        browser=device.browser,
        device_type=device.device_type
    )

    db.add(new_device)
    db.flush()

    device_cache.put(cache_key, new_device.id)
    return new_device.id
