"""
Page dimension service — resolves page info into d_pages rows.
"""

from urllib.parse import urlparse
from sqlalchemy.orm import Session
from src.pages.model import Page
from src.events.schema import PagePayload
from src.cache import cache_manager


def resolve_page(page: PagePayload, db: Session) -> int:
    """
    Upsert page by URL. Extracts host from the full URL.

    Cache layer: URL → page_id.
    Returns the page_id.
    """
    page_cache = cache_manager.get_cache("pages")

    # Cache hit — skip DB query
    cached = page_cache.get(page.url)
    if cached is not None:
        return cached

    parsed_url = urlparse(page.url)
    host = parsed_url.netloc or "unknown"

    existing = db.query(Page).filter_by(url=page.url).first()

    if existing:
        page_cache.put(page.url, existing.id)
        return existing.id

    new_page = Page(
        page_name=page.page_name,
        url=page.url,
        full_path=page.full_path,
        host=host
    )

    db.add(new_page)
    db.flush()

    page_cache.put(page.url, new_page.id)
    return new_page.id
